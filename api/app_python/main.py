from asyncio import streams
from fastapi import FastAPI
from fastapi.responses import JSONResponse
import requests

from typing import Optional
from pydantic import BaseModel

app = FastAPI()

@app.get("/ping")
def pong() -> dict[str, str]:
    return {"ping": "pong"}

@app.get("/readability")
def readability(nick: str) -> dict[str, float]:
    import s_readability as s_readability
    return {"score": s_readability.flesch_score(nick)}

class RetrainResponse(BaseModel):
    time: float
    url: Optional[str]
    accuracy: float

@app.get(
    "/retrain",
    response_model=RetrainResponse,
    summary="Retrain the model, optionally return a confusion-matrix link."
)
def retrain(min_messages: int, varg: Optional[str] = None) -> RetrainResponse:
    import s_retrain, joblib, time, requests
    cm_requested = (varg == "--cm")
    pipeline = s_retrain.create_pipeline()

    X, y = s_retrain.get_X_y(min_messages)
    start = time.time()
    pipeline.fit(X, y)
    elapsed = time.time() - start
    joblib.dump(pipeline, "pipeline.joblib")

    url: Optional[str] = None
    accuracy = 0.0
    if cm_requested:
        cm_table, labels, accuracy = s_retrain.evaluate_pipeline(pipeline, X, y)
        s_retrain.plot_and_save_confusion_matrix(cm_table, labels)
        with open("cm.png", "rb") as f:
            resp = requests.post("https://tmpfiles.org/api/v1/upload", files={"file": f})
            print(resp.json())
            if resp.json()["status"] == "success":
                url = resp.json()["data"]["url"]
            else:
                url = "failed"

    return RetrainResponse(time=elapsed, url=url, accuracy=accuracy)

class AttributeRequest(BaseModel):
    msg: str
    min_messages: int

@app.post(
    "/attribute",
    summary="Attribute a message to a chatter."
)
def attribute(req: AttributeRequest) -> str:
    import joblib, os
    import s_retrain

    if not os.path.exists("pipeline.joblib"):
        pipeline = s_retrain.create_pipeline()
        X, y = s_retrain.get_X_y(req.min_messages)
        pipeline.fit(X, y)

        joblib.dump(pipeline, "pipeline.joblib")
    else:
        pipeline = joblib.load("pipeline.joblib")
    
    author = pipeline.predict([req.msg])[0]
    return JSONResponse(content={"author": author})
