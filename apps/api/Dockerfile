FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 APP_HOST=0.0.0.0 APP_PORT=8080 PYTHONPATH=/app/apps/api/src:/app/services/mock-telecom/src
WORKDIR /app
COPY apps/api/requirements.lock /tmp/requirements.lock
RUN pip install --no-cache-dir -r /tmp/requirements.lock && useradd --uid 10001 --create-home relay
COPY apps/api/src apps/api/src
COPY services/mock-telecom/src services/mock-telecom/src
COPY resources/challenge resources/challenge
RUN mkdir -p /app/data && chown relay:relay /app/data
USER relay
EXPOSE 8080
CMD ["python", "-m", "relay_api"]
