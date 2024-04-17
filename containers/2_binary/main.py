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

TAU_B = float(os.environ.get("MODEL_TAU_B", default=-0.0002196942507948895))
MULTI_CLASS_HOST = os.environ.get("MODEL_MULTI_CLASS_HOST", default="http://multi_class_api:8002")
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


class ProcessedFlow(BaseModel):
    event_timestamp: datetime = None
    processing_timestamp_start: datetime = None
    processing_timestamp_end: datetime = None
    binary_timestamp_start: datetime = None
    features_1: conlist(float, min_items=67, max_items=67)
    features_2: conlist(float, min_items=67, max_items=67)

    @validator("binary_timestamp_start", always=True)
    def set_binary_timestamp_start(cls, value):
        return datetime.now()


class DetectedFlow(BaseModel):
    event_timestamp: datetime = None
    processing_timestamp_start: datetime = None
    processing_timestamp_end: datetime = None
    binary_timestamp_start: datetime = None
    binary_timestamp_end: datetime = None
    anomaly_score: float
    binary_prediction: BinaryPrediction
    features_2: conlist(float, min_items=67, max_items=67)

    @validator("binary_timestamp_end", always=True)
    def set_binary_timestamp_end(cls, value):
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
    multi_class_confidence: float = None
    multi_class_prediction: MultiClassPrediction = None

    @validator("binary_timestamp_end", always=True)
    def set_binary_timestamp_end(cls, value):
        return datetime.now()


@app.on_event("startup")
def load_scalers():
    global model
    with open(r"models/stage1_ocsvm_model.p", "rb") as file:
        model = pickle.load(file)


@app.post("/predict", response_model=PredictedFlow, response_model_exclude_none=True)
async def predict(flow: ProcessedFlow):
    feature_arr = np.array(flow.features_1).reshape(1, -1)
    # invert sign to act as anomaly score
    anomaly_score = -model.decision_function(feature_arr)[0]
    prediction = BinaryPrediction.BENIGN if anomaly_score < TAU_B else BinaryPrediction.ATTACK
    detected_flow = DetectedFlow(
        event_timestamp=flow.event_timestamp,
        processing_timestamp_start=flow.processing_timestamp_start,
        processing_timestamp_end=flow.processing_timestamp_end,
        binary_timestamp_start=flow.binary_timestamp_start,
        anomaly_score=anomaly_score,
        binary_prediction=prediction,
        features_2=flow.features_2
    )
    if prediction == BinaryPrediction.ATTACK:
        async with httpx.AsyncClient(timeout=HTTPX_TIMEOUT) as client:
            response = await client.post(MULTI_CLASS_HOST + "/predict", json=jsonable_encoder(detected_flow))
        return response.json()
    else:
        return detected_flow


@app.get("/")
async def health():
    return "OK"
