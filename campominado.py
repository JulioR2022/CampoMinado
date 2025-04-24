from itertools import combinations
from collections import deque
import subprocess

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
    for conj in combinacoes:
        clausula = ""
        for elemento in conj:
            clausula += f"{-elemento} "
        clausula += "0\n"
        with open(caminho, 'a') as file:
            file.write(clausula)
            qtd_clausulas+= 1
    return qtd_clausulas

def clausula_L(combinacoes, caminho):
    """"(A V B...)"""
    
    qtd_clausulas = 0
    for conj in combinacoes:
        clausula = ""
        for elemento in conj:
            clausula += f"{elemento} "
        clausula += "0\n"
        with open(caminho, 'a') as file:
            file.write(clausula)
            qtd_clausulas+= 1
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

    resposta = subprocess.run(['clasp', pergunta],text=True)
    return resposta

# Começo da execução do algoritmo --------------------------------------      

regras = "/tmp/regras_JRGD"

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
    qtd_pos_in = int (input())
    if qtd_pos_in == 0:
        continua_jogando = 0
        print(0)
        continue

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
            with open(regras, 'a') as file:
                file.write(f"-{var} 0\n")
                qtd_clausulas+= 1
    
    if(qtd_visitados == qtd_variaveis):
        print(0)
        continua_jogando = 0
        continue

    # Dado uma posicao geramos as clasulas referente as posicoes adjacentes
    for posicao in entrada:
        continua_jogando = 0
        dx,dy,k = posicao[0],posicao[1],posicao[2]
        adj = adjacentes(dx,dy,tam)
    
        if k==0:
            for elemento in adj:
                if(visitados[elemento]):
                    continue
                visitados[elemento] = True
                qtd_visitados += 1
                with open(regras, 'a') as file:
                    file.write(f"{-elemento} 0\n")
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
    
    # Faz as perguntas para tomar as decisões
    while fila:
        elemento = fila.popleft()
        tem_bomba = pergunta(elemento,regras,qtd_variaveis, qtd_clausulas)
        # Returncode == 20 é unsat
        if tem_bomba.returncode == 20:
            with open(regras, 'a') as file:
                file.write(f'{elemento} 0\n')
            visitados[elemento] = True
            qtd_visitados += 1
            marca_celulas.append([variaveis[elemento][0], 
                variaveis[elemento][1],'B'])
            
            qtd_bomba -= 1
            if qtd_bomba == 0:    
                break
            
        nao_tem_bomba = pergunta(-elemento,regras,qtd_variaveis, qtd_clausulas)
        if nao_tem_bomba.returncode == 20:
            with open(regras, 'a') as file:
                file.write(f'{-elemento} 0\n')
            visitados[elemento] = True
            qtd_visitados += 1
            marca_celulas.append([variaveis[elemento][0], 
                variaveis[elemento][1],'A'])
    
    tam_marca_celulas = len(marca_celulas)

    if(tam_marca_celulas == 0):
        continua_jogando = 0
        print(0)
        continue   

    print(tam_marca_celulas)
    for celula in marca_celulas:
        print(f"{celula[0]} {celula[1]} {celula[2]}")
        
    
    if qtd_bomba == 0:
        for elemento in adj:
            if not visitados[elemento]:
                print(f"{variaveis[elemento][0]} {variaveis[elemento][1]} A")
                visitados[elemento] = True
                qtd_visitados += 1
        continua_jogando = 0
    
        
    marca_celulas = []


