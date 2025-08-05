import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from scipy.spatial import Delaunay
from scipy.spatial.distance import cdist, pdist, squareform
import networkx as nx
from scipy.stats import mannwhitneyu

import hypernetx as hnx  # pip install hypernetx

import vis


def test_all(X, Y):
    result = pd.DataFrame([mannwhitneyu(X[c], Y[c]) for c in X], index=X.columns)

    df = pd.DataFrame([X.median(), Y.median()])
    result['magnitude'] = df.max() / df.min()

    result['direction'] = np.sign(result.statistic / (len(X) * len(Y)) - 0.5)

    return result


def get_groups(result, alpha=0.01):
    mask = result.pvalue < alpha
    return (
        result.index[np.logical_and(mask, result.direction > 0)],
        result.index[np.logical_and(mask, result.direction < 0)],
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
    G = nx.relabel_nodes(get_triangulation(xy), dict(enumerate(X.index)))

    for u, v, d in G.edges(data=True):
        diff = X.loc[u] - X.loc[v]

        d['test'] = pd.DataFrame(
            dict(magnitude=diff, direction=np.sign(diff), pvalue=0)
        )

    coef = (X - X.mean()) / X.std()

    return G, coef


def draw_tradeoff_lattice(
    G,
    cluster=None,
    colors=None,
    points=None,
    coef=None,
    coef_threshold=1,
    with_edge_labels=True,
    show_positive=False,
    by=None,
    alpha=0.05,
    node_size=1000,
    node_labels_kwargs=dict(),
    edge_labels_kwargs=dict(),
    ax=None,
):
    if by is not None:
        G = reorient_lattice(G, by=by)

    if points is not None:
        vis.get_cluster_hulls(
            pd.DataFrame(points),
            cluster,
            marker_color=colors,
            marker_size=10,
            with_labels=False,
        )

        pos = {v: G.nodes[v]['pos'] for v in G}
    else:
        try:
            pos = nx.nx_agraph.graphviz_layout(G, prog='dot')
        except:
            pos = nx.kamada_kawai_layout(G)

    if coef is not None:
        draw_cluster_labels(
            pos, coef=coef, threshold=coef_threshold, **node_labels_kwargs
        )

    # nx.draw_networkx_nodes(G, pos, edgecolors='lightgray', node_color='none')
    nx.draw_networkx_edges(
        G,
        pos,
        node_size=node_size,
        edge_color=[
            (
                'black'
                if by is None or d['test'].loc[by, 'pvalue'] < alpha
                else 'lightgray'
            )
            for u, v, d in G.edges(data=True)
        ],
    )

    def create_label(d):
        test = d['test']
        return '\n'.join(
            [
                f'{"+" if ser.direction > 0 else "- "}{k}'
                for k, ser in test[test.pvalue < alpha].iterrows()
                if (with_edge_labels is True or k in with_edge_labels)
                and (show_positive is True or ser.direction < 0)
            ]
        )

    if with_edge_labels is not False:
        nx.draw_networkx_edge_labels(
            G,
            pos,
            edge_labels={(u, v): create_label(d) for u, v, d in G.edges(data=True)},
            **edge_labels_kwargs,
        )

    return G


def reorient_lattice(G, by, alpha=0.01):
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
                backgroundcolor=(1, 1, 1, 0.5),
                **kwargs,
            )


