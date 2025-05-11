import socket
import sys

class Peer:
    def __init__(self, address, port, neighbors_file, shared_dir):
        self.address = address
        self.port = int(port)
        self.peers = {}  # Dicionário para armazenar os peers conhecidos e seu status (ONLINE/OFFLINE)
        self.clock = 0  # Relógio lógico
        self.shared_dir = shared_dir
        self.load_peers(neighbors_file)
        
    def load_peers(self, file_path):
        """Carrega a lista de peers conhecidos do arquivo."""
        try:
            with open(file_path, 'r') as f:
                for line in f:
                    peer = line.strip()
                    if peer:
                        self.peers[peer] = "OFFLINE"
                        print(f"Adicionando novo peer {peer} status OFFLINE")
        except FileNotFoundError:
            print("Erro: Arquivo de vizinhos não encontrado.")
            sys.exit(1)
        
    def update_clock(self):
        """Incrementa o relógio e exibe a atualização."""
        self.clock += 1
        print(f"=> Atualizando relogio para {self.clock}")
    
    def start_server(self):
        """Inicia o servidor TCP."""
        try:
            server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server_socket.bind((self.address, self.port))
            server_socket.listen()
            print(f"Peer iniciado em {self.address}:{self.port}, ouvindo conexões...\n")
            
            while True:
                conn, addr = server_socket.accept()
                with conn:
                    message = conn.recv(1024).decode()
                    print(f"Mensagem recebida: \"{message}\"")
                    self.update_clock()
        except Exception as e:
            print(f"Erro ao iniciar o servidor: {e}")
            sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Uso: python eachare.py <endereco>:<porta> <vizinhos.txt> <diretorio_compartilhado>")
        sys.exit(1)
    
    endereco, porta = sys.argv[1].split(":")
    vizinhos_arquivo = sys.argv[2]  # Agora isso vai pegar corretamente o arquivo "vizinhos.txt"
    shared_dir = sys.argv[3]
    
    # Criando e iniciando um peer
    peer = Peer(endereco, porta, vizinhos_arquivo, shared_dir)
    peer.start_server()
