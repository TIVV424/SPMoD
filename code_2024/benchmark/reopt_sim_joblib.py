#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Jan 21 2024

Author: Ruiting Wang
"""

from reopt_24 import MaxMatchOnl
from multiprocessing import cpu_count
from joblib import Parallel, delayed
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import os
import time
import sys

driver = pd.read_csv("Database//NYC_trip//driver_260_2000.csv", index_col=0)
order = pd.read_csv("Database//NYC_trip//order_clean_260.csv", index_col=0)
area = np.load("Database//NYC_area//NY_area.npy")
df_MTC = pd.read_csv("Database//network8_10//network_metrics_MTC.csv", index_col=0)
df_MTC = df_MTC[df_MTC["time"] == "8-10am"]
df_MTC.reset_index(drop=True, inplace=True)


seed = 0
void = 30
weight_on = "T"
timestr = time.strftime("%Y%m%d-%H%M%S")
if not os.path.exists(os.path.join("Database//online_result", timestr)):
    os.makedirs(os.path.join("Database//online_result", timestr))

# f = open("Database//online_result//%s//log.txt" % (timestr), "w")
# sys.stdout = f

order["call_time"] = pd.to_datetime(order["call_time"])
order["end_time"] = pd.to_datetime(order["end_time"])
start_time = pd.to_datetime("2022-06-01 08:00:00 AM")
end_time = pd.to_datetime("2022-06-01 10:00:00 AM")
order_pick = order[(order["call_time"] > start_time) & (order["call_time"] <= end_time)]
order_pick = order_pick[["sid", "call_time", "eid", "end_time"]]
order_pick.reset_index(drop=True, inplace=True)
order_pick["MTC"] = df_MTC["MTC"]
assert len(order_pick) == len(df_MTC)
assert order_pick.isna().sum().sum() == 0
## Change this to 1000 for testing
order_pick = order_pick.values[:1000]
print(order_pick.shape)
# print("Number of orders between 8-10 am,", len(order_pick))


driver_pick = pd.read_csv("Database//NYC_trip//driver_with_time.csv")
driver_pick["time"] = pd.to_datetime(driver_pick["time"])
# print("Number of drivers between 8-10 am,", len(driver_pick))
driver_pick = driver_pick.values

para_df = pd.read_csv("experiments//para_log.csv")

match_result = []
time_spent = []


def run_online_match(ind):
    opt_interval = para_df["opt"][ind]
    roll_interval = para_df["roll"][ind]
    locked_interval = para_df["locked"][ind]
    weight_on = para_df["weight"][ind]
    start = time.time()
    SMM = MaxMatchOnl(
        timestr,
        order_pick,
        driver_pick,
        area,
        0,
        opt_interval,
        roll_interval,
        locked_interval,
        seed=seed,
        void=void,
        weight_on=weight_on,
    )
    match_temp = SMM.twooffMatch()
    end = time.time()
    time_temp = end - start
    # print(" =============== Running time ============== \n", end - start)
    # print(" =============== Match results ============== \n")
    # print("Total orders:", len(order_pick))
    # print("Total drivers:", len(driver_pick))
    # print("Total matches:", match_temp)
    # print(" ============================================= \n")
    return match_temp, time_temp


temp_out = Parallel(n_jobs=int(cpu_count() - 1), prefer="processes")(
    delayed(run_online_match)(ind=i) for i in range(len(para_df))
)

match_temp, time_temp = temp_out[0]

match_result.append(match_temp)
time_spent.append(time_temp)


pd.DataFrame(
    {
        "match_result": match_result,
        "time": time_spent,
        "weight": para_df["weight"].tolist(),
        "opt_int": para_df["opt"].tolist(),
        "roll_int": para_df["roll"].tolist(),
        "locked_int": para_df["locked"].tolist(),
    }
).to_csv("Database//online_result//%s//match_result_mpc.csv" % (timestr))
