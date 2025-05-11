import sys
import os

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
        self.endereco = endereco  # Endereço do peer
        self.porta = porta        # Porta do peer
        self.estado = "OFFLINE"   # Estado inicial do peer

    def atualizar_estado(self, novo_estado):
        """Atualiza o estado do peer (ONLINE ou OFFLINE)"""
        self.estado = novo_estado
        print(f"Atualizando peer {self.endereco}:{self.porta} status {novo_estado}")

# Classe Mensagem para gerenciar a criação e análise de mensagens
class Mensagem:
    def __init__(self, origem, clock, tipo, argumentos=None):
        self.origem = origem          # Identificação do peer remetente (endereço:porta)
        self.clock = clock            # Valor do relógio local
        self.tipo = tipo              # Tipo da mensagem (HELLO, GET_PEERS, etc.)
        self.argumentos = argumentos or []  # Lista de argumentos adicionais

    def construir_mensagem(self):
        """Constrói a mensagem em formato string para ser enviada"""
        mensagem = f"{self.origem} {self.clock} {self.tipo}"  # Cabeçalho da mensagem
        if self.argumentos:
            mensagem += " " + " ".join(self.argumentos)  # Adiciona argumentos, se existirem
        mensagem += "\n"  # Finaliza a mensagem com nova linha
        return mensagem

    @staticmethod
    def analisar_mensagem(mensagem_str):
        """Analisa uma mensagem recebida e retorna uma instância da classe Mensagem"""
        partes = mensagem_str.strip().split(" ")
        origem = partes[0]            # Origem da mensagem (endereço:porta)
        clock = int(partes[1])        # Valor do relógio
        tipo = partes[2]              # Tipo da mensagem
        argumentos = partes[3:]       # Argumentos adicionais
        return Mensagem(origem, clock, tipo, argumentos)

    def exibir_mensagem(self):
        """Exibe a mensagem formatada para depuração ou apresentação"""
        print(f"Mensagem formatada: {self.construir_mensagem().strip()}")

def inicializar_programa():
    # Verifica se os argumentos foram fornecidos corretamente
    if len(sys.argv) != 4:
        print("Uso: python <nome_do_arquivo>.py <endereco>:<porta> <vizinhos.txt> <diretorio_compartilhado>")
        sys.exit(1)

    # Lê os argumentos da linha de comando
    endereco_porta = sys.argv[1]
    arquivo_vizinhos = sys.argv[2]
    diretorio_compartilhado = sys.argv[3]

    # Valida o formato do endereço:porta
    if ":" not in endereco_porta or not endereco_porta.split(":")[1].isdigit():
        print("Erro: Formato inválido de endereço:porta. Deve ser no formato <endereco>:<porta>.")
        sys.exit(1)

    # Verifica se o arquivo de vizinhos existe
    if not os.path.isfile(arquivo_vizinhos):
        print(f"Erro: Arquivo de vizinhos '{arquivo_vizinhos}' não encontrado.")
        sys.exit(1)

    # Verifica se o diretório compartilhado existe
    if not os.path.isdir(diretorio_compartilhado):
        print(f"Erro: Diretório compartilhado '{diretorio_compartilhado}' não encontrado ou inválido.")
        sys.exit(1)

    print("Parâmetros de inicialização lidos com sucesso!")
    print(f"Endereço e Porta: {endereco_porta}")
    print(f"Arquivo de Vizinhos: {arquivo_vizinhos}")
    print(f"Diretório Compartilhado: {diretorio_compartilhado}")

    # Lê o arquivo de vizinhos e inicializa a lista de peers
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

# Inicia o programa
if __name__ == "__main__":
    endereco_porta, lista_vizinhos, diretorio_compartilhado = inicializar_programa()