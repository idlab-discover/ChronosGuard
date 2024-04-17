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

BINARY_HOST = os.environ.get("MODEL_BINARY_HOST", default="http://binary_api:8001")
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


class CleanFlow(BaseModel):
    event_timestamp: datetime = None
    processing_timestamp_start: datetime = None
    features_orig: conlist(float, min_items=67, max_items=67)

    @validator("processing_timestamp_start", always=True)
    def set_processing_timestamp_start(cls, value):
        return datetime.now()


class ProcessedFlow(BaseModel):
    event_timestamp: datetime = None
    processing_timestamp_start: datetime = None
    processing_timestamp_end: datetime = None
    features_1: conlist(float, min_items=67, max_items=67)
    features_2: conlist(float, min_items=67, max_items=67)

    @validator("processing_timestamp_end", always=True)
    def set_processing_timestamp_end(cls, value):
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
    anomaly_score: float = None
    binary_prediction: BinaryPrediction = None
    multi_class_confidence: float = None
    multi_class_prediction: MultiClassPrediction = None

    @validator("processing_timestamp_end", always=True)
    def set_processing_timestamp_end(cls, value):
        return datetime.now()


@app.on_event("startup")
def load_scalers():
    global scaler_1, scaler_2
    with open(r"scalers/stage1_ocsvm_scaler.p", "rb") as file_1:
        scaler_1 = pickle.load(file_1)
    with open(r"scalers/stage2_rf_scaler.p", "rb") as file_2:
        scaler_2 = pickle.load(file_2)


@app.post("/predict", response_model=PredictedFlow, response_model_exclude_none=True)
async def predict(flow: CleanFlow):
    feature_arr = np.array(flow.features_orig).reshape(1, -1)
    processed_flow = ProcessedFlow(
        event_timestamp=flow.event_timestamp,
        processing_timestamp_start=flow.processing_timestamp_start,
        features_1=scaler_1.transform(feature_arr)[0].tolist(),
        features_2=scaler_2.transform(feature_arr)[0].tolist()
    )
    async with httpx.AsyncClient(timeout=HTTPX_TIMEOUT) as client:
        response = await client.post(BINARY_HOST + "/predict", json=jsonable_encoder(processed_flow))
    return response.json()


@app.get("/")
async def health():
    return "OK"
