FROM python:3.8-slim
WORKDIR /app
COPY . /app
RUN pip install prometheus_client requests
CMD ["python3", "main.py"]