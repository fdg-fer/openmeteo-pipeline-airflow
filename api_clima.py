#%%
import requests
import pandas as pd
import json


def get_city_coord(city):
    # URL da API da Nominatim busca de lat, lon
    url = "https://nominatim.openstreetmap.org/search"


    params = {
        # Query que busca a cidade 
        "q": f"{city}, Brasil",
        "format": "json", 
        "limit": 1   
    }  

    headers = {
        "User-Agent": "clima-teste/1.0"   
    }

    response = requests.get(url, params=params, headers=headers)
    # Se solicitação bem sucedida retornar resposta
    if response.status_code == 200:
        data = response.json()
        if data:
            # Pega primeiro dict e a chave, convert de string para número flutuante
            return float(data[0]["lat"]), float(data[0]["lon"])
        else:
            print(f" Não encontrado: {city}")
           


def previsao_temp(lat, lon, cidade):
    # URL da API da Open Meteo busca temperatura e vento baseada na lat, lon
    url = "https://api.open-meteo.com/v1/forecast"
    
    # Parametros presentes na API(lat, lon, temperatura/hora, vento/hora)
    params = {
        "latitude": lat,
        "longitude": lon,
        "hourly": ["temperature_2m", "wind_speed_10m"],
        "timezone": "America/Sao_Paulo"
    }

    response = requests.get(url, params=params)
    data = response.json()
    
    # Transforma em data hora 
    hora_temp = pd.to_datetime(data['hourly']['time'])
    # Extrai Temperatura por hota
    temps = data['hourly']['temperature_2m']
    # Extrai Vento por hora
    vento = data['hourly']['wind_speed_10m']
    
    # Dataframe dict dos dados extraídos
    df = pd.DataFrame({
        "datetime": hora_temp,
        "temperatura": temps,
        "vento_10m": vento    
    })
    
    # Criando coluna de data(o dt.date captura apenas a data)
    df['data'] = df['datetime'].dt.date

    # Agrupa por data e retorna o índice de menor temperatura
    min_temps = df.loc[df.groupby('data')['temperatura'].idxmin()]
    # Agrupa por data e retorna o índice de maior temperatura 
    max_temps = df.loc[df.groupby('data')['temperatura'].idxmax()]

    # Resetando os indexs
    min_temps = min_temps.reset_index(drop=True)
    max_temps = max_temps.reset_index(drop=True)
 
    # Resultado de todas as colunas em um único Dataframe
    if response.status_code == 200:
        result = pd.DataFrame({
            "date": min_temps['data'],
            "cidade": cidade,
            "time_min": min_temps['datetime'].dt.time,
            "temp_min": min_temps['temperatura'],
            "vento_10m_min": min_temps['vento_10m'],
            "time_max": max_temps['datetime'].dt.time ,
            "temp_max": max_temps['temperatura'],
            "vento_10m_max": max_temps['vento_10m'],
                          
        })
        return(result)



def chuva_total(lat, lon, cidade):
    # URL da API da Open Meteo busca de chuva baseada na lat, lon
    url = "https://api.open-meteo.com/v1/forecast"

    params = {
        "latitude": lat,
        "longitude": lon,
        "daily": "rain_sum",
        "timezone": "America/Sao_Paulo"
    }

    response = requests.get(url, params=params)
    data = response.json()
    
    # Transforma em data hora
    hora_chuva = pd.to_datetime(data['daily']['time'])
    # Extrai a chuva por hora
    chuva = data['daily']['rain_sum']
    
    # Dataframe dict dos dados extraídos
    df = pd.DataFrame({
        "datetime": hora_chuva.date,
        "chuva_total": chuva,
        "cidade": cidade        
    })

    return(df)



def main():
    # 1. Lê o JSON e carrega lista de capitais
    with open('capitais.json', 'r') as file:
        capitais = json.load(file)

    # 2. Obter coordenadas
    localizacao = []
    
    # Iteração para chamada da funcao que retorna(lat, long, cidade)
    for cidade in capitais:

        lat, lon = get_city_coord(cidade)
        localizacao.append({
            "latitude": lat,
            "longitude": lon,
            "cidade": cidade
        })
        
        

    # 3. Obter previsões de temperatura e vento
    lista_temp = []
    
    # Iteração para chamada da funcao que retorna(temperatura, vento) 
    for linha in localizacao:
        lat = linha["latitude"]
        lon = linha["longitude"]
        cidade = linha["cidade"]
        
        df_previsao = previsao_temp(lat, lon, cidade)
        
        if df_previsao is not None:
            lista_temp.append(df_previsao)
            
    # Unindo todas iterações
    df_temp_total = pd.concat(lista_temp, ignore_index=True)



    # 4. Obter previsões de chuva
    lista_chuva = []
    
    # Iteração para chamada da funcao que retorna(chuva) 
    for linha in localizacao:
        lat = linha["latitude"]
        lon = linha["longitude"]
        cidade = linha["cidade"]
        
        df_chuva = chuva_total(lat, lon, cidade)
        
        if df_chuva is not None:
            lista_chuva.append(df_chuva)
            
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

    
