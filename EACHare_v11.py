import sys
import os
import socket

# Classe Clock para gerenciar o relógio local
class Clock:
    def __init__(self):
        self.valor = 0  # Inicializa o relógio com valor 0

    def incrementar(self):
        """Incrementa o valor do relógio em 1 e exibe uma mensagem"""
        self.valor += 1
        print(f"=> Atualizando relogio para {self.valor}")
        return self.valor

    def atualizar(self, valor_recebido):
        """Atualiza o valor do relógio considerando mensagens recebidas"""
        self.valor = max(self.valor, valor_recebido) + 1
        print(f"=> Atualizando relogio para {self.valor}")
        return self.valor

# Classe Peer para representar os vizinhos conhecidos
class Peer:
    def __init__(self, endereco, porta):
        self.endereco = endereco
        self.porta = porta
        self.estado = "OFFLINE"

    def atualizar_estado(self, novo_estado):
        """Atualiza o estado do peer (ONLINE ou OFFLINE)"""
        self.estado = novo_estado
        print(f"Atualizando peer {self.endereco}:{self.porta} status {novo_estado}")

# Classe Mensagem para gerenciar a criação e análise de mensagens
class Mensagem:
    def __init__(self, origem, clock, tipo, argumentos=None):
        self.origem = origem
        self.clock = clock
        self.tipo = tipo
        self.argumentos = argumentos or []

    def construir_mensagem(self):
        """Constrói a mensagem em formato string para ser enviada"""
        mensagem = f"{self.origem} {self.clock} {self.tipo}"
        if self.argumentos:
            mensagem += " " + " ".join(self.argumentos)
        mensagem += "\n"
        return mensagem

    @staticmethod
    def analisar_mensagem(mensagem_str):
        """Analisa uma mensagem recebida e retorna uma instância da classe Mensagem"""
        partes = mensagem_str.strip().split(" ")
        origem = partes[0]
        clock = int(partes[1])
        tipo = partes[2]
        argumentos = partes[3:]
        return Mensagem(origem, clock, tipo, argumentos)

    def exibir_mensagem(self):
        """Exibe a mensagem formatada"""
        print(f"Mensagem formatada: {self.construir_mensagem().strip()}")

def inicializar_programa():
    """Inicializa o programa e valida os parâmetros"""
    if len(sys.argv) != 4:
        print("Uso: python <nome_do_arquivo>.py <endereco>:<porta> <vizinhos.txt> <diretorio_compartilhado>")
        sys.exit(1)

    endereco_porta = sys.argv[1]
    arquivo_vizinhos = sys.argv[2]
    diretorio_compartilhado = sys.argv[3]

    if ":" not in endereco_porta or not endereco_porta.split(":")[1].isdigit():
        print("Erro: Formato inválido de endereço:porta.")
        sys.exit(1)

    if not os.path.isfile(arquivo_vizinhos):
        print(f"Erro: Arquivo de vizinhos '{arquivo_vizinhos}' não encontrado.")
        sys.exit(1)

    if not os.path.isdir(diretorio_compartilhado):
        print(f"Erro: Diretório compartilhado '{diretorio_compartilhado}' não encontrado ou inválido.")
        sys.exit(1)

    print("Parâmetros de inicialização lidos com sucesso!")
    print(f"Endereço e Porta: {endereco_porta}")
    print(f"Arquivo de Vizinhos: {arquivo_vizinhos}")
    print(f"Diretório Compartilhado: {diretorio_compartilhado}")

    lista_vizinhos = []
    with open(arquivo_vizinhos, "r") as arquivo:
        for linha in arquivo:
            linha = linha.strip()
            if linha:
                endereco_peer, porta_peer = linha.split(":")
                peer = Peer(endereco_peer, int(porta_peer))
                lista_vizinhos.append(peer)
                print(f"Adicionando novo peer {linha} status {peer.estado}")

    print("Lista de peers inicializada com sucesso!")
    return endereco_porta, lista_vizinhos, diretorio_compartilhado

