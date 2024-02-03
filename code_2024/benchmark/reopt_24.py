#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Jan 21 2024

Author: Ruiting Wang
"""

import networkx as nx
import random
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from time import time


class MaxMatchOnl(object):
    def __init__(
        self, order, driver, area, uncertainty, opt_interval, roll_interval, locked_interval, seed, void, weight_on=True
    ):
        """
        Parameters
        ------------
        order: (numpy array) order information, including start area, start time, end area, end time
        driver: (numpy array) driver information, including current area, current time
        area: (numpy array) travel time between areas
        uncertainty: (float) uncertainty of travel time
        opt_interval: (int) time interval of optimization
        roll_interval: (int) time interval of rolling
        locked_interval: (int) time interval of locked
        seed: (int) random seed

        Returns
        ------------

        """
        self.order = order
        self.driver = driver
        self.area = area
        self.n_order = order.shape[0]
        self.n_driver = driver.shape[0]
        self.n_area = area.shape[0]
        self.opt_interval = opt_interval
        self.roll_interval = roll_interval
        self.locked_interval = locked_interval
        self.uncertainty = 0
        self.seed = seed
        self.void = void
        self.order_list = range(0, self.n_order)
        self.order_MTC = self.order[:, 4]
        self.weight_on = weight_on
        print("=========== Weighted feature :", self.weight_on, " ===========")

    def getConnectivity(self, driver_list, order_list, void_time):
        driver_time = self.driver[:, 1]
        driver_area = self.driver[:, 0]
        order_start_time = self.order[:, 1]
        order_start_area = self.order[:, 0]
        order_end_time = self.order[:, 3]
        order_end_area = self.order[:, 2]

        driver_con_trip = {}
        trip_con_trip = {}

        time1 = time()

        for i in range(len(driver_list)):
            # TODO: update this to use numpy indexing
            """
            driver_con_trip.append(
                set(
                    np.where(
                        order_start_time
                        - driver_time[i]
                        - void_time
                        > self.area[driver_area[i], :]
                    )
                )
                & set(order_list)
            )

            """
            driver_con_trip[i] = []
            max_void_time = driver_time[i] + void_time
            min_void_time = driver_time[i]

            fil_index = set(
                np.where((order_start_time < max_void_time) & (order_start_time > min_void_time))[0].tolist()
            ) & set(order_list)
            for j in fil_index:
                # print(driver_area[i],order_start_area[j])
                # print(self.area[driver_area[i],order_start_area[j]])
                if (
                    driver_time[i] + pd.Timedelta(self.area[driver_area[i], order_start_area[j]], unit="s")
                    < order_start_time[j]
                ):
                    driver_con_trip[i].append(j)

        print("time_cal_driver_con_trip", time() - time1)

        time1 = time()

        for i in range(len(order_end_area)):
            # TODO: update this to use numpy indexing
            trip_con_trip[i] = []
            max_void_time = order_end_time[i] + void_time
            min_void_time = order_end_time[i]

            fil_index = set(
                np.where((order_start_time < max_void_time) & (order_start_time > min_void_time))[0].tolist()
            ) & set(order_list)

            for j in fil_index:
                if (
                    order_end_time[i] + pd.Timedelta(self.area[order_end_area[i], order_start_area[j]], unit="s")
                    < order_start_time[j]
                ):
                    trip_con_trip[i].append(j)
        print("time_cal_trip_con_trip", time() - time1)

        time1 = time()
        G = self.buildNetwork(driver_list, order_list, driver_con_trip, trip_con_trip)
        print("time_build_network", time() - time1)

        return G

    def buildNetwork(self, driver_list, order_list, driver_con_trip, trip_con_trip):

        order_MTC = self.order_MTC

        G = nx.DiGraph()
        # add supersource and supersink to the network
        n_driver = len(driver_list)
        G.add_node("s", demand=-n_driver)
        G.add_node("k", demand=n_driver)
        # add drivers to the network
        for i in driver_list:
            G.add_node("dr" + str(i))
        # add trips to the network
        for i in order_list:
            G.add_node("t" + str(i))
            # G.add_node("td" + str(i))

        # add edge to supersource and supersink
        for i in driver_list:
            G.add_edge("s", "dr" + str(i), weight=0, capacity=1)
            G.add_edge("dr" + str(i), "k", weight=0, capacity=1)

        for i in order_list:
            G.add_edge("td" + str(i), "k", weight=0, capacity=1)

        # add trips
        if self.weight_on == True:
            for i in order_list:
                G.add_edge("to" + str(i), "td" + str(i), weight=-order_MTC[i], capacity=1)
        else:
            for i in order_list:
                G.add_edge("to" + str(i), "td" + str(i), weight=-1, capacity=1)

        # add driver's connectivity to trip
        for i in driver_con_trip:
            for j in driver_con_trip[i]:
                G.add_edge("dr" + str(i), "to" + str(j), weight=0, capacity=1)

        # add trip's connectivity to trip
        for i in trip_con_trip:
            for j in trip_con_trip[i]:
                G.add_edge("td" + str(i), "to" + str(j), weight=0, capacity=1)

        # nx.draw(G, with_labels=True)
        # plt.savefig("test_rasterization.png", dpi=150)
        # plt.show()
        nx.write_gexf(G, "30.gexf")
        return G

    def offlineMatch(self, DriverList, TripList, void_time):
        time1 = time()
        G = self.getConnectivity(DriverList, TripList, void_time)
        time_getConnectivity = time() - time1
        flowCost, flowDict = nx.network_simplex(G)
        time_simplex = time() - time1 - time_getConnectivity
        print("time_get_connectivity", time_getConnectivity)
        print("time_simplex", time_simplex)
        return -flowCost, flowDict

    def findTripList(self, flowDict):
        TripList = sorted(
            [int(u[2:]) for u in flowDict for v in flowDict[u] if flowDict[u][v] > 0 and "to" in u and "td" in v]
        )
        return TripList

    def createDriver(self):
        CFDriver = set(range(0, self.n_driver))
        return CFDriver

    def getKeys(self, Dict, Value):
        return [k for k, v in Dict.items() if v == Value]

    def updateDriver(self, DriverList, MatchRoute, LockedEndTime, RollEndTime):
        for i in DriverList:
            key = self.getKeys(MatchRoute["dr" + str(i)], 1)
            if "t" not in key[0]:
                continue
            else:
                while "t" in key[0]:
                    TripzID = int(key[0][2:])
                    key = self.getKeys(MatchRoute[key[0]], 1)

                    if self.order[TripzID, 1] <= LockedEndTime:
                        self.driver[i, 1] = self.order[TripzID, 3]
                        self.driver[i, 0] = self.order[TripzID, 2]

            # compute left time
            if self.driver[i, 1] < RollEndTime:
                self.driver[i, 1] = RollEndTime
            else:
                continue
                """
                LeftTime = int((BatchEndTime - self.driver[i,1])/pd.Timedelta(1,unit='m'))
                # find possible area
                MoveArea = np.where(self.area[self.order[TripzID,2],:] < LeftTime)[0].tolist()
                try:
                    PickArea = random.sample(MoveArea,1)
                    self.driver[i,1] = self.driver[i,1]+pd.Timedelta(self.area[int(self.driver[i,0]),PickArea[0]],unit='s')
                    self.driver[i,0] = PickArea[0]
                except:
                    continue
                """

        return True

    def twooffMatch(self):
        Trip = range(0, self.n_order)
        CFDriver = self.createDriver()
        TotalNum = 0

        start_time = min(self.order[:, 1])
        end_time = max(self.order[:, 1])
        for i in pd.date_range(start=start_time, end=end_time, freq=str(self.roll_interval) + "min"):
            # print(np.max(self.driver[:,0]))

            interval_start = i
            interval_end = i + pd.Timedelta(self.opt_interval, unit="m")
            interval_locked = i + pd.Timedelta(self.locked_interval, unit="m")
            interval_roll = i + pd.Timedelta(self.roll_interval, unit="m")

            print(interval_start, interval_end, interval_locked, interval_roll)

            driverList = np.where(self.driver[:, 1] <= interval_end)[0].tolist()
            tripList = np.where((self.order[:, 1] <= interval_end) & (self.order[:, 1] > interval_start))[0].tolist()

            AllDriver_i = list(set(driverList) & set(CFDriver))
            Trip_i = list(set(tripList) & set(Trip))

            void_time = pd.Timedelta(20, unit="m")
            OneNum, OneMatch = self.offlineMatch(AllDriver_i, Trip_i, void_time)

            if self.weight_on == "T":
                cnt = 0
                for key in OneMatch.keys():
                    path = OneMatch[key]
                    if (len(path) == 1) & (sum(path.values()) == 1) & key.startswith("to"):
                        cnt += 1

                TotalNum = cnt
            else:
                TotalNum = OneNum

            print("Total Driver Num", len(AllDriver_i))
            print("Total Order Num", len(Trip_i))
            print("Order matched", TotalNum)

            tripListOpt = np.where((self.order[:, 1] <= interval_locked) & (self.order[:, 1] > interval_start))[
                0
            ].tolist()
            Trip_i_Opt = list(set(tripListOpt) & set(Trip))
            OneTripList = list(set(self.findTripList(OneMatch)) & set(Trip_i_Opt))
            RealOneNum = len(OneTripList)

            print("Order in Batch", len(Trip_i_Opt))
            print("Order matched in Batch", RealOneNum)

            IntervalNum = RealOneNum

            self.updateDriver(AllDriver_i, OneMatch, interval_locked, interval_roll)

            TotalNum = TotalNum + IntervalNum

        return TotalNum
