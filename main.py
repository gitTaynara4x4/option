import requests
from flask import Flask, jsonify, request
import logging

app = Flask(__name__)

# Defina o URL do seu webhook no Bitrix24
WEBHOOK_URL = "https://marketingsolucoes.bitrix24.com.br/rest/35002/7a2nuej815yjx5bg/"

# Configuração básica de logging
logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO  # Definindo o nível de log para INFO
)

# Função para buscar a cidade e UF via APIs públicas (ViaCEP, OpenCEP, BrasilAPI)
def get_city_and_uf(cep):
    logging.info(f"Consultando o CEP: {cep}")  # Log: indicando que estamos consultando o CEP
    cep = cep.replace("-", "")  # Remover o traço do CEP
    
    # Tentar primeiro a API ViaCEP
    url_viacep = f"https://viacep.com.br/ws/{cep}/json/"
    response = requests.get(url_viacep)
    if response.status_code == 200 and "erro" not in response.json():
        data = response.json()
        cidade = data.get("localidade", "")
        rua = data.get("logradouro", "")
        bairro = data.get("bairro", "")
        uf = data.get("uf", "")
        logging.info(f"ViaCEP utilizado - Cidade: {cidade}, Rua: {rua}, Bairro: {bairro}, UF: {uf}")  # Log para ViaCEP
        return cidade, rua, bairro, uf,
    
    # Se o ViaCEP falhar, tenta o OpenCEP
    logging.info(f"ViaCEP falhou ou retornou erro. Tentando o OpenCEP...")  # Log de falha no ViaCEP
    url_opencep = f"https://opencep.com.br/api/cep/{cep}"
    response_opencep = requests.get(url_opencep)
    if response_opencep.status_code == 200:
        data = response_opencep.json()
        cidade = data.get("cidade", "")
        rua = data.get("logradouro", "")
        bairro = data.get("bairro", "")
        uf = data.get("uf", "")
        logging.info(f"OpenCEP utilizado - Cidade: {cidade}, Rua: {rua}, Bairro: {bairro}, UF: {uf}")  # Log para OpenCEP
        return cidade, rua, bairro, uf

    # Se o OpenCEP falhar, tenta a BrasilAPI
    logging.info(f"OpenCEP falhou ou retornou erro. Tentando o BrasilAPI...")  # Log de falha no OpenCEP
    url_brasilapi = f"https://brasilapi.com.br/api/cep/v2/{cep}"
    response_brasilapi = requests.get(url_brasilapi)
    if response_brasilapi.status_code == 200:
        data = response_brasilapi.json()
        cidade = data.get("city", "")
        rua = data.get("street", "")
        bairro = data.get("neighborhood", "")
        uf = data.get("state", "")
        logging.info(f"BrasilAPI utilizado - Cidade: {cidade}, Rua: {rua}, Bairro: {bairro}, UF: {uf}")  # Log para BrasilAPI
        return cidade, rua, bairro, uf

    # Se todas as APIs falharem
    logging.error(f"Erro ao consultar o CEP {cep} nas três APIs.")  # Log de erro
    return None, None, None, None

# Função para atualizar os campos no Bitrix24
def update_bitrix24_record(deal_id, cidade, rua, bairro, uf):
    logging.info(f"Atualizando o Bitrix24 com Cidade: {cidade}, Rua: {rua}, Bairro: {bairro} UF: {uf} para o registro {deal_id}...")  # Log
    # O endpoint correto para atualizar um "deal" no Bitrix24 é o "crm.deal.update"
    url = f"{WEBHOOK_URL}crm.deal.update.json"

    # Estrutura do payload para a atualização
    payload = {
        'ID': deal_id,  # ID do registro do "deal" que queremos atualizar
        'FIELDS': {
            'UF_CRM_1731957897': bairro.upper(), # Campo Bairro
            'UF_CRM_1731957878': rua.upper(), # Campo Rua
            'UF_CRM_1731588487': cidade.upper(),  # Campo Cidade
            'UF_CRM_1731589190': uf.upper(),   # Campo UF
        }
    }

    # Realizando a requisição POST para o Bitrix24
    response = requests.post(url, json=payload)
    
    # Log detalhado da resposta da API Bitrix24
    logging.info(f"Resposta da API Bitrix24: {response.status_code} - {response.text}")  # Log detalhado da resposta

    if response.status_code == 200:
        # Confirmando a atualização
        logging.info(f"Registro {deal_id} atualizado com sucesso!")
    else:
        # Caso contrário, log de erro detalhado
        logging.error(f"Erro ao atualizar o registro no Bitrix24: {response.status_code} - {response.text}")

# Endpoint da API para atualizar cidade e UF a partir de um CEP
@app.route('/atualizar_cidade_uf/<int:deal_id>/<string:cep>', methods=['POST'])
def atualizar_cidade_uf(deal_id, cep):
    try:
        # Verifica se ambos os parâmetros foram fornecidos
        if not deal_id or not cep:
            logging.error(f"Parâmetros inválidos: deal_id={deal_id}, cep={cep}")  # Log de erro
            return jsonify({"erro": "Parâmetros obrigatórios não fornecidos"}), 400

        # Passo 1: Consultar a cidade e UF pelo CEP
        cidade, rua, bairro, uf = get_city_and_uf(cep)

        if cidade and uf:
            # Passo 2: Atualizar o registro no Bitrix24 com cidade e UF
            update_bitrix24_record(deal_id, cidade, rua, bairro, uf)
            return jsonify({"sucesso": f"Registro {deal_id} atualizado com sucesso!"}), 200
        else:
            logging.error("Erro ao obter cidade e UF para o CEP!")  # Log de erro
            return jsonify({"erro": "Não foi possível obter dados para o CEP"}), 400

    except Exception as e:
        logging.error(f"Erro inesperado: {e}")  # Log de erro inesperado
        return jsonify({"erro": f"Erro interno no servidor: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=7964)