def configurar_socket(endereco_porta):
    """Configura o socket TCP para escutar conexões"""
    endereco, porta = endereco_porta.split(":")
    servidor = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    servidor.bind((endereco, int(porta)))
    servidor.listen()
    print(f"Peer escutando em {endereco}:{porta}")
    return servidor

def obter_peers(lista_vizinhos, endereco_porta, clock):
    """Percorre a lista de peers conhecidos e envia a mensagem GET_PEERS para cada um"""
    for peer in lista_vizinhos:
        clock.incrementar()
        mensagem = Mensagem(endereco_porta, clock.valor, "GET_PEERS").construir_mensagem()
        print(f"Encaminhando mensagem '{mensagem.strip()}' para {peer.endereco}:{peer.porta}")
        
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as cliente:
                cliente.settimeout(5)
                cliente.connect((peer.endereco, peer.porta))
                cliente.sendall(mensagem.encode())
                resposta = cliente.recv(1024).decode()
                
                mensagem_resposta = Mensagem.analisar_mensagem(resposta)
                if mensagem_resposta.tipo == "PEER_LIST":
                    print(f"Resposta recebida: '{resposta.strip()}'")
                    processar_peer_list(mensagem_resposta.argumentos, lista_vizinhos)
                
                peer.atualizar_estado("ONLINE")
        except (socket.timeout, ConnectionRefusedError):
            print(f"Não foi possível conectar ao peer {peer.endereco}:{peer.porta}")
            peer.atualizar_estado("OFFLINE")

def processar_peer_list(argumentos, lista_vizinhos):
    """Atualiza a lista de peers conhecidos com base na mensagem PEER_LIST recebida"""
    quantidade_peers = int(argumentos[0])
    novos_peers = argumentos[1:]
    
    for peer_info in novos_peers:
        endereco, porta, status, _ = peer_info.split(":")
        peer_existente = next((p for p in lista_vizinhos if p.endereco == endereco and p.porta == int(porta)), None)
        
        if peer_existente:
            peer_existente.atualizar_estado(status)
        else:
            novo_peer = Peer(endereco, int(porta))
            novo_peer.atualizar_estado(status)
            lista_vizinhos.append(novo_peer)
            print(f"Adicionando novo peer {endereco}:{porta} status {status}")

def exibir_menu(lista_vizinhos, endereco_porta, clock):
    """Exibe o menu principal e processa os comandos do usuário"""
    while True:
        print("\nEscolha um comando:")
        print("[1] Listar peers")
        print("[2] Obter peers")
        print("[9] Sair")
        comando = input("> ")

        if comando == "1":
            listar_peers(lista_vizinhos, endereco_porta, clock)
        elif comando == "2":
            obter_peers(lista_vizinhos, endereco_porta, clock)
        elif comando == "9":
            print("Saindo...")
            break
        else:
            print("Comando inválido. Tente novamente.")

def listar_peers(lista_vizinhos, endereco_porta, clock):
    """Lista os peers conhecidos e permite enviar mensagem HELLO"""
    print("\nLista de peers:")
    for i, peer in enumerate(lista_vizinhos):
        print(f"[{i}] {peer.endereco}:{peer.porta} {peer.estado}")
    print("[0] Voltar ao menu anterior")

    escolha = input("> ")
    if escolha == "0":
        return
    elif escolha.isdigit() and int(escolha) < len(lista_vizinhos):
        peer_selecionado = lista_vizinhos[int(escolha)]
        clock.incrementar()
        mensagem = Mensagem(endereco_porta, clock.valor, "HELLO").construir_mensagem()
        print(f"Encaminhando mensagem '{mensagem.strip()}' para {peer_selecionado.endereco}:{peer_selecionado.porta}")
        peer_selecionado.atualizar_estado("ONLINE")  # Simulação
    else:
        print("Opção inválida.")

# Inicia o programa
if __name__ == "__main__":
    endereco_porta, lista_vizinhos, diretorio_compartilhado = inicializar_programa()
    servidor = configurar_socket(endereco_porta)
    clock = Clock()
    exibir_menu(lista_vizinhos, endereco_porta, clock)