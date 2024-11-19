# Passo 1: Escolher uma imagem base com Python
FROM python:3.9-slim

# Passo 2: Definir o diretório de trabalho dentro do container
WORKDIR /app

# Passo 3: Copiar o arquivo requirements.txt para o diretório de trabalho do container
COPY requirements.txt /app/

# Passo 4: Instalar as dependências do projeto
RUN pip install --no-cache-dir -r requirements.txt

# Passo 5: Copiar o código (main.py) para o diretório de trabalho do container
COPY main.py /app/

# Passo 6: Expôr a porta 5000 (a porta onde o Flask vai rodar)
EXPOSE 7964

# Passo 7: Definir o comando para rodar o servidor Flask quando o container iniciar
CMD ["python", "main.py"]