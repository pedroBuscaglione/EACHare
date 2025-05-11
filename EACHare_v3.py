import socket
import sys
import threading

class Peer:
    def __init__(self, address, port, vizinhos_arquivo, shared_dir):  # Corrigi o parâmetro aqui
        self.address = address
        self.port = int(port)
        self.peers = {}  # Dicionário para armazenar os peers conhecidos e seu status (ONLINE/OFFLINE)
        self.clock = 0  # Relógio lógico
        self.shared_dir = shared_dir
        self.load_peers(vizinhos_arquivo)  # Uso correto do parâmetro
    
    def load_peers(self, file_path):
        """Carrega a lista de peers conhecidos do arquivo."""
        try:
            with open(file_path, 'r') as f:
                for line in f:
                    peer = line.strip()
                    if peer:
                        ip, port = peer.split(":")
                        self.peers[(ip, int(port))] = "OFFLINE"
                        print(f"Adicionando peer {ip}:{port} com status OFFLINE")
        except FileNotFoundError:
            print("Erro: Arquivo de vizinhos não encontrado.")
            sys.exit(1)
    
    def update_clock(self):
        """Incrementa o relógio lógico e exibe a atualização."""
        self.clock += 1
        print(f"=> Atualizando relógio para {self.clock}")
    
    def handle_client(self, conn, addr):
        """Lida com um cliente conectado."""
        with conn:
            message = conn.recv(1024).decode()
            print(f"Mensagem recebida de {addr}: \"{message}\"")
            self.update_clock()
    
    def start_server(self):
        """Inicia o servidor TCP em uma thread separada."""
        try:
            server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server_socket.bind((self.address, self.port))
            server_socket.listen()
            print(f"Peer iniciado em {self.address}:{self.port}, ouvindo conexões...\n")
            
            while True:
                conn, addr = server_socket.accept()
                threading.Thread(target=self.handle_client, args=(conn, addr)).start()
        except Exception as e:
            print(f"Erro ao iniciar o servidor: {e}")
            sys.exit(1)
    
    def send_message(self, peer_address, message):
        """Envia uma mensagem para um peer específico."""
        try:
            ip, port = peer_address
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect((ip, port))
                s.sendall(message.encode())
            print(f"Mensagem enviada para {ip}:{port}: \"{message}\"")
            self.update_clock()
        except Exception as e:
            print(f"Erro ao enviar mensagem para {peer_address}: {e}")

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Uso: python peer.py <endereco>:<porta> <vizinhos_arquivo> <shared_dir>")
        sys.exit(1)
    
    endereco, porta = sys.argv[1].split(":")
    vizinhos_arquivo = sys.argv[2]
    shared_dir = sys.argv[3]
    
    # Criando e iniciando um peer
    peer = Peer(endereco, porta, vizinhos_arquivo, shared_dir)  # Ajustei para usar vizinhos_arquivo corretamente
    threading.Thread(target=peer.start_server, daemon=True).start()
    
    while True:
        comando = input("Digite um comando (msg <ip>:<porta> <mensagem> ou sair): ")
        if comando.lower() == "sair":
            print("Encerrando peer...")
            sys.exit(0)
        elif comando.startswith("msg "):
            _, peer_info, mensagem = comando.split(" ", 2)
            ip, port = peer_info.split(":")
            peer.send_message((ip, int(port)), mensagem)