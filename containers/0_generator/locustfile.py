from locust import task, events, constant_throughput, LoadTestShape, constant
from locust.contrib.fasthttp import FastHttpUser

import pandas as pd
import numpy as np
from datetime import datetime
import os
import logging
import locust.stats
from locust.stats import StatsCSVFileWriter
from locust.html import get_html_report
import gevent
import math
from resource_statistics import PrometheusExporter

flows = {}
custom_config = {
    "benign_weight": int(os.environ.get("BENIGN_WEIGHT", default=4)),
    "attacker_weight": int(os.environ.get("ATTACKER_WEIGHT", default=1)),
    "user_throughput": int(os.environ.get("USER_THROUGHPUT", default=-1)),
    "attack_unknown_ratio": int(os.environ.get("ATTACKER_UNKNOWN_RATIO", default=2)),
    "detail_stat_directory": os.environ.get("DETAIL_STAT_DIRECTORY", default="data/results/"),
    "csv_stats_interval_sec": os.environ.get("CSV_STATS_INTERVAL_SEC", default=10),
    "prometheus_url": os.environ.get("PROMETHEUS_URL", default="http://localhost:9090"),
    "kubernetes_namespace": os.environ.get("KUBERNETES_NAMESPACE", default="default"),
}
stat_file = None
csv_file_greenlet = None
run_csv_directory = None
run_number = None
run_start_timestamp = None
locust.stats.CSV_STATS_INTERVAL_SEC = custom_config["csv_stats_interval_sec"]


@events.init_command_line_parser.add_listener
def _(parser):
    parser.add_argument("--run-csv-directory", include_in_web_ui=True, default="Cluster_Diktyo_cycle_initial_1pod",
                        help="Directory for csv output")
    parser.add_argument("--run-number", include_in_web_ui=True, default="01", help="Number of this run")


# Load flows for users to send
@events.init.add_listener
def on_locust_init(environment, runner, web_ui, **kwargs):
    global env
    env = environment
    data = pd.read_csv("data/test.csv")
    y = data["Y"].replace(["Heartbleed", "Infiltration"], "Unknown")
    x = data.drop(columns=['Y'])
    for flow_type in np.unique(y):
        flows[flow_type] = x[y == flow_type]


# Log detailed statistics from on finish individual request
@events.request.add_listener
def write_response(request_type, name, response_time, response_length, response, exception, **kwargs):
    json_response = response.json()
    stat_file.write(
        request_type + "," +
        name + "," +
        str(response_time) + "," +
        str(response_length) + "," +
        str(json_response.get("event_timestamp", "")) + "," +
        str(datetime.now().isoformat()) + "," +
        str(env.runner.user_count) + "," +
        str(json_response.get("timestamp_start", "")) + "," +
        str(json_response.get("timestamp_end", "")) + "," +
        str(json_response.get("processing_timestamp_start", "")) + "," +
        str(json_response.get("processing_timestamp_end", "")) + "," +
        str(json_response.get("binary_timestamp_start", "")) + "," +
        str(json_response.get("binary_timestamp_end", "")) + "," +
        str(json_response.get("multi_class_timestamp_start", "")) + "," +
        str(json_response.get("multi_class_timestamp_end", "")) + "," +
        str(json_response.get("zero_day_timestamp_start", "")) + "," +
        str(json_response.get("zero_day_timestamp_end", "")) + "," +
        str(json_response.get("anomaly_score", "")) + "," +
        str(json_response.get("binary_prediction", "")) + "," +
        str(json_response.get("multi_class_confidence", "")) + "," +
        str(json_response.get("multi_class_prediction", "")) + "\n"
    )


# Open new CSV and write headers to log detailed statistics from individual requests
def open_new_detail_stat_file():
    global stat_file
    logging.info(
        "Creating new detail CSV file in direcotry: " + custom_config["detail_stat_directory"] + run_csv_directory)
    if not os.path.exists(custom_config["detail_stat_directory"] + run_csv_directory):
        os.makedirs(custom_config["detail_stat_directory"] + run_csv_directory)
    stat_file = open(custom_config[
                         "detail_stat_directory"] + run_csv_directory + "/" + run_number + "_detail_" + datetime.now().strftime(
        "%d%m%Y-%H%M%S") + '.csv', 'w')
    stat_file.write(
        "request_type," +
        "name," +
        "response_time_ms," +
        "response_length," +
        "event_timestamp," +
        "finished_timestamp," +
        "num_of_users," +
        "timestamp_start," +
        "timestamp_end," +	
        "processing_timestamp_start," +
        "processing_timestamp_end," +
        "binary_timestamp_start," +
        "binary_timestamp_end," +
        "multi_class_timestamp_start," +
        "multi_class_timestamp_end," +
        "zero_day_timestamp_start," +
        "zero_day_timestamp_end," +
        "anomaly_score," +
        "binary_prediction," +
        "multi_class_confidence," +
        "multi_class_prediction\n"
    )


@events.reset_stats.add_listener
def reset_stat_file(**kwargs):
    global stat_file
    stat_file.close()
    open_new_detail_stat_file()


