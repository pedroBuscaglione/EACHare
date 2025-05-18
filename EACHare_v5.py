#######################################################################
# Discentes: Mariana Borges Araujo da Silva - 14596342                #
#            Pedro Serrano Buscaglione - 14603652                     #
# Docente: Prof Dr. Renan Cerqueira Afonso Alves                      #
# Disciplina: Desenvolvimento de Sistemas de Informações Distribuídos #
# Turma 094                                                           #
#######################################################################

import sys
import os
import socket
import threading
import base64
import time

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
        self.relogio = 0
        self.ultimo_hello = time.time()

    def atualizar_estado(self, novo_estado):
        self.estado = novo_estado
        if novo_estado == "ONLINE":
            self.ultimo_hello = time.time()
        print(f"Atualizando peer {self.endereco}:{self.porta} status {novo_estado}")

    def atualizar_relogio(self, valor):
        if valor > self.relogio:
            self.relogio = valor

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
            raise ValueError("Mensagem inválida")
        origem = partes[0]
        clock = int(partes[1])
        tipo = partes[2]
        argumentos = partes[3:]
        return Mensagem(origem, clock, tipo, argumentos)

def enviar_hello(peer, endereco_porta, clock):
    clock.incrementar()
    mensagem = Mensagem(endereco_porta, clock.valor, "HELLO").construir_mensagem()
    print(f"Encaminhando mensagem '{mensagem.strip()}' para {peer.endereco}:{peer.porta}")
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as cliente:
            cliente.settimeout(5)
            cliente.connect((peer.endereco, peer.porta))
            cliente.sendall(mensagem.encode())
            print("=> Mensagem enviada com sucesso!")
            peer.atualizar_estado("ONLINE")
    except (socket.timeout, ConnectionRefusedError, OSError) as e:
        print(f"Erro ao conectar com o peer {peer.endereco}:{peer.porta}: {e}")
        peer.atualizar_estado("OFFLINE")

def obter_peers(lista_vizinhos, endereco_porta, clock):
    for peer in lista_vizinhos:
        clock.incrementar()
        mensagem = Mensagem(endereco_porta, clock.valor, "GET_PEERS").construir_mensagem()
        print(f"Encaminhando mensagem '{mensagem.strip()}' para {peer.endereco}:{peer.porta}")
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as cliente:
                cliente.settimeout(5)
                cliente.connect((peer.endereco, peer.porta))
                cliente.sendall(mensagem.encode())
                resposta = cliente.recv(8192).decode()
                resposta_msg = Mensagem.analisar_mensagem(resposta)
                clock.atualizar(resposta_msg.clock)
                peer.atualizar_estado("ONLINE")
                peer.atualizar_relogio(resposta_msg.clock)
                if resposta_msg.tipo == "PEER_LIST":
                    for peer_info in resposta_msg.argumentos[1:]:
                        endereco, porta, estado, relogio = peer_info.split(":")
                        porta = int(porta)
                        relogio = int(relogio)
                        existente = next((p for p in lista_vizinhos if p.endereco == endereco and p.porta == porta), None)
                        if existente:
                            if relogio > existente.relogio:
                                existente.atualizar_estado(estado)
                                existente.atualizar_relogio(relogio)
                        else:
                            novo = Peer(endereco, porta)
                            novo.atualizar_estado(estado)
                            novo.atualizar_relogio(relogio)
                            lista_vizinhos.append(novo)
        except (socket.timeout, ConnectionRefusedError, OSError) as e:
            print(f"Falha ao contatar {peer.endereco}:{peer.porta}: {e}")
            peer.atualizar_estado("OFFLINE")

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
            with open(os.path.join("compartilhado", nome), "wb") as f:
                f.write(base64.b64decode(conteudo_base64))
            print(f"Download do arquivo {nome} finalizado.")
    except Exception as e:
        print(f"Erro no download: {e}")

