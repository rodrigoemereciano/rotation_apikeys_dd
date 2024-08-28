import os
import requests
import json
from datadog_api_client import ApiClient, Configuration
from datadog_api_client.v2.api.key_management_api import KeyManagementApi
from datadog_api_client.v2.model.api_key_update_attributes import APIKeyUpdateAttributes
from datadog_api_client.v2.model.api_key_update_data import APIKeyUpdateData
from datadog_api_client.v2.model.api_key_update_request import APIKeyUpdateRequest
from datadog_api_client.v2.model.api_keys_type import APIKeysType
from datadog_api_client.v2.model.api_key_create_attributes import APIKeyCreateAttributes
from datadog_api_client.v2.model.api_key_create_data import APIKeyCreateData
from datadog_api_client.v2.model.api_key_create_request import APIKeyCreateRequest
from datadog_api_client.v2.model.application_key_update_attributes import ApplicationKeyUpdateAttributes
from datadog_api_client.v2.model.application_key_update_data import ApplicationKeyUpdateData
from datadog_api_client.v2.model.application_key_update_request import ApplicationKeyUpdateRequest
from datadog_api_client.v2.model.application_keys_type import ApplicationKeysType
from datadog_api_client.v1.model.application_key import ApplicationKey


api_key_name = os.getenv('API_NAME')
app_key_name = os.getenv('APP_NAME')
vault_url_defined = os.getenv('VAULT_URL')

# Configurações do Datadog (URL do Proxy, API Key e Application Key)
proxy_url = "https://api.us5.datadoghq.com/api/v2/api_keys"
proxy_url_app = "https://api.us5.datadoghq.com/api/v2/application_keys"
proxy_url_app_create = "https://api.us5.datadoghq.com/api/v1/application_key"
api_key = "<apikey>"
app_key = "<appkey>"


def get_apikeys():
    try:
        print("#### BUSCA API KEY ALVO ####")
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
        print("#### RENOMEIA API KEY ATUAL PARA OLD  ####")
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
        print("#### GERA NEW API KEY ####")
        global response_api_key

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
        response_api_key = response_data.get("data", {}).get("attributes", {}).get("key")
        data_id = response_data.get("data", {}).get("id")

        # Criar um dicionário apenas com os valores desejados
        result = {
            "name": name,
            "created_at": created_at,
            "key": response_api_key,
            "id": data_id
        }

        print(f"API Key gerada: {result}")

        # Define o caminho para salvar o arquivo JSON no diretório /tmp
        file_path = os.path.join('/app', 'datadog_api_key_response.json')

        # Salva a resposta no arquivo JSON
        with open(file_path, 'w') as json_file:
            json.dump(result, json_file, indent=4)
        
        print(f"Registro salvo no: {file_path}")

         # Enviar o id e key para o Vault
        # enviar_para_vault(data_id, key)   Comentado para chamada posterior
        get_appkeys()

    except requests.exceptions.RequestException as e:
        print(f"Erro ao conectar ao proxy: {e}")

def get_appkeys():
    try:
        print("#### BUSCA APP KEY ALVO ####")
        headers = {
                    "DD-SITE": proxy_url_app,
                    "DD-API-KEY": api_key,
                    "DD-APPLICATION-KEY": app_key,
                    "Content-Type": "application/json"
                }

        configuration = Configuration()
        configuration.api_key['apiKeyAuth'] = api_key
        configuration.api_key['appKeyAuth'] = app_key


                # Envia a solicitação para o proxy
        headers = {
            "DD-SITE": proxy_url_app,
            "DD-API-KEY": api_key,
            "DD-APPLICATION-KEY": app_key,
            "Content-Type": "application/json"
        }

        response = requests.get(proxy_url_app, headers=headers)
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
            
            if name == app_key_name:
                renomeia_appkey(key_id)
            else:
                print('APP Key a ser rotacionada não foi encontrada')    

    except requests.exceptions.RequestException as e:
        print(f"Erro: {e}")

def renomeia_appkey(APPLICATION_KEY_DATA_ID):
    try:
        print("#### RENOMEIA APP KEY ATUAL PARA OLD ####")
        body = ApplicationKeyUpdateRequest(
            data=ApplicationKeyUpdateData(
                type=ApplicationKeysType.APPLICATION_KEYS,
                id=APPLICATION_KEY_DATA_ID,
                attributes=ApplicationKeyUpdateAttributes(
                    name=f"{app_key_name}-old",
                ),
            ),
        )

        headers = {
                    "DD-SITE": f"proxy_url_app/{APPLICATION_KEY_DATA_ID}",
                    "DD-API-KEY": api_key,
                    "DD-APPLICATION-KEY": app_key,
                    "Content-Type": "application/json"
                }

        configuration = Configuration()
        configuration.api_key['apiKeyAuth'] = api_key
        configuration.api_key['appKeyAuth'] = app_key

        body_json = body.to_dict()

        # Envia a solicitação para o proxy

        response = requests.patch(f"{proxy_url_app}/{APPLICATION_KEY_DATA_ID}", json=body_json, headers=headers)
        response.raise_for_status()  # Levanta uma exceção se a solicitação falhar

        # Captura a resposta JSON
        response_data = response.json()

        name = response_data.get("data", {}).get("attributes", {}).get("name")

        print(f"APP Key renomeada para:{name}")
        criar_app_key_e_salvar(app_key_name)
    
    except requests.exceptions.RequestException as e:
        print(f"Erro: {e}")

