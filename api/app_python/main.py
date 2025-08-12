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

@app.get(
    "/retrain",
    summary="Retrain the model. Optionally return a confusion-matrix link."
)
def retrain(
    min_messages: int,
    cm: Optional[int] = 0,
    cf: Optional[int] = 0
) -> JSONResponse:
    import s_retrain, joblib, time, requests

    cm = bool(cm)

    pipeline = s_retrain.create_pipeline()

    X, y = s_retrain.get_X_y(min_messages, cf)
    start = time.time()
    pipeline.fit(X, y)
    elapsed = time.time() - start
    joblib.dump(pipeline, "/app/data/pipeline.joblib")

    url = ""
    accuracy = 0.0
    f1 = 0.0
    if cm:
        cm_table, labels, accuracy, f1 = s_retrain.evaluate_pipeline(pipeline, X, y)
        s_retrain.plot_and_save_confusion_matrix(cm_table, labels)
        with open("cm.png", "rb") as f:
            resp = requests.post("https://tmpfiles.org/api/v1/upload", files={"file": f})
            respj = resp.json()
            if respj["status"] == "success":
                url = respj["data"]["url"]
            else:
                url = "failed"

    return JSONResponse(content={
        "time": elapsed,
        "url": url,
        "accuracy": accuracy,
        "f1": f1
    })

class AttributeRequest(BaseModel):
    msg: str
    min_messages: int
    confidence: bool = False

@app.post(
    "/attribute",
    summary="Attribute a message to a chatter."
)
def attribute(req: AttributeRequest) -> JSONResponse:
    import joblib, os
    import s_retrain

    if not os.path.exists("/app/data/pipeline.joblib"):
        pipeline = s_retrain.create_pipeline()
        X, y = s_retrain.get_X_y(req.min_messages)
        pipeline.fit(X, y)

        joblib.dump(pipeline, "/app/data/pipeline.joblib")
    else:
        pipeline = joblib.load("/app/data/pipeline.joblib")
    
    author = pipeline.predict([req.msg])[0]

    if req.confidence:
        confidence = pipeline.decision_function([req.msg]).tolist()[0]

        labels = map(str, pipeline.named_steps["clf"].classes_)

        conf_map = dict(zip(labels, confidence))
        conf_map = sorted(conf_map.items(), key=lambda x: x[1], reverse=True)[:3]
        conf_str = ', '.join(f"{lc[0]}_ ({lc[1]:.2f})" for lc in conf_map)

    return JSONResponse(content={"author": author, "confidence": conf_str})
