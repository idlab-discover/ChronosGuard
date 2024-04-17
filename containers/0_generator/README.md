# Flow Generator

Locust is used to simulate attackers and benign users. The benign user posts only benign flows to the ML-pipeline, while the attacker generates flows for 6 different types of attacks. Initially a file containing the flows from which the users randomly sample, is loaded. Below you find the number of unique samples per flow type used in the simulation.

| Flow Type   | #Samples |
|-------------|---------:|
| Benign      |    56468 |
| (D)DOS      |      584 |
| Port Scan   |      584 |
| Botnet      |      584 |
| Brute Force |      584 |
| Web Attack  |      584 |
| Unknown     |       47 |

## Custom Load Shape
The load test is executed using a stepped load starting from 1 up to 100 users. Each step takes 30 seconds and increases the number of users with 10 using a spawn-rate of 1 user per second.

## Environment Variables

`BENIGN_WEIGHT`, `ATTACKER_WEIGHT`
: Control the ratio between benign users and attackers when spawing multiple users.
**Default**: Benign (4) - Attacker (1)

`USER_THROUGHPUT`
: Maximum number of requests per second per user (-1 to sent new request after previous finished).
**Default**: 1

`ATTACKER_UNKNOWN_RATIO`
: Ratio known vs unknown flows posted by an attacker.
**Default**: 2 (Double as many known attacks vs unknown attacks)

`DETAIL_STAT_DIRECTORY`
: Directory to save CSV with the details of individual requests
**Default**: '/data/results/'

`CSV_STATS_INTERVAL_SEC`
: Interval for how frequently the locust CSV file is written if this option is configured
**Default**: 10 sec

`PROMETHEUS_URL`
: The URL to the Prometheus server for fetching metrics
**Default**: http://localhost:9090

`KUBERNETES_NAMESPACE`
: The namespace to use when querying the Kubernetes API server
**Default**: 'Default'

### Locust Environment Variables

`LOCUST_HOST`
: Host to target in the simulation in the following format: `http://<IP>:<PORT>`

`LOCUST_CSV`
: Store current request stats to files in CSV format. Setting this option will generate three files using `CSV_PREFIX`.

`LOCUST_CSV_FULL_HISTORY`
: Store each stats entry in CSV format to _stats_history.csv file. You must also specify the ‘–csv’ argument to enable this.

For all available configuration options: see [Locust Configuration](https://docs.locust.io/en/stable/configuration.html#all-available-configuration-options).

## Build Image

`docker build -t flow_generator .`

## Run Image

### Web Mode

`docker run -it --rm -p8089:8089 flow_generator -H http://<IP>:<PORT>`

Browse to the webpage at <http://localhost:8089> to start the locust flow generator.

### Headless Mode

`docker run -it --rm -p8089:8089 flow_generator --headless --users 5 --spawn-rate 1 -H http://<IP>:<PORT>`
