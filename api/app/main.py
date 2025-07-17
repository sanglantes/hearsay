from fastapi import FastAPI

app = FastAPI() oi

@app.get("/ping")
def pong():
    return {"ping": "pong"}