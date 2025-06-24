import socket
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog
import os

HOST = 'localhost'
PORT = 5000

class ClienteApp:
    def __init__(self, master):
        self.master = master
        self.master.title("Cliente - Servidor de Arquivos")
        
        self.conexao = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.conexao.connect((HOST, PORT))

        self.arquivos_listbox = tk.Listbox(master, width=50)
        self.arquivos_listbox.pack(pady=10)

        tk.Button(master, text="Atualizar Lista", command=self.listar_arquivos).pack()
        tk.Button(master, text="Upload", command=self.enviar_arquivo).pack()
        tk.Button(master, text="Download", command=self.baixar_arquivo).pack()
        tk.Button(master, text="Excluir", command=self.excluir_arquivo).pack()

        self.listar_arquivos()

    def listar_arquivos(self):
        try:
            self.conexao.send(b'LISTAR')
            dados = self.conexao.recv(4096)
            if not dados:
                messagebox.showerror("Erro", "Servidor não respondeu.")
                return

            arquivos = dados.decode().split('|')
            self.arquivos_listbox.delete(0, tk.END)

            # Se a resposta for 'VAZIO', não mostra nada (lista vazia)
            if arquivos == ['VAZIO']:
                return

            for nome in arquivos:
                if nome:
                    self.arquivos_listbox.insert(tk.END, nome)

        except Exception as e:
            messagebox.showerror("Erro ao listar arquivos", str(e))


    def enviar_arquivo(self):
        caminho = filedialog.askopenfilename()
        if not caminho:
            return
        nome = os.path.basename(caminho)
        tamanho = os.path.getsize(caminho)
        self.conexao.send(f'UPLOAD|{nome}|{tamanho}'.encode())
        with open(caminho, 'rb') as f:
            self.conexao.sendall(f.read())
        resp = self.conexao.recv(1024)
        messagebox.showinfo("Envio", resp.decode())
        self.listar_arquivos()

    def baixar_arquivo(self):
        selecionado = self.arquivos_listbox.get(tk.ACTIVE)
        if not selecionado:
            return
        self.conexao.send(f'DOWNLOAD|{selecionado}'.encode())
        tamanho = self.conexao.recv(1024).decode()
        if tamanho == 'ERRO':
            messagebox.showerror("Erro", "Arquivo não encontrado")
            return

        caminho = filedialog.asksaveasfilename(defaultextension="", initialfile=selecionado)
        if not caminho:
            return
        tamanho = int(tamanho)
        with open(caminho, 'wb') as f:
            bytes_recebidos = 0
            while bytes_recebidos < tamanho:
                dados = self.conexao.recv(min(1024, tamanho - bytes_recebidos))
                f.write(dados)
                bytes_recebidos += len(dados)
        messagebox.showinfo("Download", "Download concluído com sucesso")

    def excluir_arquivo(self):
        selecionado = self.arquivos_listbox.get(tk.ACTIVE)
        if not selecionado:
            return
        self.conexao.send(f'EXCLUIR|{selecionado}'.encode())
        resp = self.conexao.recv(1024)
        messagebox.showinfo("Exclusão", resp.decode())
        self.listar_arquivos()

if __name__ == '__main__':
    print("Iniciando cliente...")  # <-- Confirmar que o código está rodando
    root = tk.Tk()
    app = ClienteApp(root)
    root.mainloop()

