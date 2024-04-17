# All-in-one API

The all-in-one api accepts a clean `flow` and an optional `event_timestamp`. The clean flow is first processed by the binary detector using the provided threshold (TAU_B). If the flow is flagged as an **Attack**, it is classified by the multi-class classifier to one of the known attack types with a certain confidence. Only if the confidence is below the supplied threshold (TAU_M) an additional step is performded to differentiate zero-day attacks from misclassified benign flows using a last threshold (TAU_U).

## API Endpoints

| HTTP Method | Endpoint   | Description                             |
|-------------|------------|-----------------------------------------|
| POST        | `/predict` | Run the ML pipeline for a clean flow.   |
| GET         |        `/` | Healthcheck                             |
| GET         |    `/docs` | OpenAPI documentation                   |

### Predict samples using the API

The API expects a HTTP POST request with a JSON body containing a list with the 67 features as `float` and a optional timestamp with the event time.

```` bash
curl --location --request POST 'http://localhost:8000/predict' \
--header 'Accept: application/json' \
--header 'Content-Type: application/json' \
--data-raw '{
    "event_timestamp": "2022-08-10T12:53:56+00:00",
    "features_orig": [6.0,3.0,2.0,0.0,12.0,0.0,6.0,6.0,6.0,0.0,0.0,0.0,0.0,0.0,4000000.0,666666.7,3.0,0.0,3.0,3.0,3.0,3.0,0.0,3.0,3.0,0.0,0.0,0.0,0.0,0.0,0.0,40.0,0.0,666666.7,0.0,6.0,6.0,6.0,0.0,0.0,0.0,0.0,0.0,0.0,1.0,0.0,0.0,0.0,9.0,6.0,0.0,2.0,12.0,0.0,0.0,506.0,-1.0,1.0,20.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0]
}'
````

## Environment variables

`MODEL_TAU_B`
: The used threshold on the anomaly score to differentiate `Benign` from `Attack`.
**Default**: -0.0002196942507948895

`MODEL_TAU_M`
: The used threshold on the confidence to classify a flow as a known attack or `Unknown`.
**Default**: 0.98

`MODEL_TAU_U`
: The used threshold on the anomaly score to differentiate `Benign` from true `Unknown`.
**Default**: 0.0040588613744241275

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

`docker build -t all_in_one_api .`

## Run image

`docker run -it --rm -p8000:8000 all_in_one_api`
