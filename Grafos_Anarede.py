import re
import pandas as pd
from collections import defaultdict, deque

# Gera Lista de Barras e Lista de Linhas
# Selecionar o caso do anarede para abrir
with open('caso2029acesso.PWF', encoding='latin-1') as f:
    arqv_pwf = f.readlines()

# Retorna DataFrame com numeração da Barra, Tipo, Nome, Grupo Base, Grupo limite e área
def info_barras(arqv_pwf):    
    # Posições do DBAR
    linha_inicial_dbar = arqv_pwf.index('DBAR\n')
    linha_final_dbar = arqv_pwf.index('99999\n', linha_inicial_dbar)
    
    # Barra, Tipo, Nome, Grupo Base, Grupo limite e área
    DBAR = []
    for i in range(linha_inicial_dbar, linha_final_dbar):
        if arqv_pwf[i] not in ['DBAR\n'] and arqv_pwf[i][0]!='(':
            DBAR.append((arqv_pwf[i][0:5].strip(), arqv_pwf[i][7:8].strip(), arqv_pwf[i][10:22].strip(), arqv_pwf[i][8:10].strip(), arqv_pwf[i][22:24].strip(), int(arqv_pwf[i][73:76].strip()), arqv_pwf[i][58:63].strip()))

    # Criando dataframe
    df1 = pd.DataFrame(DBAR, columns=['num', 'tipo', 'nome', 'gb', 'gl', 'area', 'carga'])  
    df1["gb"].replace({'0':1,'3':1, '03':1, '5':1,'6':13.5,'7':1,'8':1, '08':1, '11':10.5,'12':12.3,'15':15,'16':15.7,'17':17.1,'18':18.3,'19':18.5,'24':24,'25':1,'26':1,'27':26,'28':1,'29':1,'30':30,'39':19,'A':765,'B':525,'C':500,'D':440,'E':345,'F':230,'G':138,'H':88,'I':69,'J':46,'L':34.5,'M':34,'N':13.8,'O':13.4,'OR':1,'P':23,'Q':20,'R':6.9,'S':12,'T':1.,'U':1.,'V':1.,'W':161,'X':13.2,'Y':1.,'Z':11.9}, inplace=True)
    df1.loc[((df1['area'] >= 1) & (df1['area'] <= 105)) | ((df1['area'] >= 401) & (df1['area'] <= 405)), 'regiao'] = 'S'  
    df1.loc[((df1['area'] >= 201) & (df1['area'] <= 363)) | ((df1['area'] >= 431) & (df1['area'] <= 564)), 'regiao'] = 'SECO'
    df1.loc[((df1['area'] >= 581) & (df1['area'] <= 883)), 'regiao'] = 'NNE'  
    
    return df1


barras = info_barras(arqv_pwf)

# Posições do DLIN
linha_inicial_dlin = arqv_pwf.index('DLIN\n')
linha_final_dlin = arqv_pwf.index('99999\n', linha_inicial_dlin)

todos_trafos=[] 
ltc_trafos=[]
# Procura trafos
DLIN = []
for i in range(linha_inicial_dlin, linha_final_dlin):
    if (arqv_pwf[i][0]!='(') and (arqv_pwf[i]!='DLIN\n'):
        todos_trafos.append((arqv_pwf[i][0:5].strip(), arqv_pwf[i][10:16].strip(), arqv_pwf[i][15:17].strip()))       

ltc_trafos_df = pd.DataFrame(todos_trafos, columns=['De', 'Para', 'Num'])

# Filtro de áreas ONS
areas_selecionadas = [701,702,704,711,712,715,716,721,722,724,741,742,744,761,762,764,771,772]
fontes_usinas = ['UFV', 'EOL', 'UEE', 'UTE']
barras_eol_ufv = barras[(barras['tipo']=='1') & (barras['area'].isin(areas_selecionadas)) & (barras['nome'].str[-6:-3].isin(fontes_usinas))]
barras_eol_ufv['barra_alta'] = 'teste'
barras_eol_ufv['conexoes'] = ''
barras_eol_ufv

# Obter a barra de alta por meio de grafos
# A parada é quando ele encontra uma barra de 500, 230, 138 ou 69 kV
def parse_dlin(ltc_trafos_df):
    graph = defaultdict(list)
    for i in range(len(ltc_trafos_df)):
        # Extrair os dois pontos de conexão (De e Pa)
        de = int(ltc_trafos_df.iloc[i,:]['De'])
        pa = int(ltc_trafos_df.iloc[i,:]['Para'])
        
        # Adicionar uma aresta bidirecional ao grafo
        graph[de].append(pa)
        graph[pa].append(de)
        
    return graph


def bfs_connections(graph, start_node):
    visited = set()
    queue = deque([start_node])
    connected_nodes = []

    while queue:
        node = queue.popleft()
        if node not in visited:
            visited.add(node)
            connected_nodes.append(node)
            if ((barras[barras['num'] == str(node)]['gb'].values[0] == 500) or (barras[barras['num'] == str(node)]['gb'].values[0] == 230) or (barras[barras['num'] == str(node)]['gb'].values[0] == 69) or (barras[barras['num'] == str(node)]['gb'].values[0] == 138)):
                return connected_nodes
            
            for neighbor in graph[node]:
                if neighbor not in visited:
                    queue.append(neighbor)

    return connected_nodes

# Construir o grafo
graph = parse_dlin(ltc_trafos_df)

# Encontrar todas as conexões a partir do nó
for i in range(len(barras_eol_ufv)):
    connected_nodes = bfs_connections(graph, int(barras_eol_ufv.iloc[i,:]['num']))
    barra_alta = connected_nodes[-1]
    barras_eol_ufv.iloc[i, 8] = barra_alta
    barras_eol_ufv.iloc[i, 9] = str(connected_nodes)

print("Nodos conectados:", connected_nodes)

# Planilha de saida com todas as vizinhanças
barras_eol_ufv.to_excel("casoacesso.xlsx")