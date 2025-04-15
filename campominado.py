from itertools import combinations
import queue

def getVariaveis(dx, dy, variaveis):
    var = 0
    for key, value in variaveis.items():
        if value == f'{dx}{dy}':
            var = int(key)
            return var
    return var

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

    
def adjacentes(dx, dy, variaveis, limite):
    var = getVariaveis(dx, dy, variaveis)
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
            adj.append(var + 1 + limites) # Superior direita
        if baixo:
            adj.append(var + 1 - limite ) # Inferior direita
            
    if baixo:
        adj.append(var - limite) # Baixo
       
    if cima:
        adj.append(var + limite) # Cima
    
    return adj


# U = n -> k+1
# L = n -> n-k+1
def gera_clausulas(caminho, k, n, adj):
        
    # Gerar a clausula U
    comb_U = combinations(adj, k+1)
    clausula_U(comb_u, caminho)
    
    # Gerar a clausula L
    comb_L = combinations(adj, n-k+1)
    clausula_U(comb_L, caminho)

# Começo da execução do arquivo      
campo_minado = int (input())
minas = {}
variaveis = {}
contador = 0
for i in range(campo_minado):
    for j in range(campo_minado):
        variaveis[contador] = f'{i}{j}'

qtd_bomba = int (input())
qtd_pos_in = int (input())

for i in range(qtd_pos_in):
    dx,dy,k = map(int, input().split())
    
    if k==0:
        var = getVariaveis(dx, dy, variaveis)
        adj = adjacentes(dx,dy,variaveis,campo_minado)
        with open("/tmp/regras_JRGD", 'a') as file:
            file.write(f"-{var} 0\n")
            for elemento in adj:
                file.write(f"-{elemento} 0\n")
    else:
        adj = adjacentes(dx,dy,variaveis,limite)
        n = len(adj)
        gera_clausulas("/tmp/regras_JRGD", k, n, adj)

# Criar a condicao de parada
# Criar a fila
# Fazer as perguntas para tomar decisoes