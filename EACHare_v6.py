import sys
import os

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

def inicializar_programa():
    # Verifica se os argumentos foram fornecidos corretamente
    if len(sys.argv) != 4:  # Espera-se 3 argumentos além do nome do script
        print("Uso: python <nome_do_arquivo>.py <endereco>:<porta> <vizinhos.txt> <diretorio_compartilhado>")
        sys.exit(1)  # Encerra o programa se os argumentos estiverem incorretos

    # Lê os argumentos da linha de comando
    endereco_porta = sys.argv[1]  # Primeiro argumento: endereço e porta do peer
    arquivo_vizinhos = sys.argv[2]  # Segundo argumento: nome do arquivo de vizinhos
    diretorio_compartilhado = sys.argv[3]  # Terceiro argumento: diretório de arquivos compartilhados

    # Valida o formato do endereço:porta
    if ":" not in endereco_porta or not endereco_porta.split(":")[1].isdigit():
        print("Erro: Formato inválido de endereço:porta. Deve ser no formato <endereco>:<porta>.")  # Mensagem de erro
        sys.exit(1)

    # Verifica se o arquivo de vizinhos existe no sistema
    if not os.path.isfile(arquivo_vizinhos):
        print(f"Erro: Arquivo de vizinhos '{arquivo_vizinhos}' não encontrado.")  # Mensagem de erro
        sys.exit(1)

    # Verifica se o diretório compartilhado existe e é válido
    if not os.path.isdir(diretorio_compartilhado):
        print(f"Erro: Diretório compartilhado '{diretorio_compartilhado}' não encontrado ou inválido.")  # Mensagem de erro
        sys.exit(1)

    # Confirma que todos os parâmetros foram lidos com sucesso
    print("Parâmetros de inicialização lidos com sucesso!")
    print(f"Endereço e Porta: {endereco_porta}")
    print(f"Arquivo de Vizinhos: {arquivo_vizinhos}")
    print(f"Diretório Compartilhado: {diretorio_compartilhado}")

    # Lê o arquivo de vizinhos e inicializa a lista de peers
    lista_vizinhos = []  # Lista que armazenará os vizinhos conhecidos
    with open(arquivo_vizinhos, "r") as arquivo:
        for linha in arquivo:  # Itera por cada linha do arquivo
            linha = linha.strip()  # Remove espaços e quebras de linha
            if linha:  # Ignora linhas vazias
                endereco_peer, porta_peer = linha.split(":")  # Separa endereço e porta
                peer = Peer(endereco_peer, int(porta_peer))  # Cria instância da classe Peer
                lista_vizinhos.append(peer)  # Adiciona o peer à lista
                print(f"Adicionando novo peer {linha} status {peer.estado}")  # Log de adição do peer

    # Confirma que a lista de peers foi inicializada
    print("Lista de peers inicializada com sucesso!")

    return endereco_porta, lista_vizinhos, diretorio_compartilhado

# Inicia o programa
if __name__ == "__main__":
    # Chama a função de inicialização e armazena os valores retornados
    endereco_porta, lista_vizinhos, diretorio_compartilhado = inicializar_programa()