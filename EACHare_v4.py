#######################################################################
# Discentes: Mariana Borges Araujo da Silva - 14596342                #
#            Pedro Serrano Buscaglione - 14603652                     #
# Docente: Prof Dr. Renan Cerqueira Afonso Alves                      #
# Disciplina: Desenvolvimento de Sistemas de Informações Distribuídos #
# Turma 094                                                           #
#######################################################################

# O seguinte exercício-programa tem como objetivo simular um 
# sistema distribuído peer-to-peer com funcionalidades de descoberta de vizinhos, troca de mensagens, 
# controle de estado e compartilhamento de arquivos. A linguagem utilizada no EP é Python

import sys
import os
import socket
import threading
import base64


# CLASSE CLOCK: relógio  de lamport

class Clock:
    def __init__(self):
        self.valor = 0
        self.lock = threading.Lock()  # Exclusão mútua para uso em múltiplas threads

    def incrementar(self):
        # Incrementa o clock local antes de enviar uma mensagem
        with self.lock:
            self.valor += 1
            print(f"=> Atualizando relogio para {self.valor}")
            return self.valor

    def atualizar(self, valor_recebido):
        # Atualiza o clock local com base no valor recebido de outro peer
        with self.lock:
            self.valor = max(self.valor, valor_recebido) + 1
            print(f"=> Atualizando relogio para {self.valor}")
            return self.valor


# CLASSE PEER: representa um vizinho conhecido 

class Peer:
    def __init__(self, endereco, porta):
        self.endereco = endereco
        self.porta = porta
        self.estado = "OFFLINE"  # Estado inicial
        self.relogio = 0

    def atualizar_estado(self, novo_estado):
        self.estado = novo_estado
        print(f"Atualizando peer {self.endereco}:{self.porta} status {novo_estado}")


# CLASSE MENSAGEM: encapsula mensagens compartilhadas

class Mensagem:
    def __init__(self, origem, clock, tipo, argumentos=None):
        self.origem = origem  # Ex: '127.0.0.1:5000'
        self.clock = clock    # tempo lógico no envio
        self.tipo = tipo      # tipo da mensagem 
        self.argumentos = argumentos or []

    def construir_mensagem(self):
        # faz a string da mensagem para enviar via socket
        mensagem = f"{self.origem} {self.clock} {self.tipo}"
        if self.argumentos:
            mensagem += " " + " ".join(self.argumentos)
        mensagem += "\n"
        return mensagem

    @staticmethod
    def analisar_mensagem(mensagem_str):
        # Divide a string recebida em partes
        partes = mensagem_str.strip().split(" ")
        
        if len(partes) < 3:
            raise ValueError(f"Formato inválido da mensagem recebida: '{mensagem_str}'")

        try:
            origem = partes[0]
            clock = int(partes[1])  # Tempo lógico
            tipo = partes[2]
            argumentos = partes[3:]
        except ValueError:
            raise ValueError(f"Erro ao converter clock para inteiro na mensagem: '{mensagem_str}'")

        return Mensagem(origem, clock, tipo, argumentos)


# Funções principais do MENU


def listar_peers(lista_vizinhos, endereco_porta, clock):
    # Exibe a lista de peers e permite selecionar um para enviar "HELLO"
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
            # Tenta conexão com o peer e envia a mensagem
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
    # Solicita a lista de peers conhecidos a cada vizinho
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
    # Recebe a resposta do tipo PEER_LIST e atualiza a lista local
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
    # Lista os arquivos do diretório compartilhado local
    try:
        arquivos = os.listdir(diretorio_compartilhado)
        print("\nArquivos compartilhados:")
        for arquivo in arquivos:
            print(arquivo)
    except FileNotFoundError:
        print(f"Erro: Diretório '{diretorio_compartilhado}' não encontrado.")

def sair(lista_vizinhos, endereco_porta, clock, servidor):
    # Envia BYE para todos os peers e encerra o programa
    print("Encerrando peer...")
    for peer in lista_vizinhos:
        clock.incrementar()
        mensagem = Mensagem(endereco_porta, clock.valor, "BYE").construir_mensagem()
        print(f'Encaminhando mensagem "{mensagem}" para {peer.endereco}:{peer.porta}')
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

