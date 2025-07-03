#%%
import requests
import pandas as pd
import json


def get_city_coord(city):
    url = "https://nominatim.openstreetmap.org/search"


    params = {
        "q": f"{city}, Brasil",
        "format": "json", 
        "limit": 1   
    }  

    headers = {
        "User-Agent": "clima-teste/1.0"   
    }

    response = requests.get(url, params=params, headers=headers)
    if response.status_code == 200:
        data = response.json()
        if data:
            return float(data[0]["lat"]), float(data[0]["lon"])
        else:
            print(f" Não encontrado: {city}")
           


def previsao_temp(lat, lon, cidade):
    url = "https://api.open-meteo.com/v1/forecast"

    params = {
        "latitude": lat,
        "longitude": lon,
        "hourly": ["temperature_2m", "wind_speed_10m"],
        "daily": "rain_sum",
        "timezone": "America/Sao_Paulo"
    }

    response = requests.get(url, params=params)
    data = response.json()

    data_hora = pd.to_datetime(data['hourly']['time'])
    temps = data['hourly']['temperature_2m']
    vento = data['hourly']['wind_speed_10m']
    

    df = pd.DataFrame({
        "datetime": data_hora,
        "temperatura": temps,
        "vento_10m": vento    
    })

    df['data'] = df['datetime'].dt.date

    min_temps = df.loc[df.groupby('data')['temperatura'].idxmin()]
    max_temps = df.loc[df.groupby('data')['temperatura'].idxmax()]


    min_temps = min_temps.reset_index(drop=True)
    max_temps = max_temps.reset_index(drop=True)
 

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
    url = "https://api.open-meteo.com/v1/forecast"

    params = {
        "latitude": lat,
        "longitude": lon,
        "daily": "rain_sum",
        "timezone": "America/Sao_Paulo"
    }

    response = requests.get(url, params=params)
    data = response.json()

    data_hora = pd.to_datetime(data['daily']['time'])
    chuva = data['daily']['rain_sum']

    df = pd.DataFrame({
        "datetime": data_hora.date,
        "chuva_total": chuva,
        "cidade": cidade        
    })

    return(df)



def main():
    # 1. Carregar lista de capitais
    with open('capitais.json', 'r') as file:
        capitais = json.load(file)

    # 2. Obter coordenadas
    localizacao = []

    for cidade in capitais:

        lat, lon = get_city_coord(cidade)
        localizacao.append({
            "latitude": lat,
            "longitude": lon,
            "cidade": cidade
        })
        
        

    # 3. Obter previsões de temperatura e vento
    lista_temp = []

    for linha in localizacao:
        lat = linha["latitude"]
        lon = linha["longitude"]
        cidade = linha["cidade"]
        
        df_previsao = previsao_temp(lat, lon, cidade)
        
        if df_previsao is not None:
            lista_temp.append(df_previsao)

    df_temp_total = pd.concat(lista_temp, ignore_index=True)



    # 4. Obter previsões de chuva
    lista_chuva = []

    for linha in localizacao:
        lat = linha["latitude"]
        lon = linha["longitude"]
        cidade = linha["cidade"]
        
        df_chuva = chuva_total(lat, lon, cidade)
        
        if df_chuva is not None:
            lista_chuva.append(df_chuva)
            
    df_chuva_total = pd.concat(lista_chuva, ignore_index=True)



    # 5. Unir dados
    df_completo = pd.merge(
        df_temp_total,
        df_chuva_total,
        left_on=['cidade', 'date'], 
        right_on=['cidade', 'datetime'],
        how='left'    
    ).drop(columns=['datetime'])
    
    
    
    
if __name__ == "__main__":
    main()
    
