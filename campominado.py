from itertools import combinations
from collections import deque
import subprocess
import shutil
import os

def getVariaveis(dx, dy, variaveis):
    var = 0
    for key, value in variaveis.items():
        if value == f'{dx}{dy}':
            var = int(key)
            return var
    return var

def adjacentes(dx, dy, limite):
    adj = []
    direcoes = [(-1,  0), (1,  0), (0, -1), (0,  1),  # Esquerda, Direita, Baixo, Cima
                (-1, -1), (-1, 1), (1, -1), (1, 1)]   # Diagonais

    for ddx, ddy in direcoes:
        nx, ny = dx + ddx, dy + ddy
        if 0 <= nx < limite and 0 <= ny < limite:
            adj.append(nx * limite + ny + 1)
    
    return adj

def clausula_U(combinacoes, caminho):
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
        
    # Gerar a clausula U
    comb_U = combinations(adj, k+1)
    x = clausula_U(comb_U, caminho)
    
    # Gerar a clausula L
    comb_L = combinations(adj, n-k+1)
    y = clausula_L(comb_L, caminho)
    return x+y

def pergunta(elemento, regras, qtd_variaveis, qtd_clausulas):
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
tam = int (input())
qtd_clausulas = 0
regras = "/tmp/regras_JRGD"

# Limpa o arquivo antes de começar a escrever novas regras
open(regras, 'w').close()

visitados = [ False for _ in range(tam * tam + 1)]
variaveis = {}
contador = 1
for i in range(tam):
    for j in range(tam):
        variaveis[contador] = f'{i}{j}'
        contador+= 1

qtd_bomba = int (input())
qtd_pos_in = int (input())

fila = deque()

for i in range(qtd_pos_in):
    dx,dy,k = map(int, input().split())
    var = getVariaveis(dx, dy, variaveis)
    visitados[var] = True
    with open(regras, 'a') as file:
        file.write(f"-{var} 0\n")
        qtd_clausulas+= 1
   
    adj = adjacentes(dx,dy,tam)
    # print(f"Posicao {dx, dy} adjacentes:")
    # for j in adj:
    #     print(f"{j} ")
        
    if k==0:
        with open(regras, 'a') as file:
            for elemento in adj:
                visitados[elemento] = True
                file.write(f"{-elemento} 0\n")
                qtd_clausulas+=1
    else:
        for elemento in adj:
            if (not visitados[elemento]) and (not elemento in fila) :
                fila.append(elemento)
        n = len(adj)
        qtd_clausulas += gera_clausulas(regras, k, n, adj)
    
while fila:
    elemento = fila.popleft()
    print(f"Tal elemento tem bomba ? {elemento}")
    resposta1 = pergunta(elemento,regras,tam * tam, qtd_clausulas)
    print(f"resposta deu isso aqui {resposta1}")
    print(f"Tal elemento nao tem bomba ? {elemento}")
    resposta2 = pergunta(-elemento,regras,tam * tam, qtd_clausulas)
    print(f"resposta deu isso aqui {resposta2}")


    # CompletedProcess(args=['clasp', '/tmp/regras_JRGD_pergunta'], returncode=20)
    # if resposta1.returncode == 20:
    #     with open(regras, 'a') as file:
    #         file.write(f'{elemento} 0\n')
    
    # if resposta2.returncode == 20:
    #     with open(regras, 'a') as file:
    #         file.write(f'{-elemento} 0\n')
    
# Criar a condicao de parada
# Criar a fila
# Fazer as perguntas para tomar decisoes