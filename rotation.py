import os
from datadog_api_client import ApiClient, Configuration
from datadog_api_client.v2.api.key_management_api import KeyManagementApi
from datadog_api_client.v2.model.api_key_update_attributes import APIKeyUpdateAttributes
from datadog_api_client.v2.model.api_key_update_data import APIKeyUpdateData
from datadog_api_client.v2.model.api_key_update_request import APIKeyUpdateRequest
from datadog_api_client.v2.model.api_keys_type import APIKeysType
from datadog_api_client.v2.model.api_key_create_attributes import APIKeyCreateAttributes
from datadog_api_client.v2.model.api_key_create_data import APIKeyCreateData
from datadog_api_client.v2.model.api_key_create_request import APIKeyCreateRequest
import requests
import json

api_key_name = "DD-proxy-teste"

# Configurações do Datadog (URL do Proxy, API Key e Application Key)
proxy_url = "https://api.us5.datadoghq.com/api/v2/api_keys"
api_key = "<SUA API KEY>"
app_key = "<SUA APP KEY>"

# there is a valid "api_key" in the system

def get_apikeys():
    try:
        headers = {
                    "DD-SITE": proxy_url,
                    "DD-API-KEY": api_key,
                    "DD-APPLICATION-KEY": app_key,
                    "Content-Type": "application/json"
                }

        configuration = Configuration()
        configuration.api_key['apiKeyAuth'] = api_key
        configuration.api_key['appKeyAuth'] = app_key


                # Envia a solicitação para o proxy
        headers = {
            "DD-SITE": proxy_url,
            "DD-API-KEY": api_key,
            "DD-APPLICATION-KEY": app_key,
            "Content-Type": "application/json"
        }

        response = requests.get(proxy_url, headers=headers)
        response.raise_for_status()  # Levanta uma exceção se a solicitação falhar


        # Captura a resposta JSON
        response_data = response.json()
        # Captura a resposta JSON
        #print(response_data)

         # Itera sobre a lista de API keys na resposta
        for api_key_data in response_data.get("data", {}):
            name = api_key_data.get("attributes", {}).get("name")
            key_id = api_key_data.get("id")
            print(f"Name: {name}, ID: {key_id}")
            
            if name == api_key_name:
                renomeia_apikey(key_id)
            else:
                print('API Key a ser rotacionada não foi encontrada')    

    except requests.exceptions.RequestException as e:
        print(f"Erro: {e}")


def renomeia_apikey(API_KEY_DATA_ID):
    try:
        body = APIKeyUpdateRequest(
            data=APIKeyUpdateData(
                type=APIKeysType.API_KEYS,
                id=API_KEY_DATA_ID,
                attributes=APIKeyUpdateAttributes(
                    name=f"{api_key_name}-old",
                ),
            ),
        )

        headers = {
                    "DD-SITE": f"proxy_url/{API_KEY_DATA_ID}",
                    "DD-API-KEY": api_key,
                    "DD-APPLICATION-KEY": app_key,
                    "Content-Type": "application/json"
                }

        configuration = Configuration()
        configuration.api_key['apiKeyAuth'] = api_key
        configuration.api_key['appKeyAuth'] = app_key

        body_json = body.to_dict()

        # Envia a solicitação para o proxy

        response = requests.patch(f"{proxy_url}/{API_KEY_DATA_ID}", json=body_json, headers=headers)
        response.raise_for_status()  # Levanta uma exceção se a solicitação falhar

        # Captura a resposta JSON
        response_data = response.json()

        name = response_data.get("data", {}).get("attributes", {}).get("name")

        print(f"API Key renomeada para:{name}")
        criar_api_key_e_salvar(api_key_name)
    
    except requests.exceptions.RequestException as e:
        print(f"Erro: {e}")

