import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from scipy.spatial import Delaunay
import networkx as nx
from scipy.stats import mannwhitneyu

import vis

def test_all(X, Y):
    result = pd.DataFrame([
        mannwhitneyu(X[c], Y[c])
        for c in X
    ], index=X.columns)

    df = pd.DataFrame([X.median(), Y.median()])
    result['magnitude'] = df.max() / df.min()

    result['direction'] = np.sign(result.statistic/(len(X)*len(Y)) - .5)
    
    return result
    
def get_groups(result, alpha=.01):
    mask = result.pvalue < alpha
    return (
        result.index[np.logical_and(mask, result.direction > 0)],
        result.index[np.logical_and(mask, result.direction < 0)]
    )

def get_group_label(result, u, v):
    def as_str(li):
        return f'({", ".join(li)})'
        
    gu, gv = get_groups(result)
    return f'{u}:{as_str(gu)} {v}:{as_str(gv)}'

def get_triangulation(points):
    G = nx.Graph()

    for i, xy in enumerate(points):
        G.add_node(i, pos=xy)
    
    tri = Delaunay(points)
    for i, j, k in tri.simplices:
        G.add_edge(i, j)
        G.add_edge(j, k)
        G.add_edge(k, i)

    return G

def get_tradeoff_lattice(X, xy, cluster):
    centroids = pd.DataFrame(xy).groupby(cluster).mean().values

    G = get_triangulation(centroids)
    
    for u, v, d in G.edges(data=True):
        d['test'] = test_all(X[cluster == u], X[cluster == v])

    return G

def get_tradeoff_lattice_direct(X, xy):
    G = nx.relabel_nodes(
        get_triangulation(xy),
        dict(enumerate(X.index))
    )
    
    for u, v, d in G.edges(data=True):
        diff = X.loc[u] - X.loc[v]
        
        d['test'] = pd.DataFrame(dict(
            magnitude=diff,
            direction=np.sign(diff),
            pvalue=0
        ))

    coef = (X - X.mean())/X.std()
    
    return G, coef

def draw_tradeoff_lattice(G, cluster=None, colors=None, points=None, coef=None, coef_threshold=1, with_labels=True, show_positive=False, by=None, alpha=.05, node_size=1000, node_labels_kwargs=dict(), edge_labels_kwargs=dict(), ax=None):
    if by is not None:
        G = reorient_lattice(
            G, by=by
        )

    if points is not None:
        vis.get_cluster_hulls(
            pd.DataFrame(points), cluster,
            marker_color=colors,
            marker_size=10,
            with_labels=False
        )

        pos = {
            v: G.nodes[v]['pos']
            for v in G
        }
    else:
        try:
            pos = nx.nx_agraph.graphviz_layout(G, prog='dot')
        except:
            pos = nx.kamada_kawai_layout(G)
    
    if coef is not None:
        draw_cluster_labels(
            pos,
            coef=coef,
            threshold=coef_threshold,
            **node_labels_kwargs
        )

    # nx.draw_networkx_nodes(G, pos, edgecolors='lightgray', node_color='none')
    nx.draw_networkx_edges(
        G, pos,
        node_size=node_size,
        edge_color=[
            'black' if by is None or d['test'].loc[by, 'pvalue'] < alpha else 'lightgray'
            for u, v, d in G.edges(data=True)
        ]
    )

    def create_label(d):
        test = d['test']
        return '\n'.join([
            f'{"+" if ser.direction > 0 else "- "}{k}'
            for k, ser in test[test.pvalue < alpha].iterrows()
            if (with_labels is True or k in with_labels) and (show_positive is True or ser.direction < 0)
        ])

    if with_labels is not False:
        nx.draw_networkx_edge_labels(
            G, pos,
            edge_labels={
                (u, v): create_label(d)
                for u, v, d in G.edges(data=True)
            },
            **edge_labels_kwargs
        )

    return G

def reorient_lattice(G, by, alpha=.01):
    D = nx.DiGraph()

    # copy nodes and data from G into D
    for v, d in G.nodes(data=True):
        D.add_node(v, **d)

    # copy edges, but flip baed on direction of by variable
    for v, u, d in G.edges(data=True):
        test = d['test'].copy()

        if test.loc[by, 'direction'] < 0:
            v, u = u, v
            test['direction'] *= -1
            
        D.add_edge(u, v, test=test)

    return D

def draw_cluster_labels(pos, coef, threshold=1.0, ax=None, **kwargs):
    ax = ax or plt.gca()

    def get_label(ser):
        names = [
            f'{"+" if np.sign(v) > 0 else "- "}{k}'
            for k, v in ser.items()
            if abs(v) > threshold
        ]
        return '\n'.join(names)
        
    labels = coef.apply(get_label, axis=1)

    for i, xy in pos.items():
        if i != -1:
            ax.annotate(
                f'# {i}\n{labels.loc[i]}',
                xy,
                va='center',
                ha='center',
                # xytext=(7, 0),
                # textcoords='offset points'
                backgroundcolor=(1, 1, 1, .5),
                **kwargs
            )