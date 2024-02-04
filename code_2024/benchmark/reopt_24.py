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
        self,
        dirname,
        order,
        driver,
        area,
        uncertainty,
        opt_interval,
        roll_interval,
        locked_interval,
        seed,
        void,
        weight_on="T",
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
        self.dirname = dirname
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

    def getConnectivity(self, driver_list, order_list, void_time):
        driver_time = self.driver[:, 1]
        driver_area = self.driver[:, 0]
        order_start_time = self.order[:, 1]
        order_start_area = self.order[:, 0]
        order_end_time = self.order[:, 3]
        order_end_area = self.order[:, 2]

        driver_con_trip = {}
        trip_con_trip = {}

        # time1 = time()

        for i in range(self.n_driver):
            driver_con_trip[i] = []
            max_void_time = driver_time[i] + void_time
            min_void_time = driver_time[i]

            fil_index = set(
                np.where((order_start_time < max_void_time) & (order_start_time > min_void_time))[0].tolist()
            ) & set(order_list)
            for j in fil_index:
                if (
                    driver_time[i] + pd.Timedelta(self.area[driver_area[i], order_start_area[j]], unit="s")
                    < order_start_time[j]
                ):
                    driver_con_trip[i].append(j)

        # print("time_cal_driver_con_trip", time() - time1)

        # time1 = time()

        for i in range(self.n_order):
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
        # print("time_cal_trip_con_trip", time() - time1)

        # time1 = time()
        G = self.buildNetwork(driver_list, order_list, driver_con_trip, trip_con_trip)
        # print("time_build_network", time() - time1)

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
        if self.weight_on == "T":
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
        # nx.write_gexf(G, "30.gexf")
        return G

    def offlineMatch(self, DriverList, TripList, void_time):
        # time1 = time()
        G = self.getConnectivity(DriverList, TripList, void_time)

        # time_getConnectivity = time() - time1
        flowCost, flowDict = nx.network_simplex(G)

        # time_simplex = time() - time1 - time_getConnectivity
        # print("time_get_connectivity", time_getConnectivity)
        # print("time_simplex", time_simplex)
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

        return 0

    def updateOrder(self, all_trips_waiting, matched_trips_batch_i):
        return set(all_trips_waiting) - set(matched_trips_batch_i)

    def twooffMatch(self):
        all_trips_waiting = list(range(0, self.n_order))
        CFDriver = self.createDriver()
        TotalNum = 0

        start_time = min(self.order[:, 1])
        end_time = max(self.order[:, 1])

        filename_txt = "match_reopt_%s_%s_%s_weight_%s.txt" % (
            self.opt_interval,
            self.roll_interval,
            self.locked_interval,
            str(self.weight_on),
        )

        f = open("Database//online_result//%s//%s" % (self.dirname, filename_txt), "w")

        for i in pd.date_range(start=start_time, end=end_time, freq=str(self.roll_interval) + "min"):
            # print(np.max(self.driver[:,0]))

            interval_start = i
            interval_end = i + pd.Timedelta(self.opt_interval, unit="m")
            interval_locked = i + pd.Timedelta(self.locked_interval, unit="m")
            interval_roll = i + pd.Timedelta(self.roll_interval, unit="m")

            fr_time = pd.to_datetime(interval_start).strftime("%H%M%S")
            to_time = pd.to_datetime(interval_end).strftime("%H%M%S")
            lto_time = pd.to_datetime(interval_locked).strftime("%H%M%S")

            filename_npy = "match_reopt_%s_%s_%s_from_%s_to_%s_lto_%s_weight_%s.npy" % (
                self.opt_interval,
                self.roll_interval,
                self.locked_interval,
                fr_time,
                to_time,
                lto_time,
                str(self.weight_on),
            )

            print("Optimization horizon: ", fr_time, " to ", to_time, ". Result applied till: ", lto_time, file=f)

            driverList = np.where(self.driver[:, 1] <= interval_end)[0].tolist()
            tripList = np.where((self.order[:, 1] <= interval_end) & (self.order[:, 1] > interval_start))[0].tolist()

            available_driver_batch_i = list(set(driverList) & set(CFDriver))
            trip_batch_i = list(set(tripList) & set(all_trips_waiting))

            void_time = pd.Timedelta(self.void, unit="m")
            OneNum, OneMatch = self.offlineMatch(available_driver_batch_i, trip_batch_i, void_time)

            if self.weight_on == "T":
                cnt = 0
                for key in OneMatch.keys():
                    path = OneMatch[key]
                    if (len(path) == 1) & (sum(path.values()) == 1) & key.startswith("to"):
                        cnt += 1

                OneNum_match = cnt
            else:
                OneNum_match = OneNum

            print("Total Driver Num", len(available_driver_batch_i), file=f)
            print("Total Order Num", len(trip_batch_i), file=f)
            print("Order matched", OneNum_match, file=f)

            trip_in_locked_interval = np.where(
                (self.order[:, 1] <= interval_locked) & (self.order[:, 1] > interval_start)
            )[0].tolist()
            exist_trip_in_locked_interval = list(set(trip_in_locked_interval) & set(all_trips_waiting))
            matched_trips_batch_i = list(set(self.findTripList(OneMatch)) & set(exist_trip_in_locked_interval))
            num_of_matched_trips = len(matched_trips_batch_i)

            print("Order in Batch", len(exist_trip_in_locked_interval), file=f)
            print("Order matched in Batch", num_of_matched_trips, file=f)

            IntervalNum = num_of_matched_trips

            np.save("Database//online_result//%s//%s" % (self.dirname, filename_npy), OneMatch)

            self.updateDriver(available_driver_batch_i, OneMatch, interval_locked, interval_roll)
            all_trips_waiting = self.updateOrder(all_trips_waiting, matched_trips_batch_i)

            TotalNum = TotalNum + IntervalNum
            print("Total matched order so far", TotalNum, file=f)

        f.close()

        return TotalNum
