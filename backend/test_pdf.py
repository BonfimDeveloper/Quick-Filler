from pathlib import Path

from app.services.pdf import extrair_texto


caminho = Path("uploads/f6edba40-89bf-47c4-96ff-e2808b80665b.pdf")

texto = extrair_texto(caminho)

print("Quantidade de caracteres:", len(texto))
print()
print("========== TEXTO EXTRAÍDO ==========")
print(texto[:5000])
print("========== FIM ==========")