import socket
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog, ttk
import os

HOST = 'localhost'
PORT = 5000

class ClienteApp:
    def __init__(self, master):
        self.master = master
        self.master.title("Cliente - Servidor de Arquivos")
        self.master.geometry("500x450")
        self.master.resizable(True, True)

        self.style = ttk.Style()
        self.style.theme_use('clam')
        self.style.configure("TButton", font=("Helvetica", 10), padding=5)
        self.style.configure("TLabel", font=("Helvetica", 10))

        main_frame = ttk.Frame(master, padding="10 10 10 10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        try:
            self.conexao = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.conexao.connect((HOST, PORT))
            self.status_bar = ttk.Label(master, text=f"Conectado ao servidor em {HOST}:{PORT}", relief=tk.SUNKEN, anchor=tk.W)
        except Exception as e:
            messagebox.showerror("Erro de Conexão", f"Não foi possível conectar ao servidor: {e}")
            self.master.destroy()
            return
        
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)


        list_frame = ttk.Frame(main_frame)
        list_frame.pack(pady=10, fill=tk.BOTH, expand=True)

        self.arquivos_listbox = tk.Listbox(list_frame, width=50, height=15, font=("Courier New", 10))
        self.arquivos_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.arquivos_listbox.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.arquivos_listbox.config(yscrollcommand=scrollbar.set)

        button_frame = ttk.Frame(main_frame)
        button_frame.pack(pady=10)

        ttk.Button(button_frame, text="Atualizar Lista", command=self.listar_arquivos).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Upload", command=self.enviar_arquivo).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Download", command=self.baixar_arquivo).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Excluir", command=self.excluir_arquivo).pack(side=tk.LEFT, padx=5)

        self.listar_arquivos()

    def update_status(self, message):
        self.status_bar.config(text=message)

    def listar_arquivos(self):
        try:
            self.conexao.send(b'LISTAR')
            self.update_status("Solicitando lista de arquivos...")
            dados = self.conexao.recv(4096)
            if not dados:
                messagebox.showerror("Erro", "Servidor não respondeu.")
                self.update_status("Erro: Servidor não respondeu.")
                return

            arquivos = dados.decode().split('|')
            self.arquivos_listbox.delete(0, tk.END)

            if arquivos == ['VAZIO'] or not arquivos[0]:
                self.arquivos_listbox.insert(tk.END, "(Nenhum arquivo no servidor)")
                self.update_status("Lista de arquivos atualizada: Nenhum arquivo.")
                return

            for nome in arquivos:
                if nome:
                    self.arquivos_listbox.insert(tk.END, nome)
            self.update_status(f"Lista de arquivos atualizada: {len(arquivos)} arquivos.")

        except Exception as e:
            messagebox.showerror("Erro ao listar arquivos", str(e))
            self.update_status(f"Erro ao listar arquivos: {e}")

    def enviar_arquivo(self):
        caminho = filedialog.askopenfilename()
        if not caminho:
            return
        nome = os.path.basename(caminho)
        tamanho = os.path.getsize(caminho)
        try:
            self.conexao.send(f'UPLOAD|{nome}|{tamanho}'.encode())
            self.update_status(f"Enviando arquivo: {nome} ({tamanho} bytes)...")
            with open(caminho, 'rb') as f:
                self.conexao.sendall(f.read())
            resp = self.conexao.recv(1024)
            messagebox.showinfo("Envio", resp.decode())
            self.update_status(f"Envio de '{nome}' concluído: {resp.decode()}")
            self.listar_arquivos()
        except Exception as e:
            messagebox.showerror("Erro de Upload", str(e))
            self.update_status(f"Erro ao enviar arquivo: {e}")

    def baixar_arquivo(self):
        selecionado = self.arquivos_listbox.get(tk.ACTIVE)
        if not selecionado or selecionado == "(Nenhum arquivo no servidor)":
            messagebox.showwarning("Seleção", "Por favor, selecione um arquivo para baixar.")
            return

        try:
            self.conexao.send(f'DOWNLOAD|{selecionado}'.encode())
            self.update_status(f"Solicitando download de: {selecionado}...")
            tamanho = self.conexao.recv(1024).decode()
            if tamanho == 'ERRO':
                messagebox.showerror("Erro", "Arquivo não encontrado no servidor.")
                self.update_status(f"Erro: Arquivo '{selecionado}' não encontrado.")
                return

            caminho = filedialog.asksaveasfilename(defaultextension="", initialfile=selecionado)
            if not caminho:
                self.update_status("Download cancelado pelo usuário.")
                return

            tamanho = int(tamanho)
            self.update_status(f"Baixando '{selecionado}' ({tamanho} bytes)...")
            with open(caminho, 'wb') as f:
                bytes_recebidos = 0
                while bytes_recebidos < tamanho:
                    dados = self.conexao.recv(min(4096, tamanho - bytes_recebidos))
                    if not dados:
                        raise ConnectionResetError("Conexão com o servidor perdida durante o download.")
                    f.write(dados)
                    bytes_recebidos += len(dados)
            messagebox.showinfo("Download", "Download concluído com sucesso!")
            self.update_status(f"Download de '{selecionado}' concluído com sucesso.")

        except Exception as e:
            messagebox.showerror("Erro de Download", str(e))
            self.update_status(f"Erro ao baixar arquivo: {e}")

    def excluir_arquivo(self):
        selecionado = self.arquivos_listbox.get(tk.ACTIVE)
        if not selecionado or selecionado == "(Nenhum arquivo no servidor)":
            messagebox.showwarning("Seleção", "Por favor, selecione um arquivo para excluir.")
            return

        if not messagebox.askyesno("Confirmação de Exclusão", f"Tem certeza que deseja excluir '{selecionado}'?"):
            return

        try:
            self.conexao.send(f'EXCLUIR|{selecionado}'.encode())
            self.update_status(f"Solicitando exclusão de: {selecionado}...")
            resp = self.conexao.recv(1024)
            messagebox.showinfo("Exclusão", resp.decode())
            self.update_status(f"Exclusão de '{selecionado}': {resp.decode()}")
            self.listar_arquivos()
        except Exception as e:
            messagebox.showerror("Erro de Exclusão", str(e))
            self.update_status(f"Erro ao excluir arquivo: {e}")

if __name__ == '__main__':
    print("Iniciando cliente...")
    root = tk.Tk()
    app = ClienteApp(root)
    root.mainloop()