FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY cargo ./cargo
COPY clients ./clients
COPY run.sh .
CMD ["sh", "run.sh"]
