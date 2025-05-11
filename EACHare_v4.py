import sys
import os

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

# Inicia o programa
if __name__ == "__main__":
    inicializar_programa()