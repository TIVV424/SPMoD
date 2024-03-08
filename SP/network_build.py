#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Jan 21 2024

Author: Ruiting Wang
"""

import networkx as nx
import numpy as np
import pandas as pd


class ConstructNetwork(object):
    '''
    construct order network or full network
    
    '''
    def __init__(self, order, area, void, driver = None):
        '''
        Input
        ---------
        order: (np.array) the order data, four columns: start_area, start_time, end_area, end_time
        area: (np.array) the travel time between areas
        void: (int) the maximum driver void time between two trips
        driver: (np.array) the driver data, two columns: area, time; 
            for order network only, no drivers' info is needed
        '''
        self.order = order
        self.driver = driver
        self.area = area
        self.n_order = len(order)
        self.order_list = range(0, self.n_order)
        if driver is not None:
            self.n_driver = len(driver)
            self.driver_list = range(0, self.n_driver)
        self.n_area = len(area)
        self.void = pd.Timedelta(void, unit="m")

    def get_t2t_onnectivity(self):
        '''
        get trip to trip connectivity 

        Return
        ---------
        trip_con_trip: (dict) the connectivity between trips, key is the trip number, value is the list of following trip numbers that can connect to it
        
        '''
        order_start_time = self.order[:, 1]
        order_start_area = self.order[:, 0]
        order_end_time = self.order[:, 3]
        order_end_area = self.order[:, 2]

        trip_con_trip = {}

        for i in range(len(order_end_area)):
            trip_con_trip[i] = []
            max_void_time = order_end_time[i] + self.void
            min_void_time = order_end_time[i]

            fil_index = set(
                np.where((order_start_time < max_void_time) & (order_start_time > min_void_time))[0].tolist()
            ) & set(self.order_list)

            for j in fil_index:
                if (
                    order_end_time[i] + pd.Timedelta(self.area[order_end_area[i], order_start_area[j]], unit="s")
                    < order_start_time[j]
                ):
                    trip_con_trip[i].append(j)

        return trip_con_trip

    def get_d2t_onnectivity(self):
        '''
        get driver to trip connectivity

        Return
        ---------
        driver_con_trip: (dict) the connectivity between drivers and trips, key is the driver number, value is the list of trip numbers that can connect to it

        '''
        driver_time = self.driver[:, 1]
        driver_area = self.driver[:, 0]
        order_start_time = self.order[:, 1]
        order_start_area = self.order[:, 0]
        order_end_time = self.order[:, 3]
        order_end_area = self.order[:, 2]

        driver_con_trip = {}
        driver_con_area = {}

        for i in range(len(driver_area)):
            driver_con_trip[i] = []
            driver_con_area[i] = []
            max_void_time = driver_time[i] + self.void
            min_void_time = driver_time[i]

            fil_index = set(
                np.where((order_start_time < max_void_time) & (order_start_time > min_void_time))[0].tolist()
            ) & set(self.order_list)
            for j in fil_index:
                if (
                    driver_time[i] + pd.Timedelta(self.area[driver_area[i], order_start_area[j]], unit="s")
                    < order_start_time[j]
                ):
                    driver_con_trip[i].append(j)

        return driver_con_trip

    def get_a2b_onnectivity(self, a, b, a_list, b_list):
        """
        get the connectivity between a set of trips a and another set of trips b

        Input
        ---------
        a: (np.array) the first set of trips, four columns: start_area, start_time, end_area, end_time
        b: (np.array) the second set of trips, four columns: start_area, start_time, end_area, end_time
        a_list: (list) the list of trips numbers in a
        b_list: (list) the list of trips numbers in b

        Return
        ---------
        a_con_b: (dict) the connectivity between a and b, key is the trip number in b, value is the list of previous trip numbers in a that can connect to it.
        a_con_b[j] = [i1, i2, ...] means trip a[i1], a[i2], ... can connect to trip b[j]

        """
        # a_start_time = a[:, 1]
        # a_start_area = a[:, 0]
        a_end_time = a[:, 3]
        a_end_area = a[:, 2]

        b_start_time = b[:, 1]
        b_start_area = b[:, 0]
        b_end_time = b[:, 3]
        b_end_area = b[:, 2]

        a_con_b = {}

        for j in range(len(b_end_area)):
            a_con_b[b_list[j]] = []

            # look before trip in b and find if there is a trip in a that can connect to it
            max_void_time = b_end_time[j] - self.void
            min_void_time = b_end_time[j]

            fil_index = set(np.where((a_end_time > max_void_time) & (a_end_time < min_void_time))[0].tolist())

            # if a[i] can connect to b[j], add it to the list
            for i in fil_index:
                if a_end_time[i] + pd.Timedelta(self.area[a_end_area[i], b_start_area[j]], unit="s") < b_start_time[j]:
                    a_con_b[b_list[j]].append(a_list[i])

        return a_con_b

    def build_full_network(self, driver_list, order_list, driver_con_trip, trip_con_trip):
        '''
        build the full network with drivers and trips (Acativity on Edge Network Flow Network)


        Input
        ---------
        driver_list: (list) the list of drivers
        order_list: (list) the list of trips
        driver_con_trip: (dict) the connectivity between drivers and trips, key is the driver number, value is the list of trip numbers that can connect to it
        trip_con_trip: (dict) the connectivity between trips, key is the trip number, value is the list of following trip numbers that can connect to it

        Return
        ---------
        G: (networkx.DiGraph) the full network flow network

        '''

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

        return G

    def build_order_network(self, order_list, trip_con_trip):
        '''
        build the order network based on order connectivity

        Input
        ---------
        order_list: (list) the list of trips
        trip_con_trip: (dict) the connectivity between trips, key is the trip number, value is the list of following trip numbers that can connect to it

        Return
        ---------
        G: (networkx.DiGraph) the order network

        '''
        G = nx.DiGraph()

        for i in order_list:
            G.add_node("t" + str(i))

        # add trip's connectivity to trip
        for i in trip_con_trip:
            for j in trip_con_trip[i]:
                G.add_edge("t" + str(i), "t" + str(j))

        return G

    def build_network(self, network_type="order"):
        '''
        build the network based on the network type

        Input
        ---------
        network_type: (str) the network type, "order" or "full"

        Return
        ---------
        G: (networkx.DiGraph) the network
        '''

        trip_con_trip = self.get_t2t_onnectivity()

        if network_type == "order":
            G = self.build_order_network(self.order_list, trip_con_trip)
        elif network_type == "full":
            driver_con_trip = self.get_d2t_onnectivity()
            G = self.build_full_network(self.driver_list, self.order_list, driver_con_trip, trip_con_trip)
        return G

    def saveNetwork(self, G, filename):
        """
        save the network to the file
        """
        nx.write_gpickle(G, filename)

    def loadNetwork(self, filename):
        """
        load the network from the file
        """
        G = nx.read_gpickle(filename)
        return G

    def network_metrics(self, G):
        """
        compute the network metrics

        Input
        ---------
        G: (networkx.DiGraph) the network

        Return
        ---------
        df: (pandas.DataFrame) the network metrics,  including degree, in-degree, out-degree, betweenness centrality, closeness centrality, Katz centrality
        """
        degree = nx.degree(G)  # degree
        in_degree = G.in_degree()  # in-degree
        out_degree = G.out_degree()  # out-degree
        clo_centrality = nx.closeness_centrality(G)  # closeness centrality
        bet_centrality = nx.betweenness_centrality(G, normalized=False)  # betweenness centrality
        katz_centrality = nx.katz_centrality(G, normalized=False)  # Katz centrality

        df = pd.DataFrame.from_dict(
            [dict(degree), dict(in_degree), dict(out_degree), clo_centrality, bet_centrality, katz_centrality]
        ).T
        df.columns = [
            "degree",
            "in_degree",
            "out_degree",
            "betweenness_centrality",
            "closeness_centrality",
            "katz_centrality",
        ]

        return df


    def naive_longest_path(self, G, node_list):
        """
        naively compute the longest path in the network (not efficient for large network)

        Input
        ---------
        G: (networkx.DiGraph) the network

        Return
        ---------
        longest_path: (list) the longest path in the network

        """
        longest_path = {}
        for node in node_list:
            longest_path[node] = len(max(nx.all_simple_paths(G, node, "sink"), key=lambda x: len(x))) - 1
        return longest_path

    def expand_network(self, G, expand_nodes, expand_nodes_list):
        """
        expand the network by adding a set of new nodes and connect new nodes to the existing network

        Input
        ---------
        G: (networkx.DiGraph) the network
        expand_nodes: (np.array) the new nodes to be added to the network
        expand_nodes_list: (list) the index of new nodes

        Return
        ---------
        G: (networkx.DiGraph) the expanded network

        """
        a_con_b = self.get_a2b_onnectivity(self.order, expand_nodes, self.order_list, expand_nodes_list)

        for i in expand_nodes_list:
            G.add_node("t" + str(i))

        # add the edges from the new nodes to the existing network
        for j in a_con_b:
            for i in a_con_b[j]:
                G.add_edge("t" + str(i), "t" + str(j))

        for j in expand_nodes_list:
            G.add_edge("t" + str(j), "sink", weight=0)

        # update the current order and order_list in the network
        self.order = np.concatenate((self.order, expand_nodes), axis=0)
        self.order_list = np.concatenate((self.order_list, expand_nodes_list), axis=0)

        return G

    def prune_network(self, G, remove_nodes_list):
        """
        prune the network by removing a set of nodes

        Input
        ---------
        G: (networkx.DiGraph) the network
        remove_nodes_name: (list) the names of nodes to be removed from the network

        Return
        ---------
        G: (networkx.DiGraph) the pruned network

        """
        # convert the index of nodes to the names of nodes
        remove_nodes_name = ["t" + str(i) for i in remove_nodes_list]

        G.remove_nodes_from(remove_nodes_name)
        pruned_nodes = len(remove_nodes_list)

        # update the current order and order_list in the network
        self.order = self.order[pruned_nodes:, :]
        self.order_list = self.order_list[pruned_nodes:]

        return G