def processar_conexao(conexao, endereco, clock, lista_vizinhos, diretorio_compartilhado):
    dados = conexao.recv(4096).decode()
    if not dados:
        return
    mensagem = Mensagem.analisar_mensagem(dados)
    clock.atualizar(mensagem.clock)
    print(f"Mensagem recebida: {dados.strip()}")

    origem = mensagem.origem
    tipo = mensagem.tipo
    endereco_remetente, porta_remetente = origem.split(":")
    porta_remetente = int(porta_remetente)
    peer_existente = next((p for p in lista_vizinhos if p.endereco == endereco_remetente and p.porta == porta_remetente), None)
    if not peer_existente:
        peer_existente = Peer(endereco_remetente, porta_remetente)
        lista_vizinhos.append(peer_existente)

    peer_existente.atualizar_estado("ONLINE")
    peer_existente.atualizar_relogio(mensagem.clock)

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
            [str(len(lista_vizinhos))] + [f"{p.endereco}:{p.porta}:{p.estado}:{p.relogio}" for p in lista_vizinhos]
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


def configurar_socket(endereco_porta):
    endereco, porta = endereco_porta.split(":")
    servidor = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    servidor.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    servidor.bind((endereco, int(porta)))
    servidor.listen()
    print(f"Peer escutando em {endereco}:{porta}")
    return servidor

def aceitar_conexoes(servidor, clock, lista_vizinhos, diretorio):
    while True:
        conexao, endereco = servidor.accept()
        threading.Thread(target=processar_conexao, args=(conexao, endereco, clock, lista_vizinhos, diretorio)).start()

def inicializar_vizinhos(arquivo_vizinhos):
    lista = []
    with open(arquivo_vizinhos, "r") as f:
        for linha in f:
            if linha.strip():
                endereco, porta = linha.strip().split(":")
                peer = Peer(endereco, int(porta))
                print(f"Adicionando novo peer {endereco}:{porta} status {peer.estado}")
                lista.append(peer)
    return lista

def menu(lista_vizinhos, endereco_porta, clock, diretorio, servidor):
    while True:
        print("\nEscolha um comando:")
        print("[1] Listar peers")
        print("[2] Obter peers")
        print("[3] Listar arquivos locais")
        print("[4] Buscar arquivos")
        print("[9] Sair")
        escolha = input("> ")

        if escolha == "1":
            for i, p in enumerate(lista_vizinhos, 1):
                print(f"[{i}] {p.endereco}:{p.porta} {p.estado}")
            opt = input("Escolha um peer para enviar HELLO ou 0 para voltar: ")
            if opt.isdigit() and 0 < int(opt) <= len(lista_vizinhos):
                enviar_hello(lista_vizinhos[int(opt)-1], endereco_porta, clock)
        elif escolha == "2":
            obter_peers(lista_vizinhos, endereco_porta, clock)
        elif escolha == "3":
            listar_arquivos(diretorio)
        elif escolha == "4":
            buscar_arquivos(lista_vizinhos, endereco_porta, clock)
        elif escolha == "9":
            for peer in lista_vizinhos:
                if peer.estado == "ONLINE":
                    clock.incrementar()
                    mensagem = Mensagem(endereco_porta, clock.valor, "BYE").construir_mensagem()
                    print(f"Encaminhando mensagem \"{mensagem.strip()}\" para {peer.endereco}:{peer.porta}")
                    try:
                        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as cliente:
                            cliente.settimeout(5)
                            cliente.connect((peer.endereco, peer.porta))
                            cliente.sendall(mensagem.encode())
                    except:
                        pass
            servidor.close()
            print("Encerrando peer.")
            sys.exit(0)
        else:
            print("Comando inválido.")

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Uso: python <script>.py <endereco:porta> <arquivo_vizinhos.txt> <diretorio_compartilhado>")
        sys.exit(1)

    endereco_porta = sys.argv[1]
    vizinhos_path = sys.argv[2]
    diretorio = sys.argv[3]

    if not os.path.isdir(diretorio):
        print("Erro: diretório inválido.")
        sys.exit(1)

    clock = Clock()
    lista_vizinhos = inicializar_vizinhos(vizinhos_path)
    servidor = configurar_socket(endereco_porta)
    threading.Thread(target=aceitar_conexoes, args=(servidor, clock, lista_vizinhos, diretorio), daemon=True).start()
    menu(lista_vizinhos, endereco_porta, clock, diretorio, servidor)
