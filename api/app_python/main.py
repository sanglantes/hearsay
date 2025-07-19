from urllib import request
from fastapi import FastAPI
import requests

app = FastAPI()

@app.get("/ping")
def pong() -> dict[str, str]:
    return {"ping": "pong"}

@app.get("/readability")
def readability(nick: str) -> dict[str, float]:
    import s_readability as s_readability
    return {"score": s_readability.flesch_score(nick)}

@app.get("/retrain")
def retrain(varg: str) -> dict[str, str] | None:
    import s_retrain
    import joblib
    import time

    url = ''
    acc = 0
    cm = False
    if varg == "--cm":
        cm = True

    pipeline = s_retrain.create_pipeline()
    joblib.dump(pipeline, "pipeline.joblib")
    
    X, y = s_retrain.get_X_y()
    t1 = time.time()
    pipeline.fit(X, y)
    t_delta = time.time() - t1


    if cm:
        cm_table, labels, acc = s_retrain.evaluate_pipeline(pipeline, X, y)
        s_retrain.plot_and_save_confusion_matrix(cm_table, labels)

        with open("confusion_matrix.png", "rb") as f:
            files = {"file": f}
            response = requests.post("https://api.put.re/upload", files=files)
            if response.json()["status"] == "success":
                url = response.json()["data"]["link"]
    
    return {"time": t_delta, "url": url, "accuracy": acc}