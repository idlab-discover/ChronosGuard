#!/usr/bin/env python3

# ./process_raw_results.py > process_raw_results_v2.log
# 
# This script processes the individual result csv's in BASE_DIR and generates following 
# files for further analysis:
# 1) concatenated detail: concatenates all 10 repetitions of a run into a single file with statistics per request
# 2) statistics detail: creates a single file with a row with statistics of each experiment (individual detail file)
# 3) aggregated statistics detail: creates a single more condensed file with statistics with a row per run (all 10 repetitions aggregated)

import numpy as np
import pandas as pd
import os
import glob
import math

BASE_DIR = "../../CNSM_DATA/v2"
NUM_USERS = [1, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100]
PERCENTILES = [.25, .5, .6, .7, .75, .8, .9, .95, .99]
FLOW_TYPES = ["Benign", "Attack", "Zero-Day"]
DETAILS_ENABLED = True
RESOURCES_ENABLED = True
TOPOLOGIES = ['cluster', 'edge-fog-cloud']
DEPLOYMENTS = ['1pod', '2pod', '3pod', '4pod']

def read_csv_detail(filename: str, verbose: bool = True) -> pd.DataFrame:
    if verbose:
        print(f"Reading file {filename}...")
    detail_dtypes= {
        "request_type": "category",
        "name": "category",
        "response_time_ms": "int64",
        "response_length": "int64",
        "num_of_users": "int64",
        "anomaly_score": "float64",
        "binary_prediction": "category",
        "multi_class_confidence": "float64",
        "multi_class_prediction": "category"
    }
    detail_dates_columns = ['event_timestamp', 'finished_timestamp', 
                          'timestamp_start', 'timestamp_end',
                          'processing_timestamp_start', 'processing_timestamp_end', 
                          'binary_timestamp_start', 'binary_timestamp_end', 
                          'multi_class_timestamp_start', 'multi_class_timestamp_end', 
                          'zero_day_timestamp_start', 'zero_day_timestamp_end']
    name_mapping = {
        'Benign': 'Benign',
        'Web Attack': 'Attack',
        'Brute Force': 'Attack',
        'Botnet': 'Attack',
        '(D)DOS': 'Attack',
        'Port Scan': 'Attack',
        'Unknown': 'Zero-Day'
    }

    df = pd.read_csv(filename, dtype=detail_dtypes)
    df[detail_dates_columns] = df[detail_dates_columns].apply(pd.to_datetime, format="%Y-%m-%dT%H:%M:%S.%f", errors='coerce')
    df["total_delay"] = df["finished_timestamp"] - df["event_timestamp"]
    df["flow_type"] = df["name"].map(name_mapping)
    df['flow_type'] = df.flow_type.astype('category')
    # return df[df["total_delay"].notna()]
    return df

def define_sorting_from_properties(properties):
    if properties[2] in ["ks", "qos"]:
        return properties[2]
    elif properties[3] in ["reverse", "alternate"]:
        return f"{properties[3]}-{properties[4]}"
    else:
        return properties[3]


