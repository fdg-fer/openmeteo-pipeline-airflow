#%%
import json


capitais = [
    "Rio Branco", "Maceió", "Macapá", "Manaus", "Salvador", "Fortaleza", "Brasília", "Vitória", 
    "Goiânia", "São Luís", "Cuiabá", "Campo Grande", "Belo Horizonte", "Belém", "João Pessoa", 
    "Curitiba", "Recife", "Teresina", "Rio de Janeiro", "Natal", "Porto Alegre", "Porto Velho", 
    "Boa Vista", "Florianópolis", "São Paulo", "Aracaju", "Palmas"
]


with open('capitais.json', 'w') as arquivo:
    json.dump(capitais, arquivo)