# Função para criar a API Key através do proxy e salvar a resposta no arquivo JSON
def criar_api_key_e_salvar(api_key_name):
    try:
        # Dados para criação da API Key
        body = APIKeyCreateRequest(
            data=APIKeyCreateData(
                type=APIKeysType.API_KEYS,
                attributes=APIKeyCreateAttributes(
                    name=api_key_name
                ),
            ),
        )

        # Configuração do cliente Datadog com a API Key e Application Key
        configuration = Configuration()
        configuration.api_key['apiKeyAuth'] = api_key
        configuration.api_key['appKeyAuth'] = app_key
        
        # Serializa o corpo da requisição para JSON
        body_json = body.to_dict()

        # Envia a solicitação para o proxy
        headers = {
            "DD-SITE": proxy_url,
            "DD-API-KEY": api_key,
            "DD-APPLICATION-KEY": app_key,
            "Content-Type": "application/json"
        }
        
        response = requests.post(proxy_url, json=body_json, headers=headers)
        response.raise_for_status()  # Levanta uma exceção se a solicitação falhar

        # Captura a resposta JSON
        response_data = response.json()
        #print(f"Resposta do proxy: {response_data}")

        # Extrair apenas os campos `data.attributes.key`, `data.id`, name e created_at
        name = response_data.get("data", {}).get("attributes", {}).get("name")
        created_at = response_data.get("data", {}).get("attributes", {}).get("created_at")
        key = response_data.get("data", {}).get("attributes", {}).get("key")
        data_id = response_data.get("data", {}).get("id")

        # Criar um dicionário apenas com os valores desejados
        result = {
            "name": name,
            "created_at": created_at,
            "key": key,
            "id": data_id
        }

        print(f"API Key gerada: {result}")

        # Define o caminho para salvar o arquivo JSON no diretório /tmp
        file_path = os.path.join('/tmp', 'datadog_api_key_response.json')

        # Salva a resposta no arquivo JSON
        with open(file_path, 'w') as json_file:
            json.dump(result, json_file, indent=4)
        
        print(f"Registro salvo no: {file_path}")

         # Enviar o id e key para o Vault
        enviar_para_vault(data_id, key)

    except requests.exceptions.RequestException as e:
        print(f"Erro ao conectar ao proxy: {e}")

# Função para enviar os dados para o Vault
def enviar_para_vault(data_id, key):
    # Configurações do Vault
    vault_url = "http://127.0.0.1:8200/v1/secret/data/datadog"
    vault_token = "<SEU TOKEN>"
    
    # Dados a serem enviados para o Vault
    vault_data = {
        "data": {
            "id": data_id,
            "key": key
        }
    }

    headers = {
        "X-Vault-Token": vault_token,
        "Content-Type": "application/json"
    }

    try:
        response = requests.post(vault_url, json=vault_data, headers=headers)
        response.raise_for_status()  # Levanta uma exceção se a solicitação falhar
        print("Dados enviados para o Vault com sucesso.")
        get_apikey_old()

    except requests.exceptions.RequestException as e:
        print(f"Erro ao enviar dados para o Vault: {e}")


def get_apikey_old():
    try:
        headers = {
                    "DD-SITE": proxy_url,
                    "DD-API-KEY": api_key,
                    "DD-APPLICATION-KEY": app_key,
                    "Content-Type": "application/json"
                }

        configuration = Configuration()
        configuration.api_key['apiKeyAuth'] = api_key
        configuration.api_key['appKeyAuth'] = app_key


                # Envia a solicitação para o proxy
        headers = {
            "DD-SITE": proxy_url,
            "DD-API-KEY": api_key,
            "DD-APPLICATION-KEY": app_key,
            "Content-Type": "application/json"
        }

        response = requests.get(proxy_url, headers=headers)
        response.raise_for_status()  # Levanta uma exceção se a solicitação falhar


        # Captura a resposta JSON
        response_data = response.json()
        # Captura a resposta JSON
        #print(response_data)

         # Itera sobre a lista de API keys na resposta
        for api_key_data in response_data.get("data", {}):
            name = api_key_data.get("attributes", {}).get("name")
            key_id = api_key_data.get("id")
            print(f"Name: {name}, ID: {key_id}")
            
            if name == f"{api_key_name}-old":
                delete_apikey(key_id)
            else:
                print('API Key a ser removida não foi encontrada')    

    except requests.exceptions.RequestException as e:
        print(f"Erro: {e}")



def delete_apikey(key_id):
    try:
        headers = {
                    "DD-SITE": proxy_url,
                    "DD-API-KEY": api_key,
                    "DD-APPLICATION-KEY": app_key,
                    "Content-Type": "application/json"
                }

        configuration = Configuration()
        configuration.api_key['apiKeyAuth'] = api_key
        configuration.api_key['appKeyAuth'] = app_key


                # Envia a solicitação para o proxy
        headers = {
            "DD-SITE": proxy_url,
            "DD-API-KEY": api_key,
            "DD-APPLICATION-KEY": app_key,
            "Content-Type": "application/json"
        }

        response = requests.delete(f"{proxy_url}/{key_id}", headers=headers)
        response.raise_for_status()  # Levanta uma exceção se a solicitação falhar

        # Captura a resposta JSON
        print('API Key antiga removida!')

    except requests.exceptions.RequestException as e:
        print(f"Erro: {e}")
    

if __name__ == '__main__':
    get_apikeys()