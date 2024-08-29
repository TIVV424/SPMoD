#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Jan 21 2024

Author: Ruiting Wang
"""

import os
import random
import sys
from datetime import datetime
from multiprocessing import cpu_count
from time import time

import numpy as np
import pandas as pd
from joblib import Parallel, delayed
from offline import MaxMatchOff

SP_list = [60, 90, 120]
date = "2022-06-10"
SP_t = 60
seed = 0
void = 30
weight_on = "T"
np.random.seed(seed)

order = pd.read_csv("Database//NYC_trip//order_clean_260.csv", index_col=0)
area = np.load("Database//NYC_area//NY_area.npy")
driver_pick = pd.read_csv("Database//offline_result//driver_260.csv")

SP = pd.read_csv("Database//network_0305_SP//SP_%d_%s.csv" % (SP_t, date), index_col=0)
SP.columns = ["SP"]
SP = SP.reset_index(drop=True)

# %%
timestr = datetime.now().strftime("%Y%m%d-%H%M%S")
if not os.path.exists(os.path.join("Database//offline_result", timestr)):
    os.makedirs(os.path.join("Database//offline_result", timestr))

f = open("Database//offline_result//%s//log.txt" % (timestr), "w")
sys.stdout = f

order["call_time"] = pd.to_datetime(order["call_time"])
order["end_time"] = pd.to_datetime(order["end_time"])
start_time = pd.to_datetime(date + " 06:00:00 AM")
end_time = pd.to_datetime(date + " 12:00:00 PM")
end_time_actual = pd.to_datetime(date + " 10:00:00 AM")

order_pick = order[(order["call_time"] >= start_time) & (order["call_time"] < end_time)]
order_pick = order_pick[["sid", "call_time", "eid", "end_time"]]
order_pick = order_pick.sort_values(by="call_time").reset_index(drop=True)

order_pick["SP"] = SP["SP"]
assert len(order_pick) == len(SP)
assert order_pick.isna().sum().sum() == 0

order_pick = order_pick[(order_pick["call_time"] < end_time_actual)]

## Change this to 1000 for testing
order_pick = order_pick.values
print(order_pick.shape)
print("Number of orders between 6-10 am,", len(order_pick))

# %%
# driver["time"] = pd.date_range(
#     start=start_time - pd.Timedelta(minutes=15), end=start_time - pd.Timedelta(minutes=15), periods=len(driver)
# )
# driver.columns = ["id", "time"]
# driver_pick = driver[["id", "time"]]
driver_pick["id"] = driver_pick["id"].astype(int)
driver_pick["time"] = pd.to_datetime(driver_pick["time"])
# driver_pick.to_csv("Database//NYC_trip//driver_with_time.csv", index=False)
# print("Number of drivers between 8-10 am,", len(driver_pick))
driver_pick = driver_pick.values

start_time = time()
SMM = MaxMatchOff(order_pick, driver_pick, area, 0, seed, void, weight_on)
match_result = SMM.twooffMatch()
end_time = time()
print(" =============== Running time ============== \n", end_time - start_time)
print(match_result)
np.save("Database//offline_result//%s//match_result_weight_%s.npy" % (str(timestr), str(weight_on)), match_result)

pd.DataFrame({"match_result": match_result, "time": end_time - start_time, "weight": weight_on}, index=[0]).to_csv(
    "Database//offline_result//%s//match_result_weight_%s.csv" % (str(timestr), str(weight_on))
)
