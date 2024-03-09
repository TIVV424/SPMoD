#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Jan 21 2024

Author: Ruiting Wang
"""

from offline import MaxMatchOff
import numpy as np
import pandas as pd
import random

from joblib import Parallel, delayed
from multiprocessing import cpu_count
from time import time


driver = pd.read_csv("Database//NYC_trip//driver_260_2000.csv", index_col=0)
order = pd.read_csv("Database//NYC_trip//order_clean_260.csv", index_col=0)
area = np.load("Database//NYC_area//NY_area.npy")
df_MTC = pd.read_csv("Database//network8_10//network_metrics_MTC.csv", index_col=0)
df_MTC = df_MTC[df_MTC["time"] == "8-10am"]
df_MTC.reset_index(drop=True, inplace=True)

seed = 0
void = 30
weight_on = "F"

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
order_pick = order_pick.values
print(order_pick.shape)
print("Number of orders between 8-10 am,", len(order_pick))


driver["time"] = pd.date_range(
    start=start_time - pd.Timedelta(minutes=15), end=start_time - pd.Timedelta(minutes=15), periods=len(driver)
)
driver.columns = ["id", "time"]
driver_pick = driver[["id", "time"]]
driver_pick["id"] = driver_pick["id"].astype(int)
driver_pick.to_csv("Database//NYC_trip//driver_with_time.csv", index=False)
print("Number of drivers between 8-10 am,", len(driver_pick))
driver_pick = driver_pick.values

start_time = time()
SMM = MaxMatchOff(order_pick, driver_pick, area, 0, seed, void, weight_on)
match_result = SMM.twooffMatch()
end_time = time()
print(" =============== Running time ============== \n", end_time - start_time)
print(match_result)
np.save("Database//offline_result//match_result_weight_%s.npy" % str(weight_on), match_result)

pd.DataFrame({"match_result": match_result, "time": end_time - start_time, "weight": weight_on}, index=[0]).to_csv(
    "Database//offline_result//match_result_weight_%s.csv" % str(weight_on)
)
