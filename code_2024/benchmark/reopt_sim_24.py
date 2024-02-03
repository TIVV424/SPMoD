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

import time


driver = pd.read_csv("Database//NYC_trip//driver_260_2000.csv", index_col=0)
order = pd.read_csv("Database//NYC_trip//order_clean_260.csv", index_col=0)
area = np.load("Database//NYC_area//NY_area.npy")
df_MTC = pd.read_csv("Database//network8_10//network_metrics_MTC.csv", index_col=0)
df_MTC = df_MTC[df_MTC["time"] == "8-10am"]
df_MTC.reset_index(drop=True, inplace=True)

seed = 0
void = 20
weight_on = True

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


driver_pick = pd.read_csv("Database//NYC_trip//driver_with_time.csv")
driver_pick["time"] = pd.to_datetime(driver_pick["time"])
print("Number of drivers between 8-10 am,", len(driver_pick))
driver_pick = driver_pick.values

match_result = []
time_spent = []
opt_int_list = []
roll_int_list = []
lock_int_list = []
weight_on_list = []

for opt_interval in [30]:
    for roll_interval in [5]:
        for locked_interval in [10]:
            for weight_on in [True]:
                start = time.time()
                SMM = MaxMatchOnl(
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
                opt_int_list.append(opt_interval)
                roll_int_list.append(roll_interval)
                lock_int_list.append(locked_interval)
                weight_on_list.append(weight_on)
                print(match_temp)
                print(" =============== Running time ============== \n", end - start)


pd.DataFrame(
    {
        "match_result": match_result,
        "time": time_spent,
        "weight": weight_on_list,
        "opt_int": opt_int_list,
        "roll_int": roll_int_list,
        "lock_int": lock_int_list,
    }
).to_csv("Database\offline_result\match_result_mpc.csv")


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
