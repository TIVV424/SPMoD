#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jun  9 17:16:19 2021

@author: didi
"""

from reopt_0820 import MaxMatchOnl
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

import time
import debugpy
import random

# debugpy.listen(5678)
# print('Waiting for debugger')
# debugpy.wait_for_client()
# print('Attached')

driver0 = pd.read_csv("..//clean_nyc_data//driver.csv")
order = pd.read_csv("..//clean_nyc_data//order.csv")
# area = np.load("..//clean_nyc_data//NY_area.npy")
area = pd.read_csv("..//clean_nyc_data//NY_area_df.csv",index_col=0)
area.columns =  [int(float(s)) for s in area.columns]
area.index =  [int(float(s)) for s in area.index]

order['call_time']=pd.to_datetime(order['call_time']); order['end_time']=pd.to_datetime(order['end_time'])
start_time = pd.to_datetime('2022-06-01 06:00:00 AM'); end_time = pd.to_datetime('2022-06-01 08:00:00 AM')
order_pick = order[(order['call_time'] > start_time) & (order['call_time'] <= end_time)]
order_pick = order_pick[['sid','call_time','eid','end_time']]
order_pick = order_pick.values
driver0['time'] = pd.date_range(start=start_time, end=start_time, periods=len(driver0))
print(len(order_pick))


start = time.time()
for Optinterval in [30]:
    for Rollinterval in [5]:
        for Lockedinterval in [10]:
    #     for driver in [driver_norm]:
            driver_pick = driver0[['id','time']]
            driver_pick = driver_pick.values
    
            SMM = MaxMatchOnl(order_pick,driver_pick,area,0,Optinterval,Rollinterval,Lockedinterval,0)
            print(SMM.twooffMatch())
        
end = time.time()
print(end - start)        
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
