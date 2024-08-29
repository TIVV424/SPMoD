#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri March 8 2024

Author: Ruiting Wang
"""

import random

import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
import pandas as pd
import seaborn as sns
from longest_path import single_sink_longest_dag_path
from network_build import ConstructNetwork

# Note: all time span should be [start_time, end_time)

date_list = [
    # "2022-06-01",
    # "2022-06-02",
    "2022-06-03",
    "2022-06-04",
    "2022-06-05",
    "2022-06-06",
    "2022-06-07",
    "2022-06-08",
    "2022-06-09",
    "2022-06-10",
]
folder = "network_0411_SP_void30"
SP_interval_list = [60]  # , 90, 120
void = 20

# load data
# driver = pd.read_csv("Database//NYC_trip//driver_260.csv", index_col=0)
order = pd.read_csv("Database//NYC_trip//order_clean_260.csv", index_col=0)
area = np.load("Database//NYC_area//NY_area.npy")

order["call_time"] = pd.to_datetime(order["call_time"])
order["end_time"] = pd.to_datetime(order["end_time"])


for date in date_list:
    # create driver's pick up time (dummy data)
    # start_time = pd.to_datetime(date + " 06:00:00 AM")
    # driver["time"] = pd.date_range(start=start_time, end=start_time, periods=len(driver))
    # driver.columns = ["id", "time"]
    # driver_pick = driver.values

    # select all orders in the morning hours
    start_time = pd.to_datetime(date + " 06:00:00 AM")
    end_time = pd.to_datetime(date + " 12:00:00 PM")
    order_pick = order[(order["call_time"] >= start_time) & (order["call_time"] < end_time)]
    order_pick = order_pick[["sid", "call_time", "eid", "end_time"]].sort_values(by="call_time")
    order_pick = order_pick.reset_index(drop=True)
    total_order_num = len(order_pick)

    for SP_interval in SP_interval_list:
        SP = dict()

        # select all orders in the current SP interval
        start_time_current = order_pick["call_time"][0]
        end_time_current = start_time + pd.Timedelta(minutes=SP_interval)
        order_pick_current = order_pick[
            (order_pick["call_time"] >= start_time_current) & (order_pick["call_time"] < end_time_current)
        ]

        # create two pointers to track the current time interval
        pointer_a = 0
        pointer_b = order_pick_current.index[-1]

        # build the network for the first time interval
        net = ConstructNetwork(order_pick_current.values, area, void=void)
        G_order = net.build_network(network_type="order")
        G_order.add_node("sink")
        for node in G_order.nodes():
            if node != "sink":
                G_order.add_edge(node, "sink", weight=0)

        # compute the longest path for the first time interval
        # record SP for the node at pointer_a
        SP_all = single_sink_longest_dag_path(G_order, "sink")
        SP["t" + str(pointer_a)] = SP_all["t" + str(pointer_a)]

        # loop through all orders in the morning hours and get SP values
        for i in range(len(order_pick)):
            start_time_current = order_pick["call_time"][i]
            end_time_current = start_time_current + pd.Timedelta(minutes=SP_interval)
            order_pick_current = order_pick[(order_pick["call_time"] < end_time_current)]
            order_pick_current = order_pick_current.iloc[i:, :]
            if order_pick_current is None:
                print("No order in the current time interval")
                continue
            if order_pick_current.index[0] > pointer_a:
                remove_nodes_list = [i for i in range(pointer_a, order_pick_current.index[0])]
                net.prune_network(G_order, remove_nodes_list)
                pointer_a = order_pick_current.index[0]

            if order_pick_current.index[-1] > pointer_b:
                expand_nodes = order_pick_current.loc[order_pick_current.index > pointer_b]
                expand_nodes_list = [i for i in expand_nodes.index]
                G_order = net.expand_network(G_order, expand_nodes.values, expand_nodes_list)
                pointer_b = order_pick_current.index[-1]

            MTC = single_sink_longest_dag_path(G_order, "sink")
            SP["t" + str(pointer_a)] = MTC["t" + str(pointer_a)]

        pd.DataFrame.from_dict(SP, orient="index").to_csv("Database//%s//SP_%d_%s.csv" % (folder, SP_interval, date))

    # compute network metrics for the whole morning times
    # start_time = pd.to_datetime(date + " 06:00:00 AM")
    # end_time = pd.to_datetime(date + " 12:00:00 PM")
    # order_pick = order[(order["call_time"] >= start_time) & (order["call_time"] < end_time)]
    # order_pick = order_pick[["sid", "call_time", "eid", "end_time"]]
    # order_pick = order_pick.values

    # net = ConstructNetwork(order_pick, area, void=void)
    # G_order = net.build_network(network_type="order")
    # net.saveNetwork(G_order, "Database//%s//order_%s.gpickle" % (folder, date))
    # df_all = net.network_metrics(G_order)
    # df_all.to_csv("Database//%s//network_metrics_%s.csv" % (folder, date))
