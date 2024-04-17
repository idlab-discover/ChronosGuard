import glob
import os
import pandas as pd


if __name__ == "__main__":
    # ['1pod', '2pod', '3pod', '4pod']
    if __name__ == "__main__":
        base_dir = "../experiments/edge-fog-cloud/with-generator-as-dependency/"
        for deployment in ['4pod']:
            for run in os.listdir(base_dir + deployment):
                df = pd.DataFrame()
                print(f"\n\n######### {run} #########\n")
                for file in glob.glob(f"{base_dir}{deployment}/{run}/*_detail_*.csv"):
                    df_temp = pd.read_csv(file)
                    #if deployment == 'onlineboutique' or deployment == 'teastore':
                        #print(df_temp.info())
                        #df_temp.columns = ['request_type', 'name', 'response_time_ms', 'response_length', 'timestamp', 'num_of_users']

                    df = pd.concat([df, df_temp])

                #print(df.describe())
                #print(df.list())
                df.to_csv(base_dir + deployment + '/' + run + '/' + run + '_merged.csv')