class TradeoffLattice:
    def get_distance(self):
        X = self.rank[self.ovars].values

        return pd.DataFrame(
            cdist(X, X, metric=lambda x, y: (x != y).any() and (x >= y).all()),
            index=self.df.index,
            columns=self.df.index,
        )

    def get_specializers(self, i, drop=True):
        # boolean mask of rows better than all generalizers
        B = self.rank < self.rank.iloc[:i].min(axis=0)

        if drop:
            return B[B.any(axis=1)]

        return B

    def get_anti_specializers(self, i):
        # boolean mask of rows worse than all generalizers
        B = self.rank.iloc[i:] > self.rank.iloc[:i].max(axis=0)
        return B[B.any(axis=1)]

    def get_full_specialization(self, drop=True):
        result = self.rank == self.rank.cummin()
        result.iloc[0, :] = False

        if drop:
            return result[result.any(axis=1)]

        return result

    def __init__(
        self,
        df,
        ovars,
        dvars,
        ascending=[],
        min_specializers=None,
        max_specializers=None,
        n_generalizers=None,
        max_generalizers=None,
        score=None,  # smaller is better
        # currently unused
        non_dominated=True,
        n_specializers=1,
        umap_kwargs={},
    ):
        self.df = df
        self.ovars = ovars
        self.dvars = dvars

        self.scale = pd.Series(1, index=ovars)
        self.scale[ascending] = -1

        self.rank = (self.df[ovars] * self.scale).rank(ascending=False)
        self.rank_order = self.rank.apply(
            lambda row: tuple(sorted(row, reverse=True)), axis=1
        ).sort_values()
        self.rank = self.rank.loc[self.rank_order.index]

        self.score = self.rank.max(axis=1) if score is None else score

        iis = list(
            range(1, len(self.rank) if max_generalizers is None else max_generalizers)
        )
        self.specializer_counts = pd.DataFrame(
            [self.get_specializers(i).sum(axis=0) for i in iis], index=iis
        )

        # automatically compute largest number of generalizers to satisfy min_specializers per ovar
        if n_generalizers is not None:
            # user-specified
            self.n_generalizers = n_generalizers
        else:
            if min_specializers is not None:
                # find the most generalizers such that there are at least *min_specializers* in each category
                mask = (self.specializer_counts >= min_specializers).all(axis=1)

                if mask.any():
                    self.n_generalizers = self.specializer_counts.index[mask].max()
                else:
                    self.n_generalizers = 1
            elif max_specializers is not None:
                # find the fewest generalizers such that there are at most *max_specializers* in each category
                self.n_generalizers = (
                    (self.specializer_counts <= max_specializers).all(axis=1).idxmax()
                )
            else:
                print(
                    'You must specify one of: min_specializers, max_specializers, or n_generalizers'
                )

        self.generalizers = self.rank.index[: self.n_generalizers]
        self.specializers = self.get_specializers(self.n_generalizers)
        self.full_specialization = self.get_full_specialization()
        self.anti_specializers = self.get_anti_specializers(self.n_generalizers)

        # assign exactly one ovar to each specializer
        self.specialization = self.specializers.apply(
            lambda row: self.rank.loc[row.name, row].idxmin(), axis=1
        )

        # determine set of non-dominated solutions (useful later on)
        self.D = self.get_distance()
        self.non_dominated = self.D.index[self.D.sum(axis=0) == 0]

        # if method == 'topk':
        #     self.generalizers = self.rank.max(axis=1)\
        #         .sort_values()\
        #         .index[:self.n_generalizers]

        #     self.n_specializers = n_specializers or len(ovars)

        #     def get_specialization(R):
        #         return {
        #             c: R[c].sort_values().index[:self.n_specializers]
        #             for c in R
        #         }

        #     self.specializers = get_specialization(self.rank)
        #     self.anti_specializers = get_specialization(-self.rank)

        # elif method == 'better-than-generalizer':
        #     def get_specializers(rank):
        #         generalizers = rank.max(axis=1)\
        #             .sort_values()\
        #             .index[:self.n_generalizers]

        #         print(generalizers)

        #         if non_dominated:
        #             generalizers = generalizers[generalizers.map(self.non_dominated.__contains__)]

        #         mask = rank < rank.loc[generalizers].min(axis=0)
        #         specializers = mask[mask.any(axis=1)]

        #         if non_dominated:
        #             specializers = specializers[specializers.index.map(self.non_dominated.__contains__)]

        #         return generalizers, specializers

        #     self.generalizers, self.specializers = get_specializers(self.rank)
        #     self.anti_generalizers, self.anti_specializers = get_specializers(-self.rank)
        # elif method == 'weighted':
        #     pass

    def ovars_formatted(self, cmap='Greens_r'):
        def get_index_label(i):
            suffix = ''
            if i in self.generalizers:
                suffix = ' (~)'
            # if i in self.anti_generalizers:
            #     suffix = ' (!)'
            if i in self.specializers.index:
                suffix = ' (*)'

            return str(i) + suffix

        df = self.rank.assign(Score=self.score)

        return (
            df.style.format(precision=0)
            .format_index(get_index_label)
            .background_gradient(axis=None, cmap=cmap)
        )

    def plot_ovars_parallel_coords(
        self,
        reorder=True,
        use_rank=True,
        x_label_format=None,
        facets=None,
        include_all_generalizers=False,
        highlight_generalizers=False,
        ax=None,
    ):

        assert (
            ax is None or facets is None
        ), "When passing an axis, facets=None is required"

        data = self.rank

        cmap = plt.get_cmap('tab10')
        categories = set(data.index.values)
        color_map = {cat: cmap(i / len(categories)) for i, cat in enumerate(categories)}

        sel_index = self.specializers.index
        other_group = self.generalizers
        lw_highlight = 1
        lw_others = 5
        if highlight_generalizers:
            sel_index = self.generalizers
            other_group = self.specializers.index
            lw_highlight = 3
            lw_others = 1

        if not use_rank:
            X = self.df[self.ovars] * self.scale
            data = (X - X.mean()) / X.std()

        if reorder:
            rows = list(set(self.generalizers).union(self.specializers.index))
            C = data.loc[rows].corr()
            C[C < 0] = 0

            A = nx.from_pandas_adjacency(C)
            order = nx.spectral_ordering(A)
            data = data[order]
            # S = sel_index[order]
            self.C = C
        else:
            order = data.columns

            self.order = order

        x = np.arange(len(data.columns))

        # groupby facet for non-generalizers
        n = self.n_generalizers

        if include_all_generalizers and facets is not None:
            grouped = data.iloc[self.n_generalizers :].groupby(
                ['All'] * len(data - n) if facets is None else facets[n:]
            )
        else:
            grouped = data.groupby(['All'] * len(data) if facets is None else facets)

        for i, (k, data_k) in enumerate(grouped):
            # add generalizers back in so they appear in each plot
            if include_all_generalizers:
                data_k = pd.concat((data.iloc[:n], data_k))

            axi = ax or plt.subplot(len(grouped), 1, i + 1)
            axi.set_title(k)

            if use_rank:
                axi.invert_yaxis()

            for name, y in data_k.iterrows():
                s = None
                if name in sel_index:
                    kwargs = dict()
                    if not highlight_generalizers:
                        s = self.specializers.loc[name, order] * 50
                    else:
                        s = 50
                    axi.scatter(x, y, marker='o', s=s, zorder=10, color=color_map[name])
                    kwargs = dict(
                        linewidth=lw_highlight, color=color_map[name], zorder=8
                    )
                    s = name
                elif name in other_group:
                    kwargs = dict(linewidth=lw_others, color='lightgray')
                    # s = name
                else:
                    kwargs = dict(linewidth=0.5, color='lightgray')

                if s is not None:
                    axi.annotate(
                        s,
                        (x[-1], y.iloc[-1]),
                        va='center',
                        ha='left',
                        xytext=(5, 0),
                        textcoords='offset points',
                    )

                axi.plot(x, y, **kwargs)

            # ax.yaxis.set_label_text('Rank' if use_rank else 'Z-score')
            axi.xaxis.set_ticks(
                x,
                (
                    data.columns
                    if x_label_format is None
                    else map(x_label_format, data.columns)
                ),
            )

            for s in ('right', 'top'):
                axi.spines[s].set_visible(False)

    def draw(
        self,
        ax=None,
        with_node_labels=True,
        node_labels_kwargs=dict(),
        with_edge_labels=True,
        show_negative=False,
        show_positive=True,
        by=None,
        node_size=1000,
        alpha=0,
        edge_labels_kwargs=dict(),
    ):
        G = self.G
        ax = ax or plt.gca()

        if by is not None:
            G = reorient_lattice(G, by=by)

        pos = nx.nx_agraph.graphviz_layout(G, prog='dot')
        try:
            pos = nx.nx_agraph.graphviz_layout(G, prog='dot')
        except:
            print('Graphviz not available. Using Kamada Kawai Layout')
            pos = nx.kamada_kawai_layout(G)

        # node labels
        if with_node_labels is True:
            for v, xy in pos.items():
                s = '\n'.join(self.get_node_label(v))
                ax.annotate(s, xy, va='center', ha='center', **node_labels_kwargs)

        nx.draw_networkx_edges(
            G,
            pos,
            node_size=node_size,
            edge_color=[
                (
                    'black'
                    if by is None or d['test'].loc[by, 'pvalue'] <= alpha
                    else 'lightgray'
                )
                for u, v, d in G.edges(data=True)
            ],
        )

        def create_edge_label(d):
            test = d['test']
            return '\n'.join(
                [
                    f'{"+" if ser.direction > 0 else "- "}{k}'
                    for k, ser in test[test.pvalue <= alpha].iterrows()
                    if (with_edge_labels is True or k in with_edge_labels)
                    and (
                        (show_positive is True and ser.direction > 0)
                        or (show_negative is True and ser.direction < 0)
                    )
                ]
            )

        if with_edge_labels is not False:
            nx.draw_networkx_edge_labels(
                G,
                pos,
                edge_labels={
                    (u, v): create_edge_label(d) for u, v, d in G.edges(data=True)
                },
                **edge_labels_kwargs,
            )

    def specializers_as_hypergraph(self, subset=None):
        df = self.full_specialization

        if subset is not None:
            df = df.loc[subset]

        incidence_dict = {c: df.index[df[c]] for c in df}

        return hnx.Hypergraph(incidence_dict)

    def specializer_cover(self):
        cover = greedy_set_cover(self.full_specialization.values)
        return self.full_specialization.index[cover]


