from kubernetes import client, config
import time
import requests
import pandas as pd
from typing import List, Dict, Set

from pandas import DataFrame


class PrometheusExporter:
    def __init__(self, prometheus_url, namespace="default") -> None:
        self.namespace = namespace
        self.prometheus_url = prometheus_url
        self.sleep = 0.2
        # Create Kubernetes Client configuration
        self.config = config.load_incluster_config()
        # Create Kubernetes Client
        self.v1 = client.CoreV1Api()

    def get_container_names(self) -> Set[str]:
        pods = self.v1.list_namespaced_pod(namespace=self.namespace)
        app_names = ["flowgenerator", "allinoneapi", "preprocessingallbinary", "multiclasszerodayapi", "preprocessingbinaryapi",
                     "preprocessingmulticlassapi", "zerodayapi", "preprocessingapi", "binaryapi", "multiclassapi"]
        container_names = set()
        for pod in pods.items:
            if (pod.metadata.labels.get("app")) and pod.metadata.labels["app"] in app_names:
                container_names.add(pod.metadata.labels["app"])
        return container_names

    def fetch_prom(self, query):
        try:
            response = requests.get(self.prometheus_url + '/api/v1/query',
                                    params={'query': query})

        except requests.exceptions.RequestException as e:
            print(e)
            print("Retrying in {}...".format(self.sleep))
            time.sleep(self.sleep)
            return self.fetch_prom(query)

        if response.json()['status'] != "success":
            print("Error processing the request: " + response.json()['status'])
            print("The Error is: " + response.json()['error'])
            print("Retrying in {}s...".format(self.sleep))
            time.sleep(self.sleep)
            return self.fetch_prom(query)

        result = response.json()['data']['result']
        return result

    # Info regarding the queries for prometheus: 
    # https://stackoverflow.com/questions/63347233/how-to-get-cpu-and-memory-usage-of-pod-in-percentage-using-promethus
    def export_metrics(self, timestamps: List) -> DataFrame:
        data = {}
        for name in self.get_container_names():
            for idx, timestamp in enumerate(timestamps):
                row = {**self.get_cpu_stat(name, timestamp), **self.get_mem_stat(name, timestamp),
                       **self.get_traffic_received_stat(name, timestamp),
                       **self.get_traffic_transmitted_stat(name, timestamp)}
                data[(name, idx)] = row
        return pd.DataFrame.from_dict(data, orient="index").rename_axis(["container", "step"])

    def get_prom_stat(self, base_query, metric, unit, format_value, statistics=None) -> Dict[str, float]:
        if statistics is None:
            statistics = ["avg", "min", "max", "stddev", "count"]
        result = {metric + "_unit": unit}
        for statistic in statistics:
            response = self.fetch_prom(statistic + base_query)
            if statistic != "count":
                result[metric + "_" + statistic] = format_value(response)
            else:
                result[metric + "_" + statistic] = response[0]['value'][1] if response else 0
        return result

    def get_cpu_stat(self, container_name, timestamp) -> Dict[str, float]:
        base_query = '(rate(container_cpu_usage_seconds_total{namespace=' \
                     '"' + self.namespace + '", container="' + container_name + '"}[30s] @' \
                     + str(timestamp) + ')) by (container)'
        # return as mCPU
        return self.get_prom_stat(base_query, "cpu", "mCPU",
                                  lambda response: float(response[0]['value'][1]) * 1000 if response else None)

    def get_mem_stat(self, container_name, timestamp) -> Dict[str, float]:
        base_query = '(avg_over_time(container_memory_working_set_bytes{namespace=' \
                     '"' + self.namespace + '", container="' + container_name + '"}[30s] @' \
                     + str(timestamp) + ')) by (container)'
        # return as MiB
        return self.get_prom_stat(base_query, "mem", "MiB",
                                  lambda response: float(response[0]['value'][1]) / 1000000 if response else None)

    def get_traffic_received_stat(self, container_name, timestamp) -> Dict[str, float]:
        base_query = '(rate(container_network_receive_bytes_total{namespace=' \
                     '"' + self.namespace + '", pod=~"' + container_name + '.*"}[30s] @' \
                     + str(timestamp) + ')) by (pod)'
        # return as KBit/s
        return self.get_prom_stat(base_query, "traffic_received", "KBit/s",
                                  lambda response: float(response[0]['value'][1]) / 1000 if response else None)

    def get_traffic_transmitted_stat(self, container_name, timestamp) -> Dict[str, float]:
        base_query = '(rate(container_network_transmit_bytes_total{namespace=' \
                     '"' + self.namespace + '", pod=~"' + container_name + '.*"}[30s] @' \
                     + str(timestamp) + ')) by (pod)'
        # return as KBit/s
        return self.get_prom_stat(base_query, "traffic_transmitted", "KBit/s",
                                  lambda response: float(response[0]['value'][1]) / 1000 if response else None)

