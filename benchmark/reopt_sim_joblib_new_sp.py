#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Jan 21 2024

Author: Ruiting Wang
"""
# %%
import os
import sys
import time
from multiprocessing import cpu_count

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from joblib import Parallel, delayed
from reopt_24 import MaxMatchOnl

SP_list = [60, 90, 120]
date = "2022-06-10"
SP_t = 60
seed = 0
void = 30
weight_on = "T"
np.random.seed(seed)

# driver = pd.read_csv("Database//NYC_trip//driver_260_2000.csv", index_col=0)
order = pd.read_csv("Database//NYC_trip//order_clean_260.csv", index_col=0)
area = np.load("Database//NYC_area//NY_area.npy")
SP = pd.read_csv("Database//network_test_0305//SP_%d_%s.csv" % (SP_t, date), index_col=0)
SP.columns = ["SP"]
SP = SP.reset_index(drop=True)

# %%
timestr = time.strftime("%Y%m%d-%H%M%S")
if not os.path.exists(os.path.join("Database//online_result", timestr)):
    os.makedirs(os.path.join("Database//online_result", timestr))

f = open("Database//online_result//%s//log.txt" % (timestr), "w")
sys.stdout = f

order["call_time"] = pd.to_datetime(order["call_time"])
order["end_time"] = pd.to_datetime(order["end_time"])
start_time = pd.to_datetime(date + " 06:00:00 AM")
end_time = pd.to_datetime(date + " 12:00:00 PM")

order_pick = order[(order["call_time"] >= start_time) & (order["call_time"] < end_time)]
order_pick = order_pick[["sid", "call_time", "eid", "end_time"]]
order_pick = order_pick.sort_values(by="call_time").reset_index(drop=True)

order_pick["SP"] = SP["SP"]
assert len(order_pick) == len(SP)
assert order_pick.isna().sum().sum() == 0

end_time = pd.to_datetime(date + " 12:00:00 PM") - pd.Timedelta(minutes=SP_t)
order_pick = order_pick[(order_pick["call_time"] < end_time)]

# %%
## Change this to 1000 for testing
order_pick = order_pick.values
print(order_pick.shape)
print("Number of orders between 6-12,", len(order_pick))

# %%
# Generate drivers
area_list = pd.read_csv("Database//NYC_area//NY_area_list.csv", index_col=0)
area_list = area_list.reset_index(drop=True).reset_index()

driver_size = int(len(order_pick) * 0.2)
driver = pd.DataFrame({"id": np.random.choice(area_list.oxmid, size=driver_size)})
driver = driver.merge(area_list, left_on="id", right_on="oxmid")
driver.drop(["oxmid"], axis=1, inplace=True)
driver.columns = ["id_263", "id_260"]
driver["time"] = pd.to_datetime(date + " 06:00:00 AM") - pd.to_timedelta(15, unit="m")
driver_pick = driver[["id_260", "time"]]
driver_pick.columns = ["id", "time"]
driver_pick.to_csv("Database//online_result//%s//driver_260.csv" % timestr, index=False)

driver_pick["time"] = pd.to_datetime(driver_pick["time"])
print("Number of drivers between 6-12,", len(driver_pick))
driver_pick = driver_pick.values
# %%
para_df = pd.read_csv("experiments//para_log.csv")


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

match_result = [i[0] for i in temp_out]
time_spent = [i[1] for i in temp_out]

pd.DataFrame(
    {
        "match_result": match_result,
        "time": time_spent,
        "weight": para_df["weight"].tolist(),
        "opt_int": para_df["opt"].tolist(),
        "roll_int": para_df["roll"].tolist(),
        "locked_int": para_df["locked"].tolist(),
    }
).to_csv("Database//online_result//%s//match_result_mpc_sp_%d_%s.csv" % (timestr, SP_t, date))

f.close()
