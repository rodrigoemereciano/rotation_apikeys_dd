# Use uma imagem base oficial do Python
FROM python:3.9-slim

# Defina o diretório de trabalho dentro do contêiner
WORKDIR /app

# Copie o arquivo requirements.txt para o diretório de trabalho
# (Este arquivo conterá as dependências do projeto)
COPY requirements.txt .

# Instale as dependências do Python
RUN pip install --no-cache-dir -r requirements.txt

# Copia todos o script rotation_apikey_dd.py do diretório atual para o contêiner
COPY rotation_apikey_dd.py .

# Defina a variável de ambiente para não gerar arquivos pyc
ENV PYTHONDONTWRITEBYTECODE=1

# Defina a variável de ambiente para o Python não fazer buffering
ENV PYTHONUNBUFFERED=1

#URL VAULT
ENV VAULT_URL=value1

#NAME API KEY
ENV API_NAME=value2

# Comando para rodar o script Python
CMD ["python", "rotation_apikey_dd.py"]
