FROM python:3.11-slim
WORKDIR /app
COPY api/requirements.txt api/requirements.txt
RUN pip install --no-cache-dir -r api/requirements.txt
COPY api api
COPY api_data api_data
ENV PORT=8080
CMD uvicorn api.app:app --host 0.0.0.0 --port ${PORT}
