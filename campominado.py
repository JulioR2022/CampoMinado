from itertools import combinations
from collections import deque
import subprocess

def getVariaveis(dx, dy, limite):
    return dx * limite + dy + 1
   
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
    """"-A V -B V -C V -D V ..."""
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

regras = "/tmp/regras_JRGD"
# Limpa o arquivo antes de começar a escrever novas regras
open(regras, 'w').close()
tam = int (input())
qtd_bomba = int (input())
fila = deque()
visitados = [ False for _ in range(tam * tam + 1)]
continua_jogando = 1
variaveis = {}
contador = 1
qtd_clausulas = 0

# Constroi as váriaveis
for i in range(tam):
    for j in range(tam):
        variaveis[contador] = (i,j)
        contador+= 1

while continua_jogando:
    qtd_pos_in = int (input())
    ja_esta_na_fila = set()
    marca_celulas = [] # Posicoes que sabemos o conteudo
    continua_jogando = 0
    entrada = []

    # Le todas as variaveis recebidas, salva na entrada e marca como visitadas
    for i in range(qtd_pos_in):
        dx,dy,k = map(int, input().split())
        var = getVariaveis(dx, dy, tam)
        entrada.append([dx,dy,k,var])
        visitados[var] = True
        with open(regras, 'a') as file:
            file.write(f"-{var} 0\n")
            qtd_clausulas+= 1

    # Dado uma posicao geramos as clasulas referente as posicoes adjacentes
    for posicao in entrada:
        dx,dy,k = posicao[0],posicao[1],posicao[2]
        adj = adjacentes(dx,dy,tam)
    
        if k==0:
            with open(regras, 'a') as file:
                for elemento in adj:
                    if(visitados[elemento]):
                        continue
                    visitados[elemento] = True
                    file.write(f"{-elemento} 0\n")
                    qtd_clausulas+=1
                    marca_celulas.append([variaveis[elemento][0], 
                        variaveis[elemento][1],'A'])
                    print("Marcou?")
                continua_jogando = 1
        else:
            for elemento in adj:
                if (not visitados[elemento]) and ( elemento not in ja_esta_na_fila):
                    fila.append(elemento)
                    ja_esta_na_fila.add(elemento)
            n = len(adj)
            qtd_clausulas += gera_clausulas(regras, k, n, adj)
        
    while fila:
        elemento = fila.popleft()
        tem_bomba = pergunta(elemento,regras,tam * tam, qtd_clausulas)

        # Returncode == 20 é unsat
        if tem_bomba.returncode == 20:
            continua_jogando = 1
            with open(regras, 'a') as file:
                file.write(f'{elemento} 0\n')
            visitados[elemento] = True
            marca_celulas.append([variaveis[elemento][0], 
                variaveis[elemento][1],'B'])
            # if(qtd_bomba != -1):
            #     qtd_bomba -= 1
            #     if qtd_bomba == 0:
            #         continua_jogando = 0
            #         break
            
        nao_tem_bomba = pergunta(-elemento,regras,tam * tam, qtd_clausulas)
        if nao_tem_bomba.returncode == 20:
            continua_jogando = 1
            with open(regras, 'a') as file:
                file.write(f'{-elemento} 0\n')
            visitados[elemento] = True
            marca_celulas.append([variaveis[elemento][0], 
                variaveis[elemento][1],'A'])
            
    # termina_campo = True if continua_jogando == 0 else False
    if(not continua_jogando):
        print(0)
    else:
        print(len(marca_celulas))
        for celula in marca_celulas:
            print(f"{celula[0]} {celula[1]} {celula[2]}")        
        
        marca_celulas = []

# Criar a condicao de parada
