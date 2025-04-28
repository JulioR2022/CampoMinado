from itertools import combinations
from collections import deque
import subprocess
import sys
import signal
from concurrent.futures import ThreadPoolExecutor

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

def clausula_U(combinacoes, contadores):
    """"(-A V -B V -C V -D V ...)"""
    clausula = ""
    for conj in combinacoes:
        for elemento in conj:
            clausula += f"{-elemento} "
        clausula += "0\n"
        contadores["qtd_clausulas"]+= 1
    return clausula

def clausula_L(combinacoes, contadores):
    """"(A V B...)"""
    clausula = ""
    for conj in combinacoes:
        for elemento in conj:
            clausula += f"{elemento} "
        clausula += "0\n"
        contadores["qtd_clausulas"]+= 1
    return clausula

# L = n -> n-k+1
# U = n -> k+1
def gera_clausulas(contadores, k, n, adj):
    """"Gera as clausulas U e L em CNF"""
    clausulas = ''
    # Gerar a clausula U
    comb_U = combinations(adj, k+1)
    clausulas += clausula_U(comb_U, contadores)
    
    # Gerar a clausula L
    comb_L = combinations(adj, n-k+1)
    clausulas += clausula_L(comb_L, contadores)
    return clausulas

def pergunta(elemento, escrever_arquivo, qtd_variaveis, qtd_clausulas):
    """"Adiciona o elemento de forma negada no arquivo e roda o clasp"""
    cnf = f'p cnf {qtd_variaveis} {qtd_clausulas + 1}\n'
    cnf += escrever_arquivo
    cnf += f'{-elemento} 0\n'
    resposta = subprocess.run(['clasp','--quiet'],input=cnf,text=True, timeout=1, stdout=subprocess.PIPE, stderr = subprocess.DEVNULL)
    return resposta

def handle_pergunta(elemento, escrever_arquivo, visitados, marca_celulas, variaveis, contadores, qtd_clausulas_antigas):
    novo = ""
    nao_tem_bomba = pergunta(-elemento, escrever_arquivo, contadores["qtd_variaveis"], qtd_clausulas_antigas)
   
    # Returncode == 20 é unsat
    if nao_tem_bomba.returncode == 20:
            novo += f'{-elemento} 0\n'
            visitados[elemento] = True
            contadores["qtd_visitados"] += 1
            contadores['qtd_clausulas'] += 1 
            marca_celulas.append([variaveis[elemento][0], 
                variaveis[elemento][1],'A'])
            return novo

    tem_bomba = pergunta(elemento, escrever_arquivo, contadores["qtd_variaveis"], qtd_clausulas_antigas)
    if tem_bomba.returncode == 20:
        novo += f'{elemento} 0\n'
        visitados[elemento] = True
        contadores["qtd_visitados"] += 1
        contadores['qtd_clausulas'] += 1 
        marca_celulas.append([variaveis[elemento][0], 
            variaveis[elemento][1],'B'])
        contadores["qtd_bomba"] -= 1
        return novo
    
    return novo

# Começo da execução do algoritmo --------------------------------------      
def main():
    escrever_arquivo = ""
    # Leitura da entrada padrão
    tam = int (input())
    qtd_bomba = int (input())

    contadores = {
        "qtd_clausulas" : 0,
        "qtd_visitados" : 0,
        "qtd_bomba" : qtd_bomba,
        "qtd_variaveis" : tam*tam
    }
    fila = deque()
    visitados = [ False for _ in range(contadores["qtd_variaveis"] + 1)]
    continua_jogando = 1
    variaveis = {}

    contador = 1
    # Constroi as váriaveis
    for i in range(tam):
        for j in range(tam):
            variaveis[contador] = (i,j)
            contador+= 1

    # Laço principal
    while continua_jogando:
        if(contadores["qtd_bomba"] == 0):
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
                contadores["qtd_visitados"] += 1
                contadores["qtd_clausulas"] += 1
                escrever_arquivo += f"-{var} 0\n"

        # Dado uma posicao geramos as clasulas referente as posicoes adjacentes
        for posicao in entrada:
            dx,dy,k = posicao[0],posicao[1],posicao[2]
            adj = adjacentes(dx,dy,tam)
            if k==0:
                for elemento in adj:
                    if(visitados[elemento]):
                        continue
                    visitados[elemento] = True
                    contadores["qtd_visitados"] += 1
                    contadores["qtd_clausulas"] += 1
                    escrever_arquivo += f'-{elemento} 0\n'
                    marca_celulas.append([variaveis[elemento][0], 
                        variaveis[elemento][1],'A'])
            else:
                for elemento in adj:
                    if (not visitados[elemento]) and ( elemento not in ja_esta_na_fila):
                        fila.append(elemento)
                        ja_esta_na_fila.add(elemento)
                n = len(adj)
                escrever_arquivo += gera_clausulas(
                    contadores, 
                    k, 
                    n, 
                    adj
                    )

        tasks = []
        qtd_clausulas_antigas = contadores["qtd_clausulas"]
        with ThreadPoolExecutor() as executor:
            # Faz as perguntas para tomar as decisões
            qtd_clausulas_temp = 0
            while fila:    
                elemento = fila.popleft()
                tasks.append(
                    executor.submit(
                        handle_pergunta,
                        elemento,
                        escrever_arquivo, 
                        visitados, 
                        marca_celulas, 
                        variaveis, 
                        contadores, 
                        qtd_clausulas_antigas
                    )
                )
        
        for task in tasks:
            escrever_arquivo += task.result()
           
        tam_marca_celulas = len(marca_celulas)

        if(tam_marca_celulas == 0):
            raise TimeoutError
            
        print(tam_marca_celulas)
        for celula in marca_celulas:
            print(f"{celula[0]} {celula[1]} {celula[2]}")
            
        marca_celulas = []

try:
    main()
except TimeoutError:
    print(0)
    sys.exit(0)
finally:
    signal.alarm(0)