def greedy_set_cover(subsets_data):
    _, universe_size = subsets_data.shape

    uncovered_elements = np.ones(universe_size, dtype=bool)
    chosen_subsets = []

    while np.any(uncovered_elements):
        best_subset_idx = -1
        max_newly_covered = -1

        for i, subset in enumerate(subsets_data):
            # Calculate newly covered elements for this subset
            newly_covered = np.sum(subset[uncovered_elements])

            if newly_covered > max_newly_covered:
                max_newly_covered = newly_covered
                best_subset_idx = i

        if best_subset_idx != -1:
            chosen_subsets.append(best_subset_idx)
            # Update uncovered elements
            uncovered_elements[subsets_data[best_subset_idx] == 1] = False
        else:
            # No subset can cover remaining elements (shouldn't happen with valid input)
            break

    return chosen_subsets


def knn_graph(X, n_neighbors=3, max_distance=1, connected=False, **kwargs):

    D = squareform(pdist(X, **kwargs))

    rank = D.argsort().argsort()
    mask = np.logical_and(rank <= n_neighbors, D <= max_distance)
    A = D.copy()
    A[~mask] = 0

    G = nx.from_numpy_array(A)

    # connect the graph via minimum spanning tree
    if connected:
        T = nx.minimum_spanning_tree(nx.from_numpy_array(D))
        for u, v, d in T.edges(data=True):
            if not G.has_edge(u, v):
                G.add_edge(u, v, spanning=True, **d)

    return G


class DirectTradeoffLattice(TradeoffLattice):
    def __init__(self, *args, whiten=True, non_dominated=False, **kwargs):
        super().__init__(*args, **kwargs)

        df = self.df.loc[self.non_dominated] if non_dominated else self.df

        X = df.values
        if whiten:
            X = (X - X.mean()) / X.std()

        self.G = nx.relabel_nodes(
            knn_graph(X, connected=True), dict(enumerate(df.index))
        )

        for u, v, d in self.G.edges(data=True):
            diff = df.loc[u] - df.loc[v]

            d['test'] = pd.DataFrame(
                dict(magnitude=diff, direction=np.sign(diff), pvalue=0)
            )

    def get_node_label(self, v):
        yield f'# {v}'
        if v in self.generalizers:
            yield '(generalizer)'

        # if v in self.anti_generalizers:
        #     yield '(anti-generalizer)'

        if v in self.specializers.index:
            for c in self.specializers.columns[self.specializers.loc[v]]:
                yield f'+{c}'

        # if v in self.anti_specializers.index:
        #     for c in self.anti_specializers.columns[self.anti_specializers.loc[v]]:
        #         yield f'-{c}'
