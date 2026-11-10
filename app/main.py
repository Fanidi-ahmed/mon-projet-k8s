from fastapi import FastAPI, Response, status
import os
from redis import Redis

app = FastAPI(title="FastAPI + Redis Demo")

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", None)

redis_client = Redis(
    host=REDIS_HOST, port=6379, password=REDIS_PASSWORD, decode_responses=True
)


@app.get("/")
def read_root():
    return {"message": "Hello from FastAPI on Kubernetes!"}


# LIVENESS : Est-ce que l'application tourne ?
@app.api_route("/health", methods=["GET", "HEAD"])
def health_check():
    return {"status": "alive"}


# READINESS : Teste Redis (Autorise GET et HEAD pour Kubernetes)
@app.api_route("/ready", methods=["GET", "HEAD"])
def readiness_check(response: Response):
    try:
        redis_client.ping()
        return {"status": "ready", "redis": "connected"}
    except Exception as e:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return {"status": "not_ready", "error": str(e)}


@app.get("/count")
def increment_counter():
    count = redis_client.incr("visits")
    return {"visits": count}
