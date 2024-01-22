#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jun  8 16:16:26 2021

@author: didi
"""

from offline import MaxMatchOff
import numpy as np
import pandas as pd
import random

# import debugpy
from joblib import Parallel, delayed
from multiprocessing import cpu_count
from time import time

# debugpy.listen(5678)
# print('Waiting for debugger')
# debugpy.wait_for_client()
# print('Attached')

driver0 = pd.read_csv("Database//NYC_trip//driver.csv")
order = pd.read_csv("Database//NYC_trip//order.csv")
# area = np.load("Database//NYC_area//NY_area.npy")
area = pd.read_csv("Database//NYC_area//NY_area_df.csv", index_col=0)
area.columns = [int(float(s)) for s in area.columns]
area.index = [int(float(s)) for s in area.index]
area.loc[:, 44] = area.loc[44, :]
order["call_time"] = pd.to_datetime(order["call_time"])
order["end_time"] = pd.to_datetime(order["end_time"])
start_time = pd.to_datetime("2022-06-01 06:00:00 AM")
end_time = pd.to_datetime("2022-06-01 08:00:00 AM")
order_pick = order[(order["call_time"] > start_time) & (order["call_time"] <= end_time)]
order_pick = order_pick[["sid", "call_time", "eid", "end_time"]].reset_index(drop=True)
print(len(order_pick))


driver0["time"] = pd.date_range(start=start_time, end=end_time, periods=len(driver0))
driver_pick = driver0[["id", "time"]]
driver_pick = driver_pick.values
seed = 0
void_list = [30]
off_trip = np.zeros((len(void_list), len(order_pick)))


def n_1_match(ind, void):
    order_pick1 = order_pick.drop(index=ind)
    order_pick1 = order_pick.values
    SMM = MaxMatchOff(order_pick1, driver_pick, area, 0, seed, void)
    return SMM.twooffMatch()


start_time = time()
off_trip = Parallel(n_jobs=int(cpu_count()), prefer="processes")(
    delayed(n_1_match)(ind=i, void=v) for i in range(5) for v in void_list
)

end_time = time()
print(end_time - start_time)

np.save("off_trip.npy", off_trip)
