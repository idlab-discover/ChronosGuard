from fastapi import FastAPI
from pydantic import BaseModel, conlist, validator
from datetime import datetime
import pickle
import numpy as np
from enum import Enum
import os

app = FastAPI()

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


class ClassifiedFlow(BaseModel):
    event_timestamp: datetime = None
    processing_timestamp_start: datetime = None
    processing_timestamp_end: datetime = None
    binary_timestamp_start: datetime = None
    binary_timestamp_end: datetime = None
    multi_class_timestamp_start: datetime = None
    multi_class_timestamp_end: datetime = None
    zero_day_timestamp_start: datetime = None
    anomaly_score: float
    binary_prediction: BinaryPrediction
    multi_class_confidence: float
    multi_class_prediction: MultiClassPrediction

    @validator("zero_day_timestamp_start", always=True)
    def set_zero_day_timestamp_start(cls, value):
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

    @validator("zero_day_timestamp_end", always=True)
    def set_zero_day_timestamp_end(cls, value):
        return datetime.now()


@app.post("/predict", response_model=PredictedFlow, response_model_exclude_none=True)
async def predict(flow: ClassifiedFlow):
    prediction = MultiClassPrediction.BENIGN if flow.anomaly_score < TAU_U else MultiClassPrediction.UNKOWN
    return PredictedFlow(
        event_timestamp=flow.event_timestamp,
        processing_timestamp_start=flow.processing_timestamp_start,
        processing_timestamp_end=flow.processing_timestamp_end,
        binary_timestamp_start=flow.binary_timestamp_start,
        binary_timestamp_end=flow.binary_timestamp_end,
        multi_class_timestamp_start=flow.multi_class_timestamp_start,
        multi_class_timestamp_end=flow.multi_class_timestamp_end,
        zero_day_timestamp_start=flow.zero_day_timestamp_start,
        anomaly_score=flow.anomaly_score,
        binary_prediction=flow.binary_prediction,
        multi_class_confidence=flow.multi_class_confidence,
        multi_class_prediction=prediction
    )


@app.get("/")
async def health():
    return "OK"