def buscar_arquivos(lista_vizinhos, endereco_porta, clock):
    arquivos_encontrados = []
    for peer in lista_vizinhos:
        if peer.estado != "ONLINE":
            continue
        clock.incrementar()
        mensagem = Mensagem(endereco_porta, clock.valor, "LS").construir_mensagem()
        print(f"Encaminhando mensagem \"{mensagem.strip()}\" para {peer.endereco}:{peer.porta}")
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as cliente:
                cliente.settimeout(5)
                cliente.connect((peer.endereco, peer.porta))
                cliente.sendall(mensagem.encode())
                resposta = cliente.recv(8192).decode()
                resposta_mensagem = Mensagem.analisar_mensagem(resposta)
                clock.atualizar(resposta_mensagem.clock)
                peer.atualizar_estado("ONLINE")
                quantidade = int(resposta_mensagem.argumentos[0])
                for info in resposta_mensagem.argumentos[1:]:
                    nome, tamanho = info.split(":")
                    arquivos_encontrados.append((nome, tamanho, f"{peer.endereco}:{peer.porta}"))
        except Exception as e:
            print(f"Erro ao conectar com {peer.endereco}:{peer.porta}: {e}")
            peer.atualizar_estado("OFFLINE")

    print("\nArquivos encontrados na rede:")
    print("Nome | Tamanho | Peer")
    print("[ 0] <Cancelar> | |")
    for i, (nome, tamanho, peer_end) in enumerate(arquivos_encontrados, 1):
        print(f"[{i}] {nome} | {tamanho} | {peer_end}")

    escolha = input("\nDigite o numero do arquivo para fazer o download:\n> ")
    if escolha.isdigit():
        escolha = int(escolha)
        if escolha == 0 or escolha > len(arquivos_encontrados):
            return
        nome, tamanho, peer_end = arquivos_encontrados[escolha - 1]
        endereco, porta = peer_end.split(":")
        realizar_download(endereco, int(porta), nome, clock, endereco_porta)

def realizar_download(endereco, porta, nome_arquivo, clock, endereco_porta):
    clock.incrementar()
    mensagem = Mensagem(endereco_porta, clock.valor, "DL", [nome_arquivo, "0", "0"]).construir_mensagem()
    print(f"=> Atualizando relogio para {clock.valor}")
    print(f"Encaminhando mensagem \"{mensagem.strip()}\" para {endereco}:{porta}")
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as cliente:
            cliente.settimeout(5)
            cliente.connect((endereco, porta))
            cliente.sendall(mensagem.encode())
            resposta = cliente.recv(10 * 1024 * 1024).decode()
            mensagem_resposta = Mensagem.analisar_mensagem(resposta)
            clock.atualizar(mensagem_resposta.clock)
            nome, _, _, conteudo_base64 = mensagem_resposta.argumentos
            caminho_arquivo = os.path.join("compartilhado", nome)  # Alteração feita aqui,  garante 
                                                                    #que o caminho do arquivo seja construído de forma independente do sistema operacional
            with open(caminho_arquivo, "wb") as f:
                f.write(base64.b64decode(conteudo_base64))
            print(f"Download do arquivo {nome} finalizado.")
    except Exception as e:
        print(f"Erro no download: {e}")

# SERVIDOR: escuta novas conexoões dos peers

