# Combined Multi-Class Classifier & Zero-day API

The combined multi-class classifier and zero-day api builds further with the result of the **Anomaly Detector API** and classifies a flow as one of the known attack classes or `Unkown` if the confidence is not high enough. When a flow is classified as `Unknown` a second threshold on the anomaly score is used to correct previously detected anomalous flows with low confidence to a known attack either as `Benign` or as a true `Unknown` attack.

## API Endpoints

| HTTP Method | Endpoint   | Description                             |
|-------------|------------|-----------------------------------------|
| POST        | `/predict` | Run the ML pipeline for a detected flow.   |
| GET         |        `/` | Healthcheck                             |
| GET         |    `/docs` | OpenAPI documentation                   |

### Predict samples using the API

The API expects a HTTP POST request with a JSON body containing a list with the scaled 67 features as `float` and optional `timestamps` for the event time and processing timestamps.

```` bash
curl --location --request POST 'http://localhost:8002/predict' \
--header 'Content-Type: application/json' \
--data-raw '{
    "event_timestamp": "2022-08-10T12:53:56+00:00",
    "processing_timestamp_start": "2022-08-10T12:53:56.527624",
    "processing_timestamp_end": "2022-08-10T12:53:56.639806",
    "binary_timestamp_start": "2022-08-11T16:36:29.458953",
    "binary_timestamp_end": "2022-08-11T16:36:29.460145",
    "anomaly_score": 5.986074868310001e-05,
    "binary_prediction": "Attack",
    "features_2": [ -5.199337582605575, -2.651731984747387, -0.4878930103874749, -5.199337582605575, 0.06151263655249807, -5.199337582605575, 0.005018295886876199, 1.6113332511692402, 0.010036718154949801, -5.199337582605575, -5.199337582605575, -5.199337582605575, -5.199337582605575, -5.199337582605575, 2.696511062787801, 2.7474533189644763, -2.651731984747387, -5.199337582605575, -2.651731984747387, -0.8901723046231351, -0.563955207252462, -0.563955207252462, -5.199337582605575, -0.563955207252462, -0.23035256480696298, -5.199337582605575, -5.199337582605575, -5.199337582605575, -5.199337582605575, -5.199337582605575, -5.199337582605575, -0.7168389528871792, -5.199337582605575, 2.9348890362047704, -5.199337582605575, 1.634746967913314, -0.3110590177663439, 0.01881964145130391, -5.199337582605575, -5.199337582605575, -5.199337582605575, -5.199337582605575, -5.199337582605575, -5.199337582605575, 5.19933758270342, -5.199337582605575, -5.199337582605575, -5.199337582605575, 0.05522908732975672, 0.010036718154949801, -5.199337582605575, -0.4878930103874749, 0.06151263655249807, -5.199337582605575, -5.199337582605575, -0.6206232306893864, -5.199337582605575, 0.236798889881903, -5.199337582605575, -5.199337582605575, -5.199337582605575, -5.199337582605575, -5.199337582605575, -5.199337582605575, -5.199337582605575, -5.199337582605575, -5.199337582605575 ]
}'
````

## Environment variables

`MODEL_TAU_M`
: The used threshold on the confidence to classify a flow as a known attack or `Unknown`.
**Default**: 0.98

`MODEL_TAU_U`
: The used threshold on the anomaly score to differentiate `Benign` from true `Unknown`.
**Default**: 0.0040588613744241275

`MODEL_HTTPX_TIMEOUT`
: The http timeout used to call the next service in the chain.
**Default**: 60 (s)

### Uvicorn Environment Variables

Uvicorn is used as underlying ASGI web server and can be configured using environment variables with the prefix `UVICORN_`.

`UVICORN_HOST`
: Bind socket to this host. IPv6 addresses are supported, for example `::`
**Default**: "127.0.0.1"

`UVICORN_PORT`
: Bind socket with this port.
**Default**: "8000"

`UVICORN_WORKERS`
: Use multiple worker processes.
**Default**: "1"

For all available configuration options: see [Uvicorn Configuration](https://www.uvicorn.org/settings/).

## Build image

`docker build -t multi_class_api .`

## Run image

`docker run -it --rm -p8000:8000 multi_class_api`
