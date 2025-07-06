
import requests
import pandas as pd


def busca_coordenada(city):
    # URL da API da Nominatim busca de lat, lon
    url = "https://nominatim.openstreetmap.org/search"


    params = {
    "city": city,
    "country": "Brasil",
    "format": "json",
    "limit": 1    
    }     

    headers = {"User-Agent": "clima-teste/1.0" }

    try:
        response = requests.get(url, params=params, headers=headers)
        response.raise_for_status() # dispara erro se não for 200
        data = response.json()
        
        
        if data:
                # Pega primeiro dict e a chave, convert de string para número flutuante
            return (
                float(data[0]["lat"]),
                float(data[0]["lon"]),
                )
        else:
            print(f"Dado não encontrado: {city}")
            return
    except Exception as e:
        print(f"Erro encontrado em {city}: {e}")        
        return

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
    
    try:
        response = requests.get(url, params=params)
        response.raise_for_status() # dispara erro se não for 200
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
                "lat": lat,
                "lon": lon,
                "time_min": min_temps['datetime'].dt.time,
                "temp_min": min_temps['temperatura'],
                "vento_10m_min": min_temps['vento_10m'],
                "time_max": max_temps['datetime'].dt.time ,
                "temp_max": max_temps['temperatura'],
                "vento_10m_max": max_temps['vento_10m']
                })
            return(result)
        
    except Exception as e:
        print("Erro encontrado em {cidade}: {e} ")

def chuva_total(lat, lon, cidade):
    # URL da API da Open Meteo busca de chuva baseada na lat, lon
    url = "https://api.open-meteo.com/v1/forecast"

    params = {
        "latitude": lat,
        "longitude": lon,
        "daily": "rain_sum",
        "timezone": "America/Sao_Paulo"
    }

    try:    
        response = requests.get(url, params=params)
        response.raise_for_status() # dispara erro se não for 200
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
    
    except Exception as e:
        print(f'Erro encontrado em: {cidade}: {e}')




