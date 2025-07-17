from fastapi import FastAPI

app = FastAPI()

@app.get("/ping")
def pong() -> dict[str, str]:
    return {"ping": "pong"}

@app.get("/readability")
def complex(nick: str) -> dict[str, float]:
    import s_flesch
    return {"score": s_flesch.flesch_score(nick)}