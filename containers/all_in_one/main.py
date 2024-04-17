from fastapi import FastAPI
from pydantic import BaseModel, conlist, validator
from datetime import datetime
import pickle
import numpy as np
from enum import Enum
import os

app = FastAPI()

TAU_B = float(os.environ.get("MODEL_TAU_B", default=-0.0002196942507948895))
TAU_M = float(os.environ.get("MODEL_TAU_M", default=0.98))
TAU_U = float(os.environ.get("MODEL_TAU_U", default=0.0040588613744241275))


class BinaryPrediction(str, Enum):
    BENIGN = 'Benign'
    ATTACK = 'Attack'


class MultiClassPrediction(str, Enum):
    DDOS = '(D)DOS'
    PORT_SCAN = 'Port Scan'
    BOTNET = 'Botnet'
    BRUTE_FORCE = 'Brute Force'
    WEB_ATTACK = 'Web Attack'
    UNKOWN = 'Unknown'
    BENIGN = 'Benign'


class CleanFlow(BaseModel):
    event_timestamp: datetime = None
    timestamp_start: datetime = None
    features_orig: conlist(float, min_items=67, max_items=67)

    @validator("timestamp_start", always=True)
    def set_timestamp_start(cls, value):
        return datetime.now()


class PredictedFlow(BaseModel):
    event_timestamp: datetime = None
    timestamp_start: datetime = None
    timestamp_end: datetime = None
    anomaly_score: float
    binary_prediction: BinaryPrediction
    multi_class_confidence: float = None
    multi_class_prediction: MultiClassPrediction = None

    @validator("timestamp_end", always=True)
    def set_timestamp_end(cls, value):
        return datetime.now()


@app.on_event("startup")
def load_scalers():
    global stage1, stage2
    with open(r"models/stage1_ocsvm.p", "rb") as file_1:
        stage1 = pickle.load(file_1)
    with open(r"models/stage2_rf.p", "rb") as file_2:
        stage2 = pickle.load(file_2)


@app.post("/predict", response_model=PredictedFlow, response_model_exclude_none=True)
async def predict(flow: CleanFlow):
    feature_arr = np.array(flow.features_orig).reshape(1, -1)
    anomaly_score = -stage1.decision_function(feature_arr)[0]
    prediction_1 = BinaryPrediction.BENIGN if anomaly_score < TAU_B else BinaryPrediction.ATTACK
    prediction_2, proba = None, None

    if prediction_1 == BinaryPrediction.ATTACK:
        proba = stage2.predict_proba(feature_arr)[0]
        prediction_2 = stage2.classes_[np.argmax(proba)] if np.max(proba) > TAU_M else MultiClassPrediction.UNKOWN

        if prediction_2 == MultiClassPrediction.UNKOWN:
            prediction_2 = MultiClassPrediction.BENIGN if anomaly_score < TAU_U else MultiClassPrediction.UNKOWN

    return PredictedFlow(
        event_timestamp=flow.event_timestamp,
        timestamp_start=flow.timestamp_start,
        anomaly_score=anomaly_score,
        binary_prediction=prediction_1,
        multi_class_confidence=np.max(proba),
        multi_class_prediction=prediction_2
    )


@app.get("/")
async def health():
    return "OK"