def processar_conexao(conexao, endereco, clock, lista_vizinhos, diretorio_compartilhado):
    dados = conexao.recv(1024).decode()
    if not dados:
        return
    
    mensagem = Mensagem.analisar_mensagem(dados)
    clock.atualizar(mensagem.clock)
    print(f"Mensagem recebida: {dados.strip()}")
    tipo = mensagem.tipo
    origem = mensagem.origem
    endereco_remetente, porta_remetente = origem.split(":")
    porta_remetente = int(porta_remetente)
    peer_existente = next((p for p in lista_vizinhos if p.endereco == endereco_remetente and p.porta == porta_remetente), None)

    if not peer_existente:
        peer_existente = Peer(endereco_remetente, porta_remetente)
        lista_vizinhos.append(peer_existente)
    peer_existente.atualizar_estado("ONLINE")
    if mensagem.clock > peer_existente.relogio:
        peer_existente.relogio = mensagem.clock

    if tipo == "HELLO":
        # Atualiza ou adiciona peer como ONLINE
        peer_existente = next((p for p in lista_vizinhos if p.endereco == origem.split(":")[0] and p.porta == int(origem.split(":")[1])), None)
        if peer_existente:
            peer_existente.atualizar_estado("ONLINE")
        else:
            novo_peer = Peer(origem.split(":")[0], int(origem.split(":")[1]))
            novo_peer.atualizar_estado("ONLINE")
            lista_vizinhos.append(novo_peer)

    elif tipo == "GET_PEERS":
        # Responde com a lista atual de peers
        endereco_str = f"{endereco[0]}:{endereco[1]}"
        resposta = Mensagem(
            endereco_str,
            clock.valor,
            "PEER_LIST",
            [str(len(lista_vizinhos))] + [f"{p.endereco}:{p.porta}:{p.estado}:0" for p in lista_vizinhos]
        ).construir_mensagem()
        conexao.sendall(resposta.encode())

    elif tipo == "LIST_FILES":
        arquivos = os.listdir(diretorio_compartilhado)
        resposta = Mensagem(endereco, clock.valor, "FILE_LIST", arquivos).construir_mensagem()
        conexao.sendall(resposta.encode())

    elif tipo == "BYE":
        # Marca peer como OFFLINE
        peer_existente = next((p for p in lista_vizinhos if p.endereco == origem.split(":")[0] and p.porta == int(origem.split(":")[1])), None)
        if peer_existente:
            peer_existente.atualizar_estado("OFFLINE")
    
    if tipo == "LS":
        arquivos = os.listdir(diretorio_compartilhado)
        lista_arquivos = [f"{nome}:{os.path.getsize(os.path.join(diretorio_compartilhado, nome))}" for nome in arquivos]
        resposta = Mensagem(f"{endereco[0]}:{endereco[1]}", clock.valor, "LS_LIST", [str(len(lista_arquivos))] + lista_arquivos).construir_mensagem()
        conexao.sendall(resposta.encode())

    elif tipo == "DL":
        nome_arquivo = mensagem.argumentos[0]
        caminho = os.path.join(diretorio_compartilhado, nome_arquivo)
        if os.path.exists(caminho):
            with open(caminho, "rb") as f:
                conteudo = f.read()
            conteudo_b64 = base64.b64encode(conteudo).decode()
            resposta = Mensagem(f"{endereco[0]}:{endereco[1]}", clock.valor, "FILE", [nome_arquivo, "0", "0", conteudo_b64]).construir_mensagem()
            conexao.sendall(resposta.encode())


def aceitar_conexoes(servidor, clock, lista_vizinhos, diretorio_compartilhado):
    # Loop contínuo para aceitar conexões e delegar threads
    while True:
        conexao, endereco = servidor.accept()
        thread = threading.Thread(target=processar_conexao, args=(conexao, endereco, clock, lista_vizinhos, diretorio_compartilhado))
        thread.start()

# INICIALIZAÇÃO

def iniciar_servidor(servidor, clock, lista_vizinhos, diretorio_compartilhado):
    # Cria thread do servidor para aceitar conexões simultâneas
    thread_servidor = threading.Thread(target=aceitar_conexoes, args=(servidor, clock, lista_vizinhos, diretorio_compartilhado))
    thread_servidor.daemon = True
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
    if len(sys.argv) != 4:
        print("Uso: python <nome_do_arquivo>.py <endereco>:<porta> <vizinhos.txt> <diretorio_compartilhado>")
        sys.exit(1)

    endereco_porta = sys.argv[1]
    arquivo_vizinhos = sys.argv[2]
    diretorio_compartilhado = sys.argv[3]

    # Verificações básicas
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

    # Lê vizinhos do arquivo
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

# INTERFACE do menu

def exibir_menu(lista_vizinhos, endereco_porta, clock, diretorio_compartilhado, servidor):
    while True:
        print("\nEscolha um comando:")
        print("[1] Listar peers")
        print("[2] Obter peers")
        print("[3] Listar arquivos locais")
        print("[4] Buscar arquivos")
        print("[9] Sair")
        comando = input("> ")

        if comando == "1":
            listar_peers(lista_vizinhos, endereco_porta, clock)
        elif comando == "2":
            obter_peers(lista_vizinhos, endereco_porta, clock)
        elif comando == "3":
            listar_arquivos(diretorio_compartilhado)
        elif comando == "4":
            buscar_arquivos(lista_vizinhos, endereco_porta, clock)
        elif comando == "9":
            sair(lista_vizinhos, endereco_porta, clock, servidor)
        else:
            print("Comando inválido. Tente novamente.")

# ENTRADA principal 

if __name__ == "__main__":
    endereco_porta, lista_vizinhos, diretorio_compartilhado = inicializar_programa()
    clock = Clock()
    servidor = configurar_socket(endereco_porta)
    iniciar_servidor(servidor, clock, lista_vizinhos, diretorio_compartilhado)
    exibir_menu(lista_vizinhos, endereco_porta, clock, diretorio_compartilhado, servidor)
