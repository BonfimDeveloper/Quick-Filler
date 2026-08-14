import { HttpClient } from '@angular/common/http';
import { Component, OnDestroy, computed, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { DomSanitizer, SafeResourceUrl } from '@angular/platform-browser';

type DocumentType = 'cartao-ponto' | 'holerite';
type Status = 'processando' | 'concluido' | 'erro';

interface Punch {
  kind: 'IN' | 'OUT';
  time_raw: string;
  time_hhmm: string;
}

interface Day {
  date_raw: string;
  punches: Punch[];
}

interface TimeCardPage {
  page: number;
  days: Day[];
}

interface PayrollField {
  code: string;
  label: string;
  reference: string;
  value: string;
}

interface PayrollBase {
  label: string;
  value: string;
}

interface PayrollPage {
  page: number;
  month: string;
  year: string;
  fields: PayrollField[];
  bases: PayrollBase[];
}

interface Transcription {
  id: string;
  tipo: DocumentType;
  status: Status;
  erro: string | null;
  value: { pages: Array<TimeCardPage | PayrollPage> } | null;
}

@Component({
  selector: 'app-root',
  imports: [FormsModule],
  templateUrl: './app.html',
  styleUrl: './app.css',
})
export class App implements OnDestroy {
  private readonly http = inject(HttpClient);
  private readonly sanitizer = inject(DomSanitizer);
  private pollTimer?: ReturnType<typeof setTimeout>;

  protected readonly tipo = signal<DocumentType>('cartao-ponto');
  protected readonly arquivo = signal<File | null>(null);
  protected readonly pdfUrl = signal<string | null>(null);
  protected readonly pdfSeguro = signal<SafeResourceUrl | null>(null);
  protected readonly transcricao = signal<Transcription | null>(null);
  protected readonly enviando = signal(false);
  protected readonly salvando = signal(false);
  protected readonly mensagem = signal('');

  protected readonly paginasCartao = computed(() => {
    if (this.transcricao()?.tipo !== 'cartao-ponto') return [];
    return (this.transcricao()?.value?.pages ?? []) as TimeCardPage[];
  });

  protected readonly paginasHolerite = computed(() => {
    if (this.transcricao()?.tipo !== 'holerite') return [];
    return (this.transcricao()?.value?.pages ?? []) as PayrollPage[];
  });

  protected selecionarTipo(tipo: DocumentType): void {
    this.tipo.set(tipo);
  }

  protected selecionarArquivo(event: Event): void {
    const input = event.target as HTMLInputElement;
    const file = input.files?.[0] ?? null;
    this.arquivo.set(file);
    this.transcricao.set(null);
    this.mensagem.set('');

    const antiga = this.pdfUrl();
    if (antiga) URL.revokeObjectURL(antiga);
    const url = file ? URL.createObjectURL(file) : null;
    this.pdfUrl.set(url);
    this.pdfSeguro.set(
      url
        ? this.sanitizer.bypassSecurityTrustResourceUrl(url)
        : null,
    );
  }

  protected enviar(): void {
    const file = this.arquivo();
    if (!file || this.enviando()) return;

    const data = new FormData();
    data.append('arquivo', file);
    data.append('tipo', this.tipo());
    this.enviando.set(true);
    this.mensagem.set('Enviando documento…');

    this.http.post<{ id: string }>('/api/transcricoes', data).subscribe({
      next: ({ id }) => {
        this.enviando.set(false);
        this.mensagem.set('Documento recebido. Processando…');
        this.consultar(id);
      },
      error: (error) => this.falhar(error),
    });
  }

  private consultar(id: string): void {
    this.http.get<Transcription>(`/api/transcricoes/${id}`).subscribe({
      next: (transcription) => {
        this.transcricao.set(transcription);

        if (transcription.status === 'processando') {
          this.mensagem.set('Lendo e estruturando o documento…');
          this.pollTimer = setTimeout(() => this.consultar(id), 1200);
          return;
        }

        this.mensagem.set(
          transcription.status === 'concluido'
            ? 'Transcrição pronta para revisão.'
            : transcription.erro ?? 'Não foi possível processar o documento.',
        );
      },
      error: (error) => this.falhar(error),
    });
  }

  protected salvar(): void {
    const transcription = this.transcricao();
    if (!transcription?.value || this.salvando()) return;

    this.salvando.set(true);
    this.http
      .put<Transcription>(`/api/transcricoes/${transcription.id}`, {
        value: transcription.value,
      })
      .subscribe({
        next: (updated) => {
          this.transcricao.set(updated);
          this.salvando.set(false);
          this.mensagem.set('Correções salvas. O download já está atualizado.');
        },
        error: (error) => this.falhar(error),
      });
  }

  protected baixar(formato: 'xlsx' | 'csv' | 'json'): void {
    const id = this.transcricao()?.id;
    if (!id) return;
    window.location.href = `/api/transcricoes/${id}/planilha?formato=${formato}`;
  }

  protected avisoCartao(page: TimeCardPage, indice: number): { tipo: 'warning' | 'sequence'; motivo: string } | null {
    const day = page.days[indice];
    const atual = this.valorData(day.date_raw);
    let anterior: number | null = null;

    for (let i = indice - 1; i >= 0; i--) {
      anterior = this.valorData(page.days[i].date_raw);
      if (anterior !== null) break;
    }

    if (atual !== null && anterior !== null && atual !== anterior + 1) {
      return { tipo: 'sequence', motivo: 'Data não sequencial' };
    }

    if (day.punches.length % 2 !== 0) {
      return { tipo: 'warning', motivo: 'Número ímpar de batidas' };
    }

    if (day.date_raw.includes('?') || day.punches.some((p) => p.time_raw.includes('?') || p.time_hhmm.includes('?'))) {
      return { tipo: 'warning', motivo: 'Há caracteres que precisam de revisão' };
    }

    return null;
  }

  protected avisoHolerite(indice: number): { tipo: 'warning' | 'sequence'; motivo: string } | null {
    const pages = this.paginasHolerite();
    const page = pages[indice];
    const atual = this.valorCompetencia(page);
    let anterior: number | null = null;

    for (let i = indice - 1; i >= 0; i--) {
      anterior = this.valorCompetencia(pages[i]);
      if (anterior !== null) break;
    }

    if (atual !== null && anterior !== null && atual !== anterior + 1) {
      return { tipo: 'sequence', motivo: 'Mês não sequencial' };
    }

    if (page.fields.length === 0 && page.bases.length === 0) {
      return { tipo: 'warning', motivo: 'Página sem dados extraídos' };
    }

    if ([...page.fields, ...page.bases].some((item) =>
      Object.values(item).some((value) => String(value).includes('?')),
    )) {
      return { tipo: 'warning', motivo: 'Há caracteres que precisam de revisão' };
    }

    return null;
  }

  private valorData(value: string): number | null {
    if (value.includes('?')) return null;
    if (/^\d+$/.test(value)) return Number(value);
    const match = value.match(/^(\d{1,2})[/-](\d{1,2})[/-](\d{4})$/);
    if (!match) return null;
    const [, day, month, year] = match.map(Number);
    const parsed = new Date(Date.UTC(year, month - 1, day));
    if (parsed.getUTCFullYear() !== year || parsed.getUTCMonth() !== month - 1 || parsed.getUTCDate() !== day) return null;
    return Math.floor(parsed.getTime() / 86_400_000);
  }

  private valorCompetencia(page: PayrollPage): number | null {
    const month = Number(page.month);
    const year = Number(page.year);
    return Number.isInteger(month) && month >= 1 && month <= 12 && Number.isInteger(year)
      ? year * 12 + month - 1
      : null;
  }

  private falhar(error: any): void {
    this.enviando.set(false);
    this.salvando.set(false);
    this.mensagem.set(error?.error?.detail ?? 'Não foi possível concluir a operação.');
  }

  ngOnDestroy(): void {
    if (this.pollTimer) clearTimeout(this.pollTimer);
    const url = this.pdfUrl();
    if (url) URL.revokeObjectURL(url);
  }
}
