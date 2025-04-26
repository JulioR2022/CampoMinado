from itertools import combinations
from collections import deque
import subprocess
import sys
import signal

class TimeoutError(Exception):
    pass

def timeout_handler(signum, frame):
    raise TimeoutError()  

signal.signal(signal.SIGALRM, timeout_handler)
signal.alarm(10)  # Define o tempo limite de 10 segundos
#signal.setitimer(signal.ITIMER_REAL, 9.9)

def getVariaveis(dx, dy, limite):
    """" Dado uma posição x e y retorna a variável associada à aquela posição"""
    return dx * limite + dy + 1
   
def adjacentes(dx, dy, limite):
    """" Dado uma posição x e y retorna as variáveis adjacentes à aquela posição"""
    adj = []
    direcoes = [(-1,  0), (1,  0), (0, -1), (0,  1),  # Esquerda, Direita, Baixo, Cima
                (-1, -1), (-1, 1), (1, -1), (1, 1)]   # Diagonais

    for ddx, ddy in direcoes:
        nx, ny = dx + ddx, dy + ddy
        if 0 <= nx < limite and 0 <= ny < limite:
            newAdj = getVariaveis(nx,ny,limite)
            adj.append(newAdj)
    
    return adj

def clausula_U(combinacoes, caminho):
    """"(-A V -B V -C V -D V ...)"""
    qtd_clausulas = 0
    clausula = ""
    for conj in combinacoes:
        for elemento in conj:
            clausula += f"{-elemento} "
        clausula += "0\n"
        qtd_clausulas += 1
    with open(caminho, 'a') as file:
        file.write(clausula)
    return qtd_clausulas

def clausula_L(combinacoes, caminho):
    """"(A V B...)"""
    qtd_clausulas = 0
    clausula = ""
    for conj in combinacoes:
        for elemento in conj:
            clausula += f"{elemento} "
        clausula += "0\n"
        qtd_clausulas+= 1
    with open(caminho, 'a') as file:
        file.write(clausula)
    return qtd_clausulas

# L = n -> n-k+1
# U = n -> k+1
def gera_clausulas(caminho, k, n, adj):
    """"Gera as clausulas U e L em CNF"""
        
    # Gerar a clausula U
    comb_U = combinations(adj, k+1)
    x = clausula_U(comb_U, caminho)
    
    # Gerar a clausula L
    comb_L = combinations(adj, n-k+1)
    y = clausula_L(comb_L, caminho)
    return x+y

def pergunta(elemento, regras, qtd_variaveis, qtd_clausulas):
    """"Adiciona o elemento de forma negada no arquivo e roda o clasp"""

    pergunta = f"{regras}_pergunta"  
    with open(pergunta, 'w') as file:
        file.write(f'p cnf {qtd_variaveis} {qtd_clausulas + 1}\n')
    
    with open(regras, 'r') as origem, open(pergunta, 'a') as destino:
        for linha in origem:
            destino.write(linha)
        destino.write(f'{-elemento} 0\n')

    resposta = subprocess.run(['clasp','--quiet', pergunta],text=True, stdout=subprocess.PIPE, stderr = subprocess.DEVNULL)
    return resposta

# Começo da execução do algoritmo --------------------------------------      
def main():
    regras = "/tmp/regras_JRGD"
    escrever_arquivo = ""
    # Limpa o arquivo antes de começar a escrever novas regras
    open(regras, 'w').close()

    # Leitura da entrada padrão
    tam = int (input())
    qtd_bomba = int (input())

    qtd_variaveis = tam * tam
    fila = deque()
    visitados = [ False for _ in range(qtd_variaveis + 1)]
    continua_jogando = 1
    variaveis = {}
    contador = 1
    qtd_clausulas = 0
    qtd_visitados = 0

    # Constroi as váriaveis
    for i in range(tam):
        for j in range(tam):
            variaveis[contador] = (i,j)
            contador+= 1

    # Laço principal
    while continua_jogando:
        if(qtd_bomba == 0):
            raise TimeoutError

        qtd_pos_in = int (input())
        if qtd_pos_in == 0:
            raise TimeoutError

        ja_esta_na_fila = set()
        marca_celulas = [] # Posicoes que sabemos o conteudo
        entrada = []

        # Le todas as variaveis recebidas, salva na entrada e marca como visitadas
        for i in range(qtd_pos_in):
            dx,dy,k = map(int, input().split())
            var = getVariaveis(dx, dy, tam)
            entrada.append([dx,dy,k,var])
            if(not visitados[var]):
                visitados[var] = True
                qtd_visitados += 1
                escrever_arquivo += f"-{var} 0\n"
                qtd_clausulas += 1


        with open(regras, 'a') as file:
            file.write(escrever_arquivo)
            escrever_arquivo = ""

        # Dado uma posicao geramos as clasulas referente as posicoes adjacentes
        for posicao in entrada:
            dx,dy,k = posicao[0],posicao[1],posicao[2]
            adj = adjacentes(dx,dy,tam)
            duvidas = []
            if k==0:
                for elemento in adj:
                    if(visitados[elemento]):
                        continue
                    visitados[elemento] = True
                    qtd_visitados += 1
                    escrever_arquivo += f'-{elemento} 0\n'
                    qtd_clausulas += 1
                    marca_celulas.append([variaveis[elemento][0], 
                        variaveis[elemento][1],'A'])
            else:
                for elemento in adj:
                    if (not visitados[elemento]) and ( elemento not in ja_esta_na_fila):
                        fila.append(elemento)
                        ja_esta_na_fila.add(elemento)
                n = len(adj)
                qtd_clausulas += gera_clausulas(regras, k, n, adj)
        
        with open(regras, 'a') as file:
            file.write(escrever_arquivo)
            escrever_arquivo = ""
        # Faz as perguntas para tomar as decisões
        qtd_clausulas_temp = 0
        while fila:    
            elemento = fila.popleft()

            nao_tem_bomba = pergunta(-elemento,regras,qtd_variaveis, qtd_clausulas)
            # Returncode == 20 é unsat
            if nao_tem_bomba.returncode == 20:
                    escrever_arquivo += f'{-elemento} 0\n'
                    visitados[elemento] = True
                    qtd_visitados += 1
                    qtd_clausulas_temp += 1
                    marca_celulas.append([variaveis[elemento][0], 
                        variaveis[elemento][1],'A'])
            else:
                tem_bomba = pergunta(elemento,regras,qtd_variaveis, qtd_clausulas)
                if tem_bomba.returncode == 20:
                    escrever_arquivo += f'{elemento} 0\n'
                    qtd_clausulas_temp += 1
                    visitados[elemento] = True
                    qtd_visitados += 1
                    marca_celulas.append([variaveis[elemento][0], 
                        variaveis[elemento][1],'B'])
                    
                    qtd_bomba -= 1

        tam_marca_celulas = len(marca_celulas)

        if(tam_marca_celulas == 0):
            raise TimeoutError
            
        print(tam_marca_celulas)
        for celula in marca_celulas:
            print(f"{celula[0]} {celula[1]} {celula[2]}")
            
        
        with open(regras, 'a') as file:
            file.write(escrever_arquivo)
            qtd_clausulas += qtd_clausulas_temp
            escrever_arquivo = ""
            
        marca_celulas = []

try:
    main()
except TimeoutError:
    print(0)
    sys.exit(0)
finally:
    signal.alarm(0)