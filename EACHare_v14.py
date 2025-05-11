import sys
import os
import socket
import threading

class Clock:
    def __init__(self):
        self.valor = 0
        self.lock = threading.Lock()

    def incrementar(self):
        with self.lock:
            self.valor += 1
            print(f"=> Atualizando relogio para {self.valor}")
            return self.valor

    def atualizar(self, valor_recebido):
        with self.lock:
            self.valor = max(self.valor, valor_recebido) + 1
            print(f"=> Atualizando relogio para {self.valor}")
            return self.valor

class Peer:
    def __init__(self, endereco, porta):
        self.endereco = endereco
        self.porta = porta
        self.estado = "OFFLINE"

    def atualizar_estado(self, novo_estado):
        self.estado = novo_estado
        print(f"Atualizando peer {self.endereco}:{self.porta} status {novo_estado}")

class Mensagem:
    def __init__(self, origem, clock, tipo, argumentos=None):
        self.origem = origem
        self.clock = clock
        self.tipo = tipo
        self.argumentos = argumentos or []

    def construir_mensagem(self):
        mensagem = f"{self.origem} {self.clock} {self.tipo}"
        if self.argumentos:
            mensagem += " " + " ".join(self.argumentos)
        mensagem += "\n"
        return mensagem

    @staticmethod
    def analisar_mensagem(mensagem_str):
        partes = mensagem_str.strip().split(" ")
        
        if len(partes) < 3:
            raise ValueError(f"Formato inválido da mensagem recebida: '{mensagem_str}'")

        try:
            origem = partes[0]
            clock = int(partes[1])  # <- Aqui ocorre o erro
            tipo = partes[2]
            argumentos = partes[3:]
        except ValueError:
            raise ValueError(f"Erro ao converter clock para inteiro na mensagem: '{mensagem_str}'")

        return Mensagem(origem, clock, tipo, argumentos)
    
def listar_peers(lista_vizinhos, endereco_porta, clock):
    """Lista os peers conhecidos e permite enviar mensagem HELLO"""
    print("\nLista de peers:")
    for i, peer in enumerate(lista_vizinhos):
        print(f"[{i+1}] {peer.endereco}:{peer.porta} {peer.estado}")
    print("[0] Voltar ao menu anterior")

    escolha = input("> ")
    if escolha == "0":
        return
    elif escolha.isdigit() and int(escolha) <= len(lista_vizinhos):
        peer_selecionado = lista_vizinhos[int(escolha)-1]
        clock.incrementar()
        mensagem = Mensagem(endereco_porta, clock.valor, "HELLO").construir_mensagem()
        print(f"Encaminhando mensagem '{mensagem.strip()}' para {peer_selecionado.endereco}:{peer_selecionado.porta}")

        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as cliente:
                cliente.settimeout(5)
                cliente.connect((peer_selecionado.endereco, peer_selecionado.porta))
                cliente.sendall(mensagem.encode())
                print(f"=> Mensagem enviada com sucesso!")
                peer_selecionado.atualizar_estado("ONLINE")
        except (socket.timeout, ConnectionRefusedError, OSError) as e:
            print(f"Erro ao conectar com o peer {peer_selecionado.endereco}:{peer_selecionado.porta}: {e}")
            peer_selecionado.atualizar_estado("OFFLINE")

    else:
        print("Opção inválida.")

def obter_peers(lista_vizinhos, endereco_porta, clock):
    """Percorre a lista de peers conhecidos e envia a mensagem GET_PEERS para cada um"""
    vizinhos_atuais = list(lista_vizinhos)

    for peer in vizinhos_atuais:
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

        except (socket.timeout, ConnectionRefusedError):
            print(f"Não foi possível conectar ao peer {peer.endereco}:{peer.porta}")
            if peer.estado == "ONLINE":
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
            print(f"Adicionando novo peer {endereco}:{porta} status {status}")
            novo_peer.atualizar_estado(status)
            lista_vizinhos.append(novo_peer)

def listar_arquivos(diretorio_compartilhado):
    try:
        arquivos = os.listdir(diretorio_compartilhado)
        print("\nArquivos compartilhados:")
        for arquivo in arquivos:
            print(arquivo)
    except FileNotFoundError:
        print(f"Erro: Diretório '{diretorio_compartilhado}' não encontrado.")

def sair(lista_vizinhos, endereco_porta, clock, servidor):
    """Envia mensagem de saída para os vizinhos e encerra o peer."""
    print("Encerrando peer...")
    for peer in lista_vizinhos:
        clock.incrementar()
        mensagem = Mensagem(endereco_porta, clock.valor, "BYE").construir_mensagem()
        print(f'Encaminhando mesndagem "{mensagem}" para {peer.endereco}:{peer.porta}')
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as cliente:
                cliente.settimeout(5)
                cliente.connect((peer.endereco, peer.porta))
                cliente.sendall(mensagem.encode())
        except (socket.timeout, ConnectionRefusedError):
            print(f"Falha ao notificar {peer.endereco}:{peer.porta}")
    
    servidor.close()
    print("Peer encerrado com sucesso.")
    sys.exit(0)

def processar_conexao(conexao, endereco, clock, lista_vizinhos, diretorio_compartilhado):
    dados = conexao.recv(1024).decode()
    if not dados:
        return
    
    mensagem = Mensagem.analisar_mensagem(dados)
    clock.atualizar(mensagem.clock)
    print(f"Mensagem recebida: {dados.strip()}")
    
    if mensagem.tipo == "HELLO":
        peer_existente = next((p for p in lista_vizinhos if p.endereco == mensagem.origem.split(":")[0] and p.porta == int(mensagem.origem.split(":")[1])), None)
        if peer_existente:
            peer_existente.atualizar_estado("ONLINE")
        else:
            novo_peer = Peer(mensagem.origem.split(":")[0], int(mensagem.origem.split(":")[1]))
            novo_peer.atualizar_estado("ONLINE")
            lista_vizinhos.append(novo_peer)
    elif mensagem.tipo == "GET_PEERS":
        endereco_str = f"{endereco[0]}:{endereco[1]}"
        resposta = Mensagem(
            endereco_str,
            clock.valor,
            "PEER_LIST",
            [str(len(lista_vizinhos))] + [f"{p.endereco}:{p.porta}:{p.estado}:0" for p in lista_vizinhos]
        ).construir_mensagem()
        conexao.sendall(resposta.encode())
    elif mensagem.tipo == "LIST_FILES":
        arquivos = os.listdir(diretorio_compartilhado)
        resposta = Mensagem(endereco, clock.valor, "FILE_LIST", arquivos).construir_mensagem()
        conexao.sendall(resposta.encode())
    elif mensagem.tipo == "BYE":
        endereco_str = f"{endereco[0]}:{endereco[1]}"
        peer_existente = next((p for p in lista_vizinhos if p.endereco == mensagem.origem.split(":")[0] and p.porta == int(mensagem.origem.split(":")[1])), None)
        if peer_existente:
            peer_existente.atualizar_estado("OFFLINE")
            print(f"Atualizando peer: {endereco_str} status {peer_existente.estado}")

def aceitar_conexoes(servidor, clock, lista_vizinhos, diretorio_compartilhado):
    while True:
        conexao, endereco = servidor.accept()
        thread = threading.Thread(target=processar_conexao, args=(conexao, endereco, clock, lista_vizinhos, diretorio_compartilhado))
        thread.start()

def iniciar_servidor(servidor, clock, lista_vizinhos, diretorio_compartilhado):
    thread_servidor = threading.Thread(target=aceitar_conexoes, args=(servidor, clock, lista_vizinhos, diretorio_compartilhado))
    thread_servidor.daemon = True  # Termina quando o programa principal encerra
    thread_servidor.start()
    return thread_servidor

def configurar_socket(endereco_porta):
    endereco, porta = endereco_porta.split(":")
    servidor = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    servidor.bind((endereco, int(porta)))
    servidor.listen()
    print(f"Peer escutando em {endereco}:{porta}")
    return servidor

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

def exibir_menu(lista_vizinhos, endereco_porta, clock, diretorio_compartilhado, servidor):
    """Exibe o menu principal e processa os comandos do usuário"""
    while True:
        print("\nEscolha um comando:")
        print("[1] Listar peers")
        print("[2] Obter peers")
        print("[3] Listar arquivos locais")
        print("[9] Sair")
        comando = input("> ")

        if comando == "1":
            listar_peers(lista_vizinhos, endereco_porta, clock)
        elif comando == "2":
            obter_peers(lista_vizinhos, endereco_porta, clock)
        elif comando == "3":
            listar_arquivos(diretorio_compartilhado)
        elif comando == "9":
            sair(lista_vizinhos, endereco_porta, clock, servidor)
        else:
            print("Comando inválido. Tente novamente.")

if __name__ == "__main__":
    endereco_porta, lista_vizinhos, diretorio_compartilhado = inicializar_programa()
    clock = Clock()
    servidor = configurar_socket(endereco_porta)
    iniciar_servidor(servidor, clock, lista_vizinhos, diretorio_compartilhado)
    exibir_menu(lista_vizinhos, endereco_porta, clock, diretorio_compartilhado, servidor)