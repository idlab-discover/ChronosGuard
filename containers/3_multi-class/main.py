from fastapi import FastAPI
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel, conlist, validator
from datetime import datetime
import pickle
import numpy as np
from enum import Enum
import os
import httpx

app = FastAPI()

TAU_M = float(os.environ.get("MODEL_TAU_M", default=0.98))
ZERO_DAY_HOST = os.environ.get("MODEL_ZERO_DAY_HOST", default="http://zero_day_api:8002")
HTTPX_TIMEOUT = int(os.environ.get("MODEL_HTTPX_TIMEOUT", default=60))


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


class DetectedFlow(BaseModel):
    event_timestamp: datetime = None
    processing_timestamp_start: datetime = None
    processing_timestamp_end: datetime = None
    binary_timestamp_start: datetime = None
    binary_timestamp_end: datetime = None
    multi_class_timestamp_start: datetime = None
    anomaly_score: float
    binary_prediction: BinaryPrediction
    features_2: conlist(float, min_items=67, max_items=67)

    @validator("multi_class_timestamp_start", always=True)
    def set_multi_class_timestamp_start(cls, value):
        return datetime.now()


class PredictedFlow(BaseModel):
    event_timestamp: datetime = None
    processing_timestamp_start: datetime = None
    processing_timestamp_end: datetime = None
    binary_timestamp_start: datetime = None
    binary_timestamp_end: datetime = None
    multi_class_timestamp_start: datetime = None
    multi_class_timestamp_end: datetime = None
    zero_day_timestamp_start: datetime = None
    zero_day_timestamp_end: datetime = None
    anomaly_score: float
    binary_prediction: BinaryPrediction
    multi_class_confidence: float
    multi_class_prediction: MultiClassPrediction

    @validator("multi_class_timestamp_end", always=True)
    def set_multi_class_timestamp_end(cls, value):
        return datetime.now()


@app.on_event("startup")
def load_scalers():
    global model
    with open(r"models/stage2_rf_model.p", "rb") as file:
        model = pickle.load(file)


@app.post("/predict", response_model=PredictedFlow, response_model_exclude_none=True)
async def predict(flow: DetectedFlow):
    feature_arr = np.array(flow.features_2).reshape(1, -1)
    proba = model.predict_proba(feature_arr)[0]
    prediction = model.classes_[np.argmax(proba)] if np.max(proba) > TAU_M else MultiClassPrediction.UNKOWN
    classfied_flow = PredictedFlow(
        event_timestamp=flow.event_timestamp,
        processing_timestamp_start=flow.processing_timestamp_start,
        processing_timestamp_end=flow.processing_timestamp_end,
        binary_timestamp_start=flow.binary_timestamp_start,
        binary_timestamp_end=flow.binary_timestamp_end,
        multi_class_timestamp_start=flow.multi_class_timestamp_start,
        anomaly_score=flow.anomaly_score,
        binary_prediction=flow.binary_prediction,
        multi_class_confidence=np.max(proba),
        multi_class_prediction=prediction
    )
    if prediction == MultiClassPrediction.UNKOWN:
        async with httpx.AsyncClient(timeout=HTTPX_TIMEOUT) as client:
            response = await client.post(ZERO_DAY_HOST + "/predict", json=jsonable_encoder(classfied_flow))
        return response.json()
    else:
        return classfied_flow


@app.get("/")
async def health():
    return "OK"
