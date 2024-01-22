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


class ConstructNetwork(object):
    def __init__(self, order, driver, area, seed, void):
        self.order = order
        self.driver = driver
        self.area = area
        self.n_order = len(order)
        self.n_driver = len(driver)
        self.n_area = len(area)
        self.seed = seed
        self.void = void

    def getConnectivity(self):
        VoidTime = pd.Timedelta(self.void, unit="m")
        OrderList = range(0, self.n_order)
        DriverList = range(0, self.n_driver)

        driver_time = self.driver[:, 1]
        driver_area = self.driver[:, 0]
        order_start_time = self.order[:, 1]
        order_start_area = self.order[:, 0]
        order_end_time = self.order[:, 3]
        order_end_area = self.order[:, 2]

        driver_list = DriverList
        order_list = OrderList
        driver_con_trip = {}
        driver_con_area = {}
        trip_con_trip = {}

        for i in range(len(driver_area)):
            driver_con_trip[i] = []
            driver_con_area[i] = []
            max_void_time = driver_time[i] + VoidTime
            min_void_time = driver_time[i]

            fil_index = set(
                np.where((order_start_time < max_void_time) & (order_start_time > min_void_time))[0].tolist()
            ) & set(OrderList)
            for j in fil_index:
                if (
                    driver_time[i] + pd.Timedelta(self.area.loc[driver_area[i], order_start_area[j]], unit="s")
                    < order_start_time[j]
                ):
                    driver_con_trip[i].append(j)

        for i in range(len(order_end_area)):
            trip_con_trip[i] = []
            max_void_time = order_end_time[i] + VoidTime
            min_void_time = order_end_time[i]

            fil_index = set(
                np.where((order_start_time < max_void_time) & (order_start_time > min_void_time))[0].tolist()
            ) & set(OrderList)

            for j in fil_index:
                if (
                    order_end_time[i] + pd.Timedelta(self.area.loc[order_end_area[i], order_start_area[j]], unit="s")
                    < order_start_time[j]
                ):
                    trip_con_trip[i].append(j)

        G = self.buildNetwork(driver_list, order_list, driver_con_trip, trip_con_trip)

        return G

    def buildNetwork(self, driver_list, order_list, driver_con_trip, trip_con_trip):
        G = nx.DiGraph()
        # add supersource and supersink to the network
        n_driver = len(driver_list)
        G.add_node("s", demand=-n_driver)
        G.add_node("t", demand=n_driver)
        # add drivers to the network
        for i in driver_list:
            G.add_node("dr" + str(i))
        # add trips to the network
        for i in order_list:
            G.add_node("to" + str(i))
            G.add_node("td" + str(i))

        # add edge to supersource and supersink
        for i in driver_list:
            G.add_edge("s", "dr" + str(i), weight=0, capacity=1)
            G.add_edge("dr" + str(i), "t", weight=0, capacity=1)

        for i in order_list:
            G.add_edge("td" + str(i), "t", weight=0, capacity=1)

        # add trips
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
        # plt.show()
        return G

    def saveNetwork(self, G, filename):
        nx.write_gpickle(G, filename)

    def loadNetwork(self, filename):
        G = nx.read_gpickle(filename)
        return G

    # def network_metrics(self, G):
    #     deg_centrality = nx.degree_centrality(G) #degree centrality

    #     nx.closeness_centrality(G) #closeness centrality
    #     nx.betweenness_centrality(G) #betweenness centrality

    # betweenness centrality

    # print(nx.betweenness_centrality(G))
    # print(nx.edge_betweenness_centrality(G))
    # print(nx.info(G))
    # print("Network density:", nx.density(G))
    # print("Network diameter:", nx.diameter(G))
    # print("Network average shortest path length:", nx.average_shortest_path_length(G))
    # print("Network average clustering coefficient:", nx.average_clustering(G))
    # print("Network average degree connectivity:", nx.average_degree_connectivity(G))
    # print("Network average degree:", nx.average_degree_connectivity(G))