# Função para criar a API Key através do proxy e salvar a resposta no arquivo JSON
def criar_app_key_e_salvar(app_key_name):
    try:
        print("#### GERA NEW APP KEY ####")
        global response_app_key

        # Dados para criação da API Key
        body = ApplicationKey(
                name=app_key_name
            )

        # Configuração do cliente Datadog com a API Key e Application Key
        configuration = Configuration()
        configuration.api_key['apiKeyAuth'] = api_key
        configuration.api_key['appKeyAuth'] = app_key
        
        # Serializa o corpo da requisição para JSON
        body_json = body.to_dict()

        # Envia a solicitação para o proxy
        headers = {
            "DD-SITE": proxy_url_app_create,
            "DD-API-KEY": api_key,
            "DD-APPLICATION-KEY": app_key,
            "Content-Type": "application/json"
        }
        
        response = requests.post(proxy_url_app_create, json=body_json, headers=headers)
        response.raise_for_status()  # Levanta uma exceção se a solicitação falhar

        # Captura a resposta JSON
        response_data = response.json()
        #print(f"Resposta do proxy: {response_data}")

        # Extrair apenas os campos `application_key.hash`, `application_key.name`
        name = response_data.get("application_key", {}).get("name")
        response_app_key = response_data.get("application_key", {}).get("hash")

        # Criar um dicionário apenas com os valores desejados
        result = {
            "name": name,
            "key": response_app_key
        }

        print(f"APP Key gerada: {result}")

        # Define o caminho para salvar o arquivo JSON no diretório /tmp
        file_path = os.path.join('/app', 'datadog_app_key_response.json')

        # Salva a resposta no arquivo JSON
        with open(file_path, 'w') as json_file:
            json.dump(result, json_file, indent=4)
        
        print(f"Registro salvo no: {file_path}")

         # Enviar o id e key para o Vault
        enviar_para_vault(response_api_key, response_app_key)

    except requests.exceptions.RequestException as e:
        print(f"Erro ao conectar ao proxy: {e}")


# Função para enviar os dados para o Vault
def enviar_para_vault(response_api_key, response_app_key):
    # Configurações do Vault
    vault_url = vault_url_defined
    vault_token = "root_token"
    
    # Dados a serem enviados para o Vault
    vault_data = {
        "data": {
            "api_key": response_api_key,
            "app_key": response_app_key
        }
    }

    headers = {
        "X-Vault-Token": vault_token,
        "Content-Type": "application/json"
    }

    try:
        print("#### ENVIA NOVAS KEYS PARA O VAULT ####")
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

        print("#### REMOVE API KEY OLD ####")

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

        #Chama remoção app_key
        get_appkey_old()

    except requests.exceptions.RequestException as e:
        print(f"Erro: {e}")

def get_appkey_old():
    try:
        headers = {
                    "DD-SITE": proxy_url_app,
                    "DD-API-KEY": api_key,
                    "DD-APPLICATION-KEY": app_key,
                    "Content-Type": "application/json"
                }

        configuration = Configuration()
        configuration.api_key['apiKeyAuth'] = api_key
        configuration.api_key['appKeyAuth'] = app_key


                # Envia a solicitação para o proxy
        headers = {
            "DD-SITE": proxy_url_app,
            "DD-API-KEY": api_key,
            "DD-APPLICATION-KEY": app_key,
            "Content-Type": "application/json"
        }

        response = requests.get(proxy_url_app, headers=headers)
        response.raise_for_status()  # Levanta uma exceção se a solicitação falhar


        # Captura a resposta JSON
        response_data = response.json()
        # Captura a resposta JSON
        print("#### REMOVE APP KEY OLD ####")

        
         # Itera sobre a lista de API keys na resposta
        for api_key_data in response_data.get("data", {}):
            name = api_key_data.get("attributes", {}).get("name")
            key_id = api_key_data.get("id")
            print(f"Name: {name}, ID: {key_id}")
            
            if name == f"{app_key_name}-old":
                delete_appkey(key_id)
            else:
                print('APP Key a ser removida não foi encontrada')    

    except requests.exceptions.RequestException as e:
        print(f"Erro: {e}")



def delete_appkey(key_id):
    try:
        headers = {
                    "DD-SITE": proxy_url_app,
                    "DD-API-KEY": api_key,
                    "DD-APPLICATION-KEY": app_key,
                    "Content-Type": "application/json"
                }

        configuration = Configuration()
        configuration.api_key['apiKeyAuth'] = api_key
        configuration.api_key['appKeyAuth'] = app_key


                # Envia a solicitação para o proxy
        headers = {
            "DD-SITE": proxy_url_app,
            "DD-API-KEY": api_key,
            "DD-APPLICATION-KEY": app_key,
            "Content-Type": "application/json"
        }

        response = requests.delete(f"{proxy_url_app}/{key_id}", headers=headers)
        response.raise_for_status()  # Levanta uma exceção se a solicitação falhar

        # Captura a resposta JSON
        print('APP Key antiga removida!')

    except requests.exceptions.RequestException as e:
        print(f"Erro: {e}")
    

if __name__ == '__main__':
    get_apikeys()