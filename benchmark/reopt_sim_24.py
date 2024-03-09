#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Jan 21 2024

Author: Ruiting Wang
"""

from reopt_24 import MaxMatchOnl
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import os
import time
import sys

orig_stdout = sys.stdout


driver = pd.read_csv("Database\NYC_trip\driver_260_2000.csv", index_col=0)
order = pd.read_csv("Database\NYC_trip\order_clean_260.csv", index_col=0)
area = np.load("Database\NYC_area\NY_area.npy")
df_MTC = pd.read_csv("Database\network8_10\network_metrics_MTC.csv", index_col=0)
df_MTC = df_MTC[df_MTC["time"] == "8-10am"]
df_MTC.reset_index(drop=True, inplace=True)


seed = 0
void = 30
weight_on = "T"
timestr = time.strftime("%Y%m%d-%H%M%S")
if not os.path.exists(os.path.join("Database\online_result", timestr)):
    os.makedirs(os.path.join("Database\online_result", timestr))

f = open("Database\online_result\%s\log.txt" % (timestr), "w")
sys.stdout = f

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


driver_pick = pd.read_csv("Database\NYC_trip\driver_with_time.csv")
driver_pick["time"] = pd.to_datetime(driver_pick["time"])
print("Number of drivers between 8-10 am,", len(driver_pick))
driver_pick = driver_pick.values

para_df = pd.read_csv('experiments\para_log.csv')

match_result = []
time_spent = []

for i in range(len(para_df)):
    opt_interval = para_df['opt'][i]
    roll_interval = para_df['roll'][i]
    locked_interval = para_df['locked'][i]
    weight_on = para_df['weight'][i]
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
    match_result.append(match_temp)
    time_spent.append(end - start)
    print(" =============== Running time ============== \n", end - start)
    print(" =============== Match results ============== \n")
    print("Total orders:", len(order_pick))
    print("Total drivers:", len(driver_pick))
    print("Total matches:", match_temp)
    print(" ============================================= \n")


pd.DataFrame(
    {
        "match_result": match_result,
        "time": time_spent,
        "weight": para_df['weight'].tolist(),
        "opt_int": para_df['opt'].tolist(),
        "roll_int": para_df['roll'].tolist(),
        "locked_int": para_df['locked'].tolist(),
    }
).to_csv("Database\online_result\%s\match_result_mpc.csv" % (timestr))

sys.stdout = orig_stdout
f.close()

"""
k = []

for drivernumber in [0.5]:
    onl_trip = np.zeros((6,5))
    c1 = 0
    for i in range(0,11,2):
        r j in [5,10]:
           c2 = 0
        fo uncertainty = 0.1*i; seed = 20; interval = 1*j
            
            start_time = pd.to_datetime('2021-01-30 06:00:00 AM'); end_time = pd.to_datetime('2021-01-30 10:00:00 AM')
            order_pick = order[(order['call_time'] > start_time) & (order['call_time'] < end_time)]
            order_pick = order_pick[[ 'sid','call_time','eid','end_time']]
            
            #start_time = pd.to_datetime('2021-01-01 09:00:00 AM'); end_time = pd.to_datetime('2021-01-01 10:00:00 AM')
            #driver_pick = driver[(driver['time'] > start_time) & (driver['time'] < end_time)]
            driver_pick = driver_pick[['rid','time']]   
            
            driver_pick = driver_pick.iloc[:int(drivernumber*len(order_pick)*0.15)]
            
            driver_pick['time'] = pd.date_range(start=pd.to_datetime('2021-01-30 06:00:00 AM'), end=pd.to_datetime('2021-01-30 06:00:00 AM'), periods=len(driver_pick))
            
            driver_pick = driver_pick.values; order_pick = order_pick.values

            
            SMM = MaxMatchOnl(order_pick,driver_pick,area,0,interval,seed)
            onl_trip[c1,c2] = SMM.twooffMatch()
            print(onl_trip[c1,c2]); c2 = c2 + 1
        c1 = c1 + 1
    print(onl_trip)
    k.append(onl_trip)  
np.save("./data/rep/rep_trip.npy", onl_trip)
"""
