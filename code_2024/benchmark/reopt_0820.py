#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jun  8 21:26:51 2021

@author: didi
"""

import networkx as nx
import random
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

class MaxMatchOnl(object):
    def __init__(self,order,driver,area,uncertainty,Optinterval,Rollinterval,Lockedinterval,seed):
        self.order = order
        self.driver = driver
        self.area = area
        self.n_order = len(order)
        self.n_driver = len(driver)
        self.n_area = len(area)
        self.Optinterval = Optinterval
        self.Rollinterval = Rollinterval
        self.Lockedinterval = Lockedinterval
        self.uncertainty = 0
        self.seed = seed
        
    def getConnectivity(self,DriverList,OrderList,VoidTime):
        driver_time = self.driver[:,1]; driver_area = self.driver[:,0]
        order_start_time = self.order[:,1]; order_start_area = self.order[:,0]
        order_end_time = self.order[:,3]; order_end_area = self.order[:,2]

        driver_list = DriverList; order_list = OrderList
        driver_con_trip = {}; driver_con_area = {}; trip_con_trip = {}
        
        for i in range(len(driver_area)):
            driver_con_trip[i] = []; driver_con_area[i]=[]; 
            max_void_time = driver_time[i]+VoidTime
            min_void_time = driver_time[i]
            
            fil_index = set(np.where((order_start_time < max_void_time) & (order_start_time > min_void_time))[0].tolist()) & set(OrderList)
            for j in fil_index:
                # print(driver_area[i],order_start_area[j])
                # print(self.area.loc[driver_area[i],order_start_area[j]])
                if driver_time[i] + pd.Timedelta(self.area.loc[driver_area[i],order_start_area[j]],unit='s') < order_start_time[j]:
                    driver_con_trip[i].append(j)
        
        for i in range(len(order_end_area)):
            trip_con_trip[i] = []
            max_void_time = order_end_time[i]+VoidTime
            min_void_time = order_end_time[i]
            
            fil_index = set(np.where((order_start_time < max_void_time) 
                                     & (order_start_time > min_void_time))[0].tolist()) & set(OrderList)
            
            for j in fil_index:
                if order_end_time[i] + pd.Timedelta(self.area.loc[order_end_area[i],order_start_area[j]],unit='s') < order_start_time[j]:
                    trip_con_trip[i].append(j)
        
        G = self. buildNetwork(driver_list, order_list, driver_con_trip, trip_con_trip)
        
        return G
    
    def buildNetwork(self, driver_list, order_list, driver_con_trip, trip_con_trip):
        G = nx.DiGraph()
        #add supersource and supersink to the network
        n_driver = len(driver_list)
        G.add_node('s', demand = -n_driver)
        G.add_node('k', demand = n_driver)
        #add drivers to the network
        for i in driver_list:
            G.add_node('dr'+str(i))
        #add trips to the network 
        for i in order_list:
            G.add_node('to'+str(i))
            G.add_node('td'+str(i))

        #add edge to supersource and supersink
        for i in driver_list:
            G.add_edge('s','dr'+str(i), weight = 0, capacity = 1)
            G.add_edge('dr'+str(i),'k', weight = 0, capacity = 1)
        
        for i in order_list:
            G.add_edge('td'+str(i),'k', weight = 0, capacity = 1)
            
        #add trips 
        for i in order_list:
            G.add_edge('to'+str(i),'td'+str(i), weight = -1, capacity = 1)
        
        #add driver's connectivity to trip
        for i in driver_con_trip:
            for j in driver_con_trip[i]:
                G.add_edge('dr'+str(i),'to'+str(j), weight = 0, capacity = 1)

        #add trip's connectivity to trip
        for i in trip_con_trip:
            for j in trip_con_trip[i]:
                G.add_edge('td'+str(i),'to'+str(j), weight = 0, capacity = 1)
                    
        #nx.draw(G, with_labels=True)
        #plt.savefig("test_rasterization.png", dpi=150)
        #plt.show()
        nx.write_gexf(G,"30.gexf")
        return G
    
    def offlineMatch(self,DriverList,TripList,VoidTime):
        G = self.getConnectivity(DriverList,TripList,VoidTime)
        flowCost, flowDict = nx.network_simplex(G)
        return -flowCost, flowDict
    
    def findTripList(self,flowDict):
        TripList = sorted([int(u[2:]) for u in flowDict for v in flowDict[u] if flowDict[u][v] > 0 and "to" in u and "td" in v ])
        return TripList
    
    def createDriver(self):
        CFDriver = set(range(0,self.n_driver))
        return CFDriver

    def getKeys(self, Dict, Value):
        return [k for k,v in Dict.items() if v == Value]

    def updateDriver(self,DriverList,MatchRoute,LockedEndTime,RollEndTime):
        for i in DriverList:
            key = self.getKeys(MatchRoute["dr"+str(i)], 1)
            if 't' not in key[0]:
                continue
            else: 
                while('t' in key[0]):
                    TripzID  = int(key[0][2:])
                    key = self.getKeys(MatchRoute[key[0]],1)
                    
                    if self.order[TripzID,1] <= LockedEndTime:
                        self.driver[i,1] = self.order[TripzID,3]
                        self.driver[i,0] = self.order[TripzID,2]

            # compute left time
            if self.driver[i,1]< RollEndTime:
                self.driver[i,1] = RollEndTime
            else:
                continue
                
                '''
                LeftTime = int((BatchEndTime - self.driver[i,1])/pd.Timedelta(1,unit='m'))
                # find possible area
                MoveArea = np.where(self.area[self.order[TripzID,2],:] < LeftTime)[0].tolist()
                try:
                    PickArea = random.sample(MoveArea,1)
                    self.driver[i,1] = self.driver[i,1]+pd.Timedelta(self.area[int(self.driver[i,0]),PickArea[0]],unit='s')
                    self.driver[i,0] = PickArea[0]
                except:
                    continue
                '''
        return True
    
    def twooffMatch(self):
        Trip = range(0,self.n_order)
        CFDriver = self.createDriver()
        TotalNum = 0
        
        start_time = min(self.order[:,1]); end_time  = max(self.order[:,1])
        for i in pd.date_range(start = start_time, end = end_time, freq = str(self.Rollinterval)+'min'):

            #print(np.max(self.driver[:,0]))
            
            interval_start = i; interval_end = i + pd.Timedelta(self.Optinterval,unit='m')
            interval_locked = i + pd.Timedelta(self.Lockedinterval,unit='m')
            interval_roll = i + pd.Timedelta(self.Rollinterval,unit='m')
            
            print(interval_start,interval_end,interval_locked,interval_roll)
            
            driverList = np.where(self.driver[:,1] <= interval_end)[0].tolist()
            tripList = np.where((self.order[:,1]<= interval_end) & (self.order[:,1]>interval_start))[0].tolist()

            AllDriver_i = list(set(driverList) & set(CFDriver))
            Trip_i = list(set(tripList) & set(Trip))
            

            VoidTime = pd.Timedelta(20,unit='m')
            OneNum, OneMatch = self.offlineMatch(AllDriver_i,Trip_i,VoidTime)
            
            print('Total Driver Num',len(AllDriver_i))
            
            print('Total Order Num',len(Trip_i))
            print('Order matched',OneNum)
            
            tripListOpt = np.where((self.order[:,1]<=interval_locked) & (self.order[:,1]>interval_start))[0].tolist()
            Trip_i_Opt = list(set(tripListOpt) & set(Trip))
            OneTripList = list(set(self.findTripList(OneMatch)) & set(Trip_i_Opt)) 
            RealOneNum = len(OneTripList)
            
            print('Order in Batch',len(Trip_i_Opt))
            print('Order matched in Batch',RealOneNum)
            
            IntervalNum = RealOneNum 
            
            self.updateDriver(AllDriver_i,OneMatch,interval_locked,interval_roll)
            
            TotalNum = TotalNum + IntervalNum
        return TotalNum
    

