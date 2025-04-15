from itertools import combinations
from queue import Queue
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

def adjacentes(var, dx, dy, variaveis, limite):
    adj = []
    baixo = True if dy - 1 >= 0 else False 
    cima = True if dy + 1 < limite else False

    if dx - 1 >= 0:
        adj.append(var -1) # Esquerda
        if cima:
            adj.append(var - 1 + limite) # Superior esquerda
        if baixo:
            adj.append(var - 1 - limite) # Inferior esquerda

    if dx + 1 < limite:
        adj.append(var +1) # Direita
        if cima:
            adj.append(var + 1 + limite) # Superior direita
        if baixo:
            adj.append(var + 1 - limite ) # Inferior direita
            
    if baixo:
        adj.append(var - limite) # Baixo
       
    if cima:
        adj.append(var + limite) # Cima
    
    return adj

def clausula_U(combinacoes, caminho):
    verifica = ""
    for conj in combinacoes:
        for elemento in conj:
            verifica += "-{elemento} "
        verifica += "0\n"
        with open(caminho, 'a') as file:
            file.write(verifica)
        verifica=""

def clausula_L(combinacoes, caminho):
    verifica = ""
    for conj in combinacoes:
        for elemento in conj:
            verifica += "{elemento} "
        verifica += "0\n"
        with open(caminho, 'a') as file:
            file.write(verifica)
        verifica=""

# U = n -> k+1
# L = n -> n-k+1
def gera_clausulas(caminho, k, n, adj):
        
    # Gerar a clausula U
    comb_U = combinations(adj, k+1)
    clausula_U(comb_U, caminho)
    
    # Gerar a clausula L
    comb_L = combinations(adj, n-k+1)
    clausula_U(comb_L, caminho)

def pergunta(elemento, caminho):
    pergunta = f"{caminho}_pergunta"  # ou escolha outro nome, se quiser
    shutil.copy(caminho, pergunta)
    with open(pergunta, 'a') as file:
        file.write('-{elemento} 0\n')
        

# def executar_clasp(caminho_arquivo_cnf):
#     try:
#         resultado = subprocess.run(
#             ['clasp', caminho_arquivo_cnf],
#             stdout=subprocess.PIPE,
#             stderr=subprocess.PIPE,
#             text=True
#         )

#         print("Saída do clasp:")
#         print(resultado.stdout)

#         if "UNSATISFIABLE" in resultado.stdout:
#             return "UNSAT"
#         elif "SATISFIABLE" in resultado.stdout:
#             return "SAT"
#         else:
#             return "INDETERMINADO"
#     except FileNotFoundError:
#         print("Erro: o comando 'clasp' não foi encontrado. Verifique se está instalado e no PATH.")
#         return None

# Começo da execução do arquivo --------------------------------------      
tam = int (input())

# 0 - nao visitado; 1 - visitado
visitados = {}
variaveis = {}
contador = 0
for i in range(tam):
    for j in range(tam):
        variaveis[contador] = f'{i}{j}'

qtd_bomba = int (input())
qtd_pos_in = int (input())

fila = Queue()
for i in range(qtd_pos_in):
    dx,dy,k = map(int, input().split())
    var = getVariaveis(dx, dy, variaveis)
    visitados[var] = 1
    with open("/tmp/regras_JRGD", 'a') as file:
        file.write(f"-{var} 0\n")
    if k==0:
        adj = adjacentes(dx,dy,variaveis,tam)
        with open("/tmp/regras_JRGD", 'a') as file:
            for elemento in adj:
                visitados[elemento] = 1
                file.write(f"-{elemento} 0\n")
    else:
        adj = adjacentes(var,dx,dy,variaveis,tam)
        for elemento in adj:
            if not visitados[elemento]:
                fila.put(elemento)
        n = len(adj)
        gera_clausulas("/tmp/regras_JRGD", k, n, adj)
    
    while not fila.empty():
        elemento = fila.get()
        pergunta(elemento,"/tmp/regras_JRGD")



# Criar a condicao de parada
# Criar a fila
# Fazer as perguntas para tomar decisoes