@events.test_start.add_listener
def reset_stat_file_2(environment, **kwargs):
    global stat_file
    global run_csv_directory
    global run_number
    global csv_file_greenlet
    # Read run parameters from web ui
    run_csv_directory = environment.parsed_options.run_csv_directory
    run_number = environment.parsed_options.run_number

    # Open new custom detail CSV
    open_new_detail_stat_file()

    # Create New Locust CSV Files
    csv_writer = StatsCSVFileWriter(
        env, locust.stats.PERCENTILES_TO_REPORT,
        custom_config["detail_stat_directory"] + run_csv_directory + "/" + run_number, True
    )
    env.web_ui.stats_csv_writer = csv_writer

    # Kill CSV writer from previous run
    if csv_file_greenlet is not None:
        csv_file_greenlet.kill(block=False)
    csv_file_greenlet = gevent.spawn(csv_writer.stats_writer)


@events.spawning_complete.add_listener
def spawning_complete(user_count, **kwargs):
    global run_start_timestamp
    if user_count == 1:
        # Set run_start_timestamp equal to seconds since epoch
        run_start_timestamp = math.ceil(datetime.now().timestamp())
        logging.info("Run started @ " + str(run_start_timestamp))


@events.quitting.add_listener
def close_stat_file(environment, **kwargs):
    if not stat_file.closed:
        stat_file.close()


@events.test_stop.add_listener
def close_stat_file_2(environment, **kwargs):
    stat_file.close()
    logging.info("Creating HTML report")
    html_report = get_html_report(env, show_download_link=False)
    with open(custom_config[
                  "detail_stat_directory"] + run_csv_directory + "/" + run_number + "_report_" + datetime.now().strftime(
        "%d%m%Y-%H%M%S") + ".html", "w", encoding="utf-8") as file:
        file.write(html_report)
    # Reset users dispatcher
    env.runner._users_dispatcher = None
    # Export the resource metrics from prometheus
    logging.info("Exporting resource metrics from prometheus")
    prom_exporter = PrometheusExporter(custom_config["prometheus_url"], custom_config["kubernetes_namespace"])
    timestamps = [(run_start_timestamp + 30) + 40 * i for i in range(0, 11)]
    df_resources = prom_exporter.export_metrics(timestamps)
    df_resources.to_csv(custom_config["detail_stat_directory"] + run_csv_directory + "/" + run_number + "_resources_" +
                        datetime.now().strftime("%d%m%Y-%H%M%S") + ".csv")


# Used by the users to send a flow to the IDS API
def execute_post_flow(user, flow_type):
    user.client.post(
        "/predict",
        name=flow_type,
        json={
            "event_timestamp": datetime.now().isoformat(),
            "features_orig": flows[flow_type].sample().values[0].tolist()
        }
    )


# Define 2 locust users (Benign, Attacker) sending extracted features from a flow with constant throughput
class BenignUser(FastHttpUser):
    weight = custom_config["benign_weight"]
    wait_time = constant_throughput(custom_config["user_throughput"]) if custom_config["user_throughput"] > 0 else constant(0)

    @task
    def benign_behaviour(self):
        execute_post_flow(self, "Benign")


class Attacker(FastHttpUser):
    weight = custom_config["attacker_weight"]
    wait_time = constant_throughput(custom_config["user_throughput"]) if custom_config["user_throughput"] > 0 else constant(0)

    @task(custom_config["attack_unknown_ratio"])
    def dos_attack(self):
        execute_post_flow(self, "(D)DOS")

    @task(custom_config["attack_unknown_ratio"])
    def portscan_attack(self):
        execute_post_flow(self, "Port Scan")

    @task(custom_config["attack_unknown_ratio"])
    def botnet_attack(self):
        execute_post_flow(self, "Botnet")

    @task(custom_config["attack_unknown_ratio"])
    def bruteforce_attack(self):
        execute_post_flow(self, "Brute Force")

    @task(custom_config["attack_unknown_ratio"])
    def web_attack(self):
        execute_post_flow(self, "Web Attack")

    @task
    def unknown_attack(self):
        execute_post_flow(self, "Unknown")


# CustomShape for load test
class StagesShape(LoadTestShape):
    """
    A simply load test shape class that has different user and spawn_rate at
    different stages.
    Keyword arguments:
        stages -- A list of dicts, each representing a stage with the following keys:
            duration -- When this many seconds pass the test is advanced to the next stage
            users -- Total user count
            spawn_rate -- Number of users to start/stop per second
            stop -- A boolean that can stop that test at a specific stage
        stop_at_end -- Can be set to stop once all stages have run.
    """

    stages = [
        {"duration": 30, "users": 1, "spawn_rate": 1},
        {"duration": 70, "users": 10, "spawn_rate": 1},
        {"duration": 110, "users": 20, "spawn_rate": 1},
        {"duration": 150, "users": 30, "spawn_rate": 1},
        {"duration": 190, "users": 40, "spawn_rate": 1},
        {"duration": 230, "users": 50, "spawn_rate": 1},
        {"duration": 270, "users": 60, "spawn_rate": 1},
        {"duration": 310, "users": 70, "spawn_rate": 1},
        {"duration": 350, "users": 80, "spawn_rate": 1},
        {"duration": 390, "users": 90, "spawn_rate": 1},
        {"duration": 430, "users": 100, "spawn_rate": 1},
    ]

    def tick(self):
        run_time = self.get_run_time()

        for stage in self.stages:
            if run_time < stage["duration"]:
                tick_data = (stage["users"], stage["spawn_rate"])
                return tick_data

        return None
