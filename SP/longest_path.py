import networkx as nx


def single_sink_longest_dag_path(graph, s):
    """
    compute the longest path from s to the sink node in a directed acyclic graph
    """
    assert graph.out_degree(s) == 0
    dist = dict.fromkeys(graph.nodes, -float("inf"))
    dist[s] = 0
    topo_order = list(reversed(list(nx.topological_sort(graph))))
    for n in topo_order:
        for s in graph.predecessors(n):
            if dist[s] < dist[n] + 1:
                dist[s] = dist[n] + 1
    return dist
