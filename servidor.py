import socket
import threading
import os

HOST = 'localhost'
PORT = 5000
PASTA_ARQUIVOS = 'arquivos'

if not os.path.exists(PASTA_ARQUIVOS):
    os.makedirs(PASTA_ARQUIVOS)

clientes = []

def tratar_cliente(conn, addr):
    print(f'[+] Cliente conectado: {addr}')
    while True:
        try:
            dados = conn.recv(1024).decode()
            if not dados:
                break

            print(f"[DEBUG] Recebido: {dados}")  # <-- importante!

            comando, *args = dados.split('|')

            if comando == 'LISTAR':
                arquivos = os.listdir(PASTA_ARQUIVOS)
                resposta = '|'.join(arquivos) if arquivos else 'VAZIO'
                conn.send(resposta.encode())

            elif comando == 'UPLOAD':
                nome_arquivo = args[0]
                tamanho = int(args[1])
                caminho = os.path.join(PASTA_ARQUIVOS, nome_arquivo)

                with open(caminho, 'wb') as f:
                    bytes_recebidos = 0
                    while bytes_recebidos < tamanho:
                        dados = conn.recv(min(1024, tamanho - bytes_recebidos))
                        f.write(dados)
                        bytes_recebidos += len(dados)
                conn.send(b'UPLOAD_OK')

            elif comando == 'DOWNLOAD':
                nome_arquivo = args[0]
                caminho = os.path.join(PASTA_ARQUIVOS, nome_arquivo)
                if os.path.exists(caminho):
                    tamanho = os.path.getsize(caminho)
                    conn.send(f'{tamanho}'.encode())
                    with open(caminho, 'rb') as f:
                        conn.sendall(f.read())
                else:
                    conn.send(b'ERRO')

            elif comando == 'EXCLUIR':
                nome_arquivo = args[0]
                caminho = os.path.join(PASTA_ARQUIVOS, nome_arquivo)
                if os.path.exists(caminho):
                    os.remove(caminho)
                    conn.send(b'EXCLUIDO')
                else:
                    conn.send(b'ERRO')

            else:
                print(f"[!] Comando desconhecido: {comando}")

        except Exception as e:
            print(f'Erro: {e}')
            break

    conn.close()
    print(f'[-] Cliente desconectado: {addr}')


def iniciar_servidor():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((HOST, PORT))
        s.listen()
        print(f'Servidor escutando em {HOST}:{PORT}')
        while True:
            conn, addr = s.accept()
            thread = threading.Thread(target=tratar_cliente, args=(conn, addr))
            thread.start()

if __name__ == '__main__':
    iniciar_servidor()