if __name__ == "__main__":
    data_per_run = []
    data_per_container = []
    for topology in TOPOLOGIES:
        for deployment in DEPLOYMENTS:
            path = f"{BASE_DIR}/{topology}/{deployment}"
            if os.path.exists(path):
                for run in os.listdir(path):
                    to_merge = []
                    run_properties = run.split("_")
                    print(f"\n######### {run} #########")
                    
                    if RESOURCES_ENABLED:
                        for file in glob.glob(f"{path}/{run}/*_resources_*.csv"):
                            df = pd.read_csv(file, index_col=["step", "container"])
                            num_repetition = file.split('/')[-1].split('_')[0]

                            for num_users in NUM_USERS:
                                for container in df.index.unique(level='container'):
                                    data_per_container.append(dict({
                                        "topology": topology,
                                        "deployment": deployment,
                                        "sorting": f"{run_properties[2]}_{define_sorting_from_properties(run_properties)}",
                                        "scenario": run_properties[-1],
                                        "repetition": num_repetition,
                                        "num_users": num_users,
                                        "container": container,
                                    }, **df.loc[(math.floor(num_users/10), container)].to_dict()))

                    if DETAILS_ENABLED:
                        for file in glob.glob(f"{path}/{run}/*_detail_*.csv"):
                            df = read_csv_detail(file)
                            num_repetition = file.split('/')[-1].split('_')[0]
                            df["num_repetition"] = num_repetition
                            df['num_repetition'] = df.num_repetition.astype('category')
                            print(df.info())
                            to_merge.append(df)

                            for num_users in NUM_USERS:
                                for flow_type in FLOW_TYPES:
                                    data_per_run.append(dict({
                                        "topology": topology,
                                        "deployment": deployment,
                                        "sorting": f"{run_properties[2]}_{define_sorting_from_properties(run_properties)}",
                                        "scenario": run_properties[-1],
                                        "repetition": num_repetition,
                                        "flow_type": flow_type,
                                        "num_users": num_users,
                                        "throughput": len(df[(df["num_of_users"] == num_users) & (df["flow_type"] == flow_type)]) / 30, # 30s step duration
                                    }, **{"response_time_ms_" + str(key): val for key, val in df.loc[(df["num_of_users"] == num_users) & (df["flow_type"] == flow_type), "response_time_ms"].describe(PERCENTILES).items()}))

                        if not os.path.exists(f"{path}/{run}/merged"):
                            os.makedirs(f"{BASE_DIR}/{topology}/{deployment}/{run}/merged")
                        df_merged = pd.concat(to_merge)
                        df_merged['num_repetition'] = df_merged.num_repetition.astype('category')
                        # 1) Save merged files to disk
                        df_merged.to_parquet(f"{BASE_DIR}/{topology}/{deployment}/{run}/merged/detail.parquet", index=False)
                        print(f"\n######### MERGED {run} #########")
                        print(df_merged.info())
                
    # 2) Write file with statistics of each individual file as a single row to disk
    if DETAILS_ENABLED:
        df = pd.DataFrame(data_per_run).astype({
            "topology": "category", 
            "deployment": "category", 
            "sorting": "category", 
            "scenario": "category",
            "repetition": "category",
            "num_users": "category",
            "flow_type": "category"
        })
        df.to_parquet('./dataframe_graphs/detail_stat.parquet', index=False)
        df.to_csv('./dataframe_graphs/detail_stat.csv', index=False)
        print(f"\n######### STATISTICS DETAILS #########")
        print(df.info())
        
    if RESOURCES_ENABLED:
        df_resources = pd.DataFrame(data_per_container).astype({
            "topology": "category", 
            "deployment": "category", 
            "sorting": "category", 
            "scenario": "category",
            "repetition": "category",
            "num_users": "category",
            "container": "category"
        })
        df_resources.to_parquet('./dataframe_graphs/resources_stat.parquet', index=False)
        df_resources.to_csv('./dataframe_graphs/resources_stat.csv', index=False)
        print(f"\n######### STATISTICS RESOURCES #########")
        print(df_resources.info())
    
    # 3) Write file with aggregated statistics per run (all 10 repetitions combined) to disk
    if DETAILS_ENABLED:
        aggregations = { **{ k: ['mean', 'std'] for k in ['throughput', 'response_time_ms_count', 'response_time_ms_mean', 'response_time_ms_min', 'response_time_ms_max']}, **{ f"response_time_ms_{int(value*100)}%": ["mean", "std"] for value in PERCENTILES }}
        df_agg = df.groupby(["topology", "deployment", "sorting", "scenario", "num_users", "flow_type"], observed=True).aggregate(aggregations)
        df_agg.columns = ['_'.join(col) for col in df_agg.columns]
        df_agg.to_parquet('./dataframe_graphs/detail_agg_stat.parquet')
        df_agg.to_csv('./dataframe_graphs/detail_agg_stat.csv')
        print(f"\n######### AGGREGATED STATISTICS DETAILS #########")
        print(df_agg.info())
        
    if RESOURCES_ENABLED:
        aggregations = { f"{metric}_{stat}": ['mean', 'std'] for metric in ["cpu", "mem", "traffic_received", "traffic_transmitted"] for stat in ["count", "avg", "min", "max", "stddev"] }
        df_resources_agg = df_resources.groupby(["topology", "deployment", "sorting", "scenario", "num_users", "container"], observed=True).aggregate(aggregations)
        df_resources_agg.columns = ['_'.join(col) for col in df_resources_agg.columns]
        df_resources_agg.to_parquet('./dataframe_graphs/resources_agg_stat.parquet')
        df_resources_agg.to_csv('./dataframe_graphs/resources_agg_stat.csv')
        print(f"\n######### AGGREGATED STATISTICS RESOURCES #########")
        print(df_resources_agg.info())