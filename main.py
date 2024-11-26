import requests, os
import time
from flask import Flask, jsonify, request
import logging
from functools import lru_cache
from dotenv import load_dotenv


load_dotenv()
BITRIX_WEBHOOK_URL = os.getenv('BITRIX_WEBHOOK_URL')
URL_VIACEP = os.getenv('URL_VIACEP')
URL_OPENCEP = os.getenv('URL_OPENCEP')
URL_BRASILAPI = os.getenv('URL_BRASILAPI')


app = Flask(__name__)


logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

@lru_cache(maxsize=100)
def get_city_and_uf(cep):
    logging.info(f"Consultando o CEP: {cep}")
    cep = cep.strip().replace("-", "")

    try:
        url_viacep = f"{URL_VIACEP}"
        response = requests.get(url_viacep, timeout=5)
        if response.status_code == 200 and "erro" not in response.json():
            data = response.json()
            cidade = data.get("cidade", "")
            rua = data.get("logradouro", "")
            bairro = data.get("bairro", "")
            uf = data.get("uf", "")
            logging.info(f"OpenCEP foi utilizado - Cidade: {cidade}, Rua: {rua}, Bairro: {bairro}, UF: {uf}")
            return cidade, rua, bairro, uf
    except requests.RequestException as e:
        logging.error(f"Erro ao Consultar o ViaCEP: {e}")
    
    try: 
        time.sleep(2)
        url_opencep = f"{URL_OPENCEP}/{cep}"
        response_opencep = requests.get(url_opencep, timeout=5)
        if response_opencep.status_code == 200:
            data = response_opencep.json()
            cidade = data.get("codade", "")
            rua = data.get("logradouro", "")
            bairro = data.get("bairro", "")
            uf = data.get("uf", "")
            logging.info(f"OpenCEP foi utilizado - Cidade: {cidade}, Rua: {rua}, Bairro: {bairro}, UF: {uf}")
            return cidade, rua, bairro, uf
    except requests.RequestException as e: 
        logging.error(f"Erro ao Consultar o OpenCep: {e}")

    try: 
        time.sleep(2)
        url_brasilapi = f"{URL_BRASILAPI}/{cep}"
        response_brasilapi = requests.get(url_brasilapi, timeout=5)
        if response_brasilapi.status_code == 200:
            data = response_brasilapi.json()
            cidade = data.get("city", "")
            rua = data.get("street", "")
            bairro = data.get("neighborhood", "")
            uf = data.get("state", "")
            logging.info(f"BrasilAPI utilizado - Cidade: {cidade}, Rua: {rua}, Bairro: {bairro}, UF: {uf}")
            return cidade, rua, bairro, uf
    except requests.RequestException as e:
        logging.error(f"erro ao Consultar o BrasilAPi: {e}")

    logging.error(f"Erro ao consultar o CEP {cep} nas três APIs. ")
    return None, None, None, None

def update_bitrix24_record(deal_id, cidade, rua, bairro, uf):
    logging.info(f"Atualizado no CRM com Cidade: {cidade}, Rua: {rua}, Bairro: {bairro}, UF: {uf} Para o registro {deal_id}... ")
    url = f"{BITRIX_WEBHOOK_URL}crm.deal.update.json"

    payload = {
        'ID': deal_id,
        'FIELDS': {
            'UF_CRM_1731957897': bairro.upper(),
            'UF_CRM_1731957878': rua.upper(),
            'UF_CRM_1731588487': cidade.upper(),
            'UF_CRM_1731589190': uf.upper(),
        }
    }

    try: 
        response = requests.post(url, json=payload, timeout=5)
        logging.info(f"Resposta da API Bitrix24: {response.status_code} - {response.text}")
        if response.status_code == 200:
            logging.info(f"Registro {deal_id} atualizado com sucesso!")
        else:
            logging.error(f"Erro ao atualizar o registro na Bitrix24:  {response.status_code} - {response.text}")
    except requests.RequestException as e:
        logging.error(f"Erro ao conectar ao Bitrix24: {e}")

@app.route ('/atualizar_cidade_uf/<int:deal_id>/<string:cep>', methods=['POST'])
def atualizar_cidade_uf(deal_id, cep):
    try:
        if not deal_id or not cep:
            logging.error(f"Parâmetros inválidos: deal_id={deal_id}, cep ={cep}")
            return jsonify({"erro": "Parâmetros obrigatórios não fornecidos"}), 400
        cidade, rua, bairro, uf = get_city_and_uf(cep)

        if cidade and uf:
            update_bitrix24_record(deal_id, cidade, rua, bairro, uf)
            return jsonify({"sucesso": f"Registro {deal_id} atualizado com sucesso!"}), 200
        else:
            logging.error("Erro ao obter cidade e uf para o CEP!")
            return jsonify ({"erro": "Não foi possível obter dados para o CEP"}), 400
        
    except Exception as e:
        logging.error(f"Erro inesperado: {e}")
        return jsonify({"erro": f"Erro interno no servidor: {str(e)}"}), 500
    
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=6927)
