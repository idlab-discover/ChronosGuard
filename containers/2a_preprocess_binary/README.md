# Preprocessing & Anomaly Detection API

This api combines the **Preprocessing API** and **Anomaly Detector** to classify a flow either as `Benign` or `Attack`. When an `Attack` is detected the flow is forwarded to the combined **Preprocessing & Multi-Class Classifier**.

## API Endpoints

| HTTP Method | Endpoint   | Description                             |
|-------------|------------|-----------------------------------------|
| POST        | `/predict` | Run the ML pipeline for a preprocessed flow.   |
| GET         |        `/` | Healthcheck                             |
| GET         |    `/docs` | OpenAPI documentation                   |

### Predict samples using the API

The API expects a HTTP POST request with a JSON body containing a list with the 67 features as `float` and an optional `timestamps` for the event time.

```` bash
curl --location --request POST 'http://localhost:8001/predict' \
--header 'Content-Type: application/json' \
--data-raw '{
    "event_timestamp": "2022-08-10T12:53:56+00:00",
    "features_orig": [6.0,3.0,2.0,0.0,12.0,0.0,6.0,6.0,6.0,0.0,0.0,0.0,0.0,0.0,4000000.0,666666.7,3.0,0.0,3.0,3.0,3.0,3.0,0.0,3.0,3.0,0.0,0.0,0.0,0.0,0.0,0.0,40.0,0.0,666666.7,0.0,6.0,6.0,6.0,0.0,0.0,0.0,0.0,0.0,0.0,1.0,0.0,0.0,0.0,9.0,6.0,0.0,2.0,12.0,0.0,0.0,506.0,-1.0,1.0,20.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0]
}'
````

## Environment variables

`MODEL_MULTI_CLASS_HOST`
: The host address of the `Multi-Class Classifier` in the following format: `http://<IP>:<PORT>`
**Default**: "http://multi_class_api:8002"

`MODEL_TAU_B`
: The used threshold on the anomaly score to differentiate `Benign` from `Attack`.
**Default**: -0.0002196942507948895

`MODEL_HTTPX_TIMEOUT`
: The http timeout used to call the next service in the chain.
**Default**: 60 (s

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

`docker build -t preprocessing_binary_api .`

## Run image

`docker run -it --rm -p8000:8000 preprocessing_binary_api`
