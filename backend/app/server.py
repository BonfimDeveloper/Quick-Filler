import os
import socket

import uvicorn


def create_dual_stack_socket() -> socket.socket:
    port = int(os.getenv("PORT", "8000"))
    server_socket = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_V6ONLY, 0)
    server_socket.bind(("::", port))
    server_socket.listen(2048)
    return server_socket


if __name__ == "__main__":
    config = uvicorn.Config("app.main:app")
    uvicorn.Server(config).run(sockets=[create_dual_stack_socket()])
