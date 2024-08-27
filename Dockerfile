FROM python:3.9-slim

# Define o diretório de trabalho dentro do contêiner
WORKDIR /app

# Copia o arquivo requirements.txt para o diretório de trabalho
# (Este arquivo conterá as dependências do projeto)
COPY requirements.txt .

# Instala as dependências do Python
RUN pip install --no-cache-dir -r requirements.txt

# Copia o script rotation_apikey_dd.py do diretório atual para o contêiner
COPY rotation_apikey_dd.py .

# Define a variável de ambiente para não gerar arquivos pyc
ENV PYTHONDONTWRITEBYTECODE=1

# Define a variável de ambiente para o Python não fazer buffering
ENV PYTHONUNBUFFERED=1

# Define URL VAULT
ENV VAULT_URL=value1

# Define NAME API KEY
ENV API_NAME=value2

# Comando para rodar o script Python
CMD ["python", "rotation_apikey_dd.py"]
