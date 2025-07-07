#%%
import pandas as pd
import json
from tqdm import tqdm
import time
from clima import busca_coordenada, previsao_temp, previsao_chuva


def main():
    # 1. Lê o JSON e carrega lista de capitais
    with open('capitais.json', 'r') as file:
        capitais = json.load(file)

    # 2. Obter coordenadas
    localizacao = []
    
    # Iteração para chamada da funcao que retorna(lat, long, cidade)
    for cidade in tqdm(capitais,  desc="🔵 Gerando dados de coordenada"):

        lat, lon = busca_coordenada(cidade)
        localizacao.append({
            "latitude": lat,
            "longitude": lon,
            "cidade": cidade
        })
        time.sleep(1.1)

    # 3. Obter previsões de temperatura e vento
    lista_temp = []
    
    # Iteração para chamada da funcao que retorna(temperatura, vento) 
    for linha in tqdm(localizacao, desc="🟠 Gerando dados de temperatura"):
        lat = linha["latitude"]
        lon = linha["longitude"]
        cidade = linha["cidade"]

        
        df_temp = previsao_temp(lat, lon, cidade)
        
        if df_temp is not None:
            lista_temp.append(df_temp)
        time.sleep(1.1)
            
    # Unindo todas iterações
    df_temp_total = pd.concat(lista_temp, ignore_index=True)



    # 4. Obter previsões de chuva
    lista_chuva = []
    
    # Iteração para chamada da funcao que retorna(chuva) 
    for linha in tqdm(localizacao, desc="🟢 Gerando dados de chuva"):
        lat = linha["latitude"]
        lon = linha["longitude"]
        cidade = linha["cidade"]
        
        
        df_chuva = previsao_chuva(lat, lon, cidade)
        
        if df_chuva is not None:
            lista_chuva.append(df_chuva)
    time.sleep(1.1)
            
    # Unindo todas iterações        
    df_chuva_total = pd.concat(lista_chuva, ignore_index=True)


    # 5. Unir dados
    df_completo = pd.merge(
        df_temp_total,
        df_chuva_total,
        left_on=['cidade', 'date'], 
        right_on=['cidade', 'datetime'],
        how='left'    
    ).drop(columns=['datetime'])
    
    return df_completo   
    
    
if __name__ == "__main__":
    df = main()
    print(df.head())
