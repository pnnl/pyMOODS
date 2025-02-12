from itertools import product

import numpy as np
import pandas as pd

import matplotlib.pyplot as plt
from matplotlib.patches import ConnectionPatch
from matplotlib.collections import LineCollection
from matplotlib.collections import PolyCollection
from matplotlib.colors import cnames, hex2color

from umap import UMAP

from sklearn.pipeline import Pipeline
from sklearn.linear_model import LogisticRegression
from sklearn.cluster import DBSCAN, HDBSCAN
from sklearn.decomposition import PCA

from scipy.cluster import hierarchy
from scipy.spatial import ConvexHull

from pymoo.algorithms.moo.nsga2 import NSGA2
from pymoo.operators.crossover.sbx import SBX
from pymoo.operators.mutation.pm import PM
from pymoo.operators.sampling.rnd import FloatRandomSampling
from pymoo.problems import get_problem
from pymoo.termination import get_termination
from pymoo.optimize import minimize

import hypernetx as hnx
from collections import defaultdict


class Loader:
    def __init__(self,
        data=None, data_ovars=None, data_dvars=None,
        from_path=None,
        from_problem=None,
        pop_size=200,
        n_offsprings=10,
        n_gen=10000,
        **kwargs
    ):

        if data is not None:
            self.df = data
            self.ovars = data_ovars
            self.dvars = data_dvars
            self.solution_mask = pd.Series(True, index=self.df.index)

        if from_path is not None:
            print('Reading', from_path, '...')
            self.df = pd.read_json(from_path)\
                .reset_index(drop=True)

            self.ovars = [c for c in self.df if c.startswith('f')]
            self.dvars = [c for c in self.df if c.startswith('x')]

            if 'start' in self.df and 'end' in self.df and 'solution_mask' in self.df:
                self.population_metadata = self.df[['start', 'end']]
                self.solution_mask = self.df.solution_mask
                self.df = self.df[self.ovars + self.dvars]
            else:
                self.solution_mask = pd.Series(True, index=self.df.index)

        if from_problem is not None:
            print('Solving...')
            algorithm = NSGA2(
                pop_size=pop_size, n_offsprings=n_offsprings,
                sampling=FloatRandomSampling(),
                crossover=SBX(prob=0.9, eta=15),
                mutation=PM(eta=20),
                eliminate_duplicates=True
            )

            termination = get_termination("n_gen", n_gen)

            self.problem = get_problem(from_problem, **kwargs)
            self.res = minimize(
                self.problem,
                algorithm,
                termination,
                seed=1,
                save_history=True,
                verbose=False
            )

            # format into Loader class
            def get_names(n, prefix='x'):
                return [f'{prefix}{i}' for i in range(n)]

            self.g = g = []
            self.X = X = []
            self.F = F = []
            for i, h in enumerate(self.res.history):
                for p in h.pop:
                    g.append(i)
                    X.append(p.X)
                    F.append(p.F)

            self.dvars = get_names(self.res.X.shape[1], 'x')
            self.ovars = get_names(self.res.F.shape[1], 'f')
            self.df = pd.concat(
                (
                    pd.DataFrame(X, columns=self.dvars, index=g),
                    pd.DataFrame(F, columns=self.ovars, index=g)
                ), 
                axis=1
            )

            population_hash = pd.util.hash_pandas_object(self.df[self.dvars], index=False)
            self.population_metadata = self.df.groupby(population_hash)\
                .apply(lambda df: pd.Series({'start': df.index[0], 'end': df.index[-1]}))

            self.df = self.df.groupby(population_hash).apply(lambda df: df.iloc[0])

            # find which individuals are part of the solution
            solution_set = set(
                pd.util.hash_pandas_object(
                    pd.DataFrame(self.res.X),
                    index=False
                )
            )

            self.solution_mask = pd.Series(
                map(solution_set.__contains__, self.df.index),
                index=self.df.index
            )

    def to_file(self, path):
        path = 'dtlz2_d10_o5_p2000_g10000.json'

        metadata = self.population_metadata.assign(solution_mask=self.solution_mask)
        metadata.columns = ['_' + c for c in metadata]

        pd.concat((metadata, self.df), axis=1)\
            .to_json(path)
            
lightgray = '#edecea'

def get_cluster_hulls(X, y, color=lightgray, marker_color=None, marker_size=5, ax=None, with_labels=True):
    grouped = X.groupby(y)

    s = marker_size**.5 if type(marker_size) in {int, float}\
        else max(marker_size)**.5

    polys = PolyCollection(
        [
            dfk.iloc[ConvexHull(dfk).vertices].values if len(dfk) > 3 else dfk.values
            for k, dfk in grouped
            if k is not None
        ],
        closed=True,
        facecolor=color,
        edgecolor=color,
        linewidth=2*s + 3
    )

    ax = ax or plt.gca()
    ax.add_collection(polys)
    ax.scatter(*X.values.T, s=marker_size, c=marker_color)
    ax.autoscale_view()

    if with_labels:
        for s, row in grouped.mean().iterrows():
            ax.annotate(f'c{s}', row.values, ha='center', va='center', color='red')

def seriate_olo(X):
    def get_index_order(y):
        Z = hierarchy.ward(y)
        return hierarchy.leaves_list(hierarchy.optimal_leaf_ordering(Z, y))

    return X.iloc[
        get_index_order(X),
        get_index_order(X.values.T)
    ]
    
def explain_cluster(X, y, order=None, lw=2, threshold=.55, label='left', ax=None):
    ax = ax or plt.gca()
    if order is None:
        order = np.unique(y)

    clf = LogisticRegression().fit(X, y)
    coef = pd.DataFrame(clf.coef_, columns=X.columns)

    ranges = X.groupby(y).describe()
    colors = plt.cm.tab10(np.arange(len(X.columns)))
    
    dy = np.linspace(-.2, .2, len(X.columns))

    all_points = []
    l, r = '25%', '75%'
    for i, ci in enumerate(order):
        mask = coef.loc[ci] > threshold
        points = ranges.loc[ci]\
            .unstack()[[l, r]]\
            .assign(y=i + dy)

        all_points.append(points[mask].rename(columns={l: 'xmin', r: 'xmax'}))
        
        lines = LineCollection(points.apply(lambda row: [(row[l], row.y), (row[r], row.y)], axis=1))
        lines.set_color(colors)
        lines.set_linewidth(lw*mask)
        
        ax.add_collection(lines)
    
        for s, row in points.iterrows():
            if mask[s]:
                ax.annotate(
                    f' {s} ',
                    (row[l if label == 'left' else r], row.y),
                    va='center',
                    ha='right' if label == 'left' else 'left'
                )
    
    ax.set_yticks(range(len(order)), [f'c{i}' for i in order])
    if label == 'left':
        ax.yaxis.tick_right()
    
    ax.autoscale_view()

    return all_points, coef

def explain_groups(
    X, y,
    colors,
    threshold=0.65,
    ar=3,
    width = 12,
    linewidth_minor = 2,
    linewidth_major = 5
):
    y_names, y_int = np.unique(y, return_inverse=True)
    y_height = np.arange(len(y_names))
    
    #
    
    clf = LogisticRegression().fit(X, y_int)
    
    coef = pd.DataFrame(clf.coef_, columns=X.columns, index=y_names)
    
    default = hex2color(cnames['lightgray']) + (1,)
    
    plt.figure(figsize=(width, width/ar))
    
    nrows, ncols = coef.shape
    
    stats = pd.concat(
        [
            X[y != i].describe(percentiles=[.1, .25, .75, .9]).T
            for i in y_names
        ],
        axis=0,
        keys=y_names
    ).swaplevel().sort_index()
    
    height = dict(zip(y_names, y_height))
    
    for i, col in enumerate(coef):
        ax = plt.subplot(1, ncols, i + 1)
    
        for start, end, weight in [['10%', '90%', linewidth_minor], ['25%', '75%', linewidth_major]]:
            lines = LineCollection([
                [
                    [ser[start], height[row]],
                    [ser[end], height[row]]
                ]
                for row, ser, in stats.loc[col].iterrows()
            ], linewidth=weight, color=default, zorder=0)
            
            ax.add_collection(lines)
    
        color_mask = coef.loc[y, col].abs() >= threshold
        
        ax.scatter(
            X[col], y_int,
            s=100*(1.5*color_mask + 1),
            marker='|',
            c=colors,
            zorder=1,
            alpha=color_mask
        )
    
        plt.xlim(0, 1)
        plt.xlabel(col)
        
        if i == 0:
            plt.yticks(y_height, y_names)
            plt.ylabel('Specialization (cluster)')
        else:
            plt.yticks([], [])
        
        ax.autoscale_view()

    return coef

def show_clusters(points, clusters, columns=None, ax=None, show_legend=True):
    ax = ax or plt.gca()
    if columns is None:
        columns = clusters.columns

    def get_convex_hull(points):
        return points.iloc[ConvexHull(points.values).vertices]

    def lighten(color, alpha=0.75):
        return np.array(color) - np.array([0, 0, 0, alpha])

    if show_legend:
        plt.legend(
            [
                plt.Rectangle(
                    (0, 0), 0, 0,
                    edgecolor=plt.cm.tab10(i),
                    facecolor=lighten(plt.cm.tab10(i))
                )
                for i, c in enumerate(clusters)
            ],
            clusters.columns
        )
            
    ax.scatter(*points.loc[clusters.index].values.T, s=1, c='lightgray')

    for i, c in enumerate(clusters):
        if c in columns:
            ec = plt.cm.tab10(i)
    
            hulls = [
                get_convex_hull(dfk)
                for k, dfk in points.groupby(clusters[c])
                if k != -1
            ]
    
            ax.add_collection(PolyCollection(
                hulls,
                edgecolor=ec,
                facecolor=lighten(ec),
            ))

            mask = clusters[c] != -1
            multi_cluster_mask = (clusters[columns] != -1).sum(axis=1) > 1
            
            ax.scatter(*points.loc[clusters.index][mask & ~multi_cluster_mask].values.T, s=2, color=ec)
            ax.scatter(*points.loc[clusters.index][multi_cluster_mask].values.T, s=2, color='black')

class Visualizer(Loader):
    def __init__(
        self, 
        left=None,
        right=None,
        Projection=UMAP(random_state=123456789, n_jobs=1),
        Cluster=DBSCAN(min_samples=1, eps=.5),
        **kwargs,
    ):

        super().__init__(**kwargs)

        self.left = left or self.ovars
        self.X_left = self.df[self.left]

        self.right = right or self.dvars
        self.X_right = self.df[self.right]

        self.X_joint = self.df[self.left + self.right]

        self.pipe = pipe = Pipeline([
            ('proj', Projection),
            ('clu', Cluster)
        ])
        
        self.y_left =  pd.DataFrame(pipe.fit_predict(self.X_left), index=self.df.index)
        self.left_xy = pd.DataFrame(pipe['proj'].embedding_, index=self.df.index)
        
        self.y_right =  pd.DataFrame(pipe.fit_predict(self.X_right), index=self.df.index)
        self.right_xy = pd.DataFrame(pipe['proj'].embedding_, index=self.df.index)

        self.y_joint =  pd.DataFrame(pipe.fit_predict(self.X_joint), index=self.df.index)
        self.joint_xy = pd.DataFrame(pipe['proj'].embedding_, index=self.df.index)

        # calculate specialization & clusters

        top_k = 20

        label = self.df[self.left]\
            .rank(ascending=False)\
            .idxmin(axis=1)

        rank = self.df.loc[self.solution_mask, self.left]\
            .rank(ascending=False)\
            .min(axis=1)\
            .reindex(self.df.index)

        df = pd.DataFrame(self.right_xy.values, columns=['x', 'y'], index=self.df.index)\
            .assign(label=label.values, is_solution=self.solution_mask)

        clu = HDBSCAN()

        def apply_clustering_to_solutions(df):
            X = df.loc[df.is_solution, ['x', 'y']]
            y = pd.Series(clu.fit_predict(X), index=X.index)\
                .reindex(df.index)\
                .fillna(-1)\
                .astype('int')
            
            return df.assign(cluster=y)

        df_clustered = df.groupby('label')\
            .apply(apply_clustering_to_solutions, include_groups=False)\
            .reset_index('label')\
            .sort_index()

        # update the name of the cluster and 
        mask = (df_clustered.cluster == -1) | (rank > top_k)
        letters = ['i','ii', 'iii', 'iv', 'v', 'vi', 'vii', 'viii', 'ix', 'x']
        def get_letters(i):
            if i >= len(letters):
                return str(i)
            return letters[i]

        df_clustered.cluster = df_clustered.label + ' (' + df_clustered.cluster.map(get_letters) + ')'
        df_clustered.loc[mask, 'cluster'] = None
        self.df_clustered = df_clustered


    def get_overlapping_clusters(self, clu, threshold=1.0, drop_intermediate=False):
        def get_clustering(mask):

            return pd.Series(
                clu.fit_predict(self.joint_xy.loc[mask.index[mask]]),
                index=mask.index[mask]
            )

        df = self.df
        if drop_intermediate:
            df = df[self.solution_mask]

        return pd.DataFrame({
            c: get_clustering(df[c].rank(ascending=False) < threshold*len(df)/len(self.ovars))
            for c in self.ovars
        }).fillna(-1).astype(int)

    def show_overlapping_cluster_grid(
        self,
        s = 4,
        thresholds = [.0625, .125, .25, .5, 1.],
        epsilons = [.1, .3, .5, .7, .9],
    ):
        n_rows = len(thresholds)
        n_cols = len(epsilons)

        diag = n_cols

        plt.figure(figsize=(s*n_cols, s*n_rows))

        for i, t in enumerate(thresholds):
            for j, e in enumerate(epsilons):
                if i + j < n_rows + diag:
                    clusters=self.get_overlapping_clusters(
                        threshold=t,
                        clu = HDBSCAN(
                            cluster_selection_epsilon=e,
                            min_cluster_size=10
                        ),
                        drop_intermediate=False
                    )
                    
                    show_clusters(
                        ax=plt.subplot(n_rows, n_cols, i*n_cols + j + 1),
                        points=self.joint_xy,
                        clusters=clusters,
                        columns=self.ovars,
                        show_legend=False,
                    )
            
                    plt.xticks([], [])
                    plt.yticks([], [])
            
                    if j == 0:
                        plt.ylabel(f'Threshold = {t}')
            
                    if i == 0:
                        plt.title(f'Epsilon = {e}')
                        
    def show_overlapping_clusters(
        self,
        s = 2,
        ncols = 3,
        **kwargs
    ):
        df = self.get_overlapping_clusters(**kwargs)
        points = self.joint_xy.loc[df.index]

        def get_convex_hull(points):
            return points.iloc[ConvexHull(points.values).vertices]

        def get_alpha_hull(points, alpha=0.):
            poly = alphashape.alphashape(points.values, alpha)
            return np.array(poly.exterior.coords.xy).T

        def lighten(color, alpha=0.75):
            return np.array(color) - np.array([0, 0, 0, alpha])

        plt.figure(figsize=(6, 6))
        plt.legend(
            [
                plt.Rectangle(
                    (0, 0), 0, 0,
                    edgecolor=plt.cm.tab10(i),
                    facecolor=lighten(plt.cm.tab10(i))
                )
                for i, c in enumerate(df)
            ],
            df.columns
        )

        ax = plt.subplot(111)
        # plt.xticks([], [])
        # plt.yticks([], [])


        nrows = int(np.ceil(len(self.ovars)/ncols))
        plt.figure(figsize=(s*ncols, s*nrows))

        for i, c in enumerate(df):
            ec = plt.cm.tab10(i)

            hulls = [
                get_convex_hull(dfk)
                for k, dfk in points.groupby(df[c])
                if k != -1
            ]

            ax.add_collection(PolyCollection(
                hulls,
                edgecolor=ec,
                facecolor=lighten(ec),
            ))

            ax.autoscale_view()

            plt.subplot(nrows, ncols, i + 1)
            plt.scatter(*self.joint_xy.values.T, s=1, c='lightgray')
            plt.scatter(*points[df[c] != -1].values.T, s=1, color=ec)
            plt.title(c)
            plt.xticks([], [])
            plt.yticks([], [])

    def show_hypergraph(self, min_size=1, **kwargs):
        df = self.get_overlapping_clusters(**kwargs)

        incidence_dict = defaultdict(list)

        nodes = {}

        for k, dfk in df.groupby(df.columns.tolist()):
            nodes[k] = dfk.index
            if (np.array(k) != -1).sum() > 1:
                for (c, kc) in zip(dfk.columns, k):
                    if kc != -1 and len(dfk) >= min_size:
                        incidence_dict[(c, kc)].append(k)

        H = hnx.Hypergraph(incidence_dict)

        max_len = max(map(len, nodes.values()))
        
        color_map = {c: plt.cm.tab10(i) for i, c in enumerate(df.columns)}
        color = [color_map[c] for c, ci in H.edges()]
        alpha = np.array([0, 0, 0, -.75])

        plt.figure(figsize=(8, 8))
        hnx.draw(
            H,
            with_node_labels=False,
            with_edge_labels=False,
            node_radius={k: (10*(len(v)/max_len)**.5) for k, v in nodes.items()},
            edges_kwargs=dict(
                facecolor=[ci + alpha for ci in color],
                edgecolor=color, linewidth=1
            )
        )


    def show_splom(self, s=2, rows=None, cols=None):
        rows = rows or self.ovars
        cols = cols or self.dvars
        
        nrows = len(rows)
        ncols = len(cols)
        
        plt.figure(figsize=(s*ncols, s*nrows))
        
        for i, ci in enumerate(rows):
            for j, cj in enumerate(cols):
                ax = plt.subplot(nrows, ncols, i*ncols + j + 1)
                plt.scatter(self.df[ci], self.df[cj], marker='.')
                if i == nrows - 1:
                    plt.xlabel(cj)
                else:
                    plt.xticks([])
                if j == 0:
                    plt.ylabel(ci)
                else:
                    plt.yticks([])

    def show_parallel_embeddings(self, s=4, scatter_kwargs={}, connect_cluster=None):
        cluster_points = self.left_xy
        y = self.y_left
        
        cmap = plt.cm.tab10
        norm = plt.Normalize(0, 10)
        color = cmap(norm(y))

        fig = plt.figure(figsize=(2.15*s, s))

        ax1 = plt.subplot(121)
        plt.title(', '.join(self.left))
        plt.scatter(*self.left_xy.T, marker='.', c=color, **scatter_kwargs)
        plt.xticks([])
        plt.yticks([])
        
        ax2 = plt.subplot(122)
        plt.title(', '.join(self.right))
        plt.scatter(*self.right_xy.T, marker='.', c=color, **scatter_kwargs)
        plt.xticks([])
        plt.yticks([])

        if connect_cluster is not None:
            if connect_cluster == 'all':
                mask = np.ones_like(y, dtype='bool')
            else:
                mask = y == connect_cluster
            
            for xyA, xyB, in zip(self.left_xy[mask], self.right_xy[mask]):            
                con = ConnectionPatch(
                    xyA=xyA, coordsA="data", axesA=ax1,
                    xyB=xyB, coordsB="data", axesB=ax2,
                    color="lightgray"
                )
                fig.add_artist(con)            

    def show_joint_clustering(self, ax_left=None, ax_right=None, fig=None):
        fig = fig or plt.figure(figsize=(12, 5))
        ax_left = ax_left or plt.subplot(121)
        ax_right = ax_right or plt.subplot(122)
    
        B = pd.DataFrame({
            'left': self.y_left,
            'right': self.y_right
        })\
            .groupby(['left', 'right'])\
            .size()\
            .unstack()\
            .fillna(0)
                
        left_points = explain_cluster(self.X_left, self.y_left, B.index, ax=ax_left)
        right_points = explain_cluster(self.X_right, self.y_right, B.columns, ax=ax_right, label='right')

        return
            
        for ii, jj in product(*map(range, B.shape)):
            weight = B.loc[ii, jj]
            if weight > 0:
                con = ConnectionPatch(
                    xyA=(left_points[ii].xmax.max() + .05, left_points[ii].y.mean()),
                    xyB=(right_points[jj].xmin.min() - .05, right_points[jj].y.mean()),
                    coordsA="data",
                    coordsB="data",
                    axesA=ax_left,
                    axesB=ax_right,
                    color=lightgray,
                    lw=weight**.5
                )
                fig.add_artist(con)
        
        plt.subplots_adjust(wspace=.4)
    
    def show_joint_clustering_with_embedding(self):
        fig = plt.figure(figsize=(12, 12))
        
        get_cluster_hulls(self.left_xy, self.y_left, ax=plt.subplot(221))
        plt.title(', '.join(self.left))
        plt.axis('off')

        get_cluster_hulls(self.right_xy, self.y_right, ax=plt.subplot(222))
        plt.title(', '.join(self.right))
        plt.axis('off')
        
        self.show_joint_clustering(
        fig=fig,
        ax_left=plt.subplot(223),
        ax_right=plt.subplot(224)
    )

    def show_specialization_clustering(
        self,
        s_min = 5,
        s_max = 25,
        selection={}
    ):
        mask = self.df_clustered.cluster.isnull()

        labels, values = np.unique(self.df_clustered.label, return_inverse=True)
        
        marker_color = plt.cm.tab10(values)
        marker_color[~self.solution_mask] = hex2color(cnames['lightgray']) + (1,)

        
        marker_size = (s_max - s_min)*(~self.df_clustered.cluster.isnull()) + s_min
        marker_size[~self.solution_mask] = 1
        
        fig = plt.figure(figsize=(12, 12))
        
        ax_left = plt.subplot(221)
        get_cluster_hulls(
            self.df_clustered[['x', 'y']],
            self.df_clustered.cluster,
            marker_color=marker_color,
            marker_size=marker_size,
            with_labels=False,
            ax=ax_left
        )
        
        plt.legend(
            [
                plt.Rectangle((0, 0), 0, 0, color=plt.cm.tab10(i))
                for i in range(len(labels))
            ],
            labels,
            loc='lower center',
            bbox_to_anchor=(1.125, 1),
            title='Specialization',
            ncols=len(labels)
        )
        
        plt.xticks([], [])
        plt.yticks([], [])
        
        plt.xlabel('Decision Space (reduced)')
        
        
        ax_right = plt.subplot(222)
        plt.scatter(
            *self.left_xy.values.T,
            c=marker_color,
            s=marker_size
        )
        
        plt.xticks([], [])
        plt.yticks([], [])
        
        plt.xlabel('Objective Space (reduced)')
        
        selected = self.df_clustered.label.apply(lambda i: i in selection or len(selection) == 0)

        for xyA, xyB, c, s in zip(
            self.right_xy[~mask].values,
            self.left_xy[~mask].values,
            marker_color[~mask],
            selected[~mask]
        ):
            con = ConnectionPatch(
                xyA=xyA,
                xyB=xyB,
                coordsA="data",
                coordsB="data",
                axesA=ax_left,
                axesB=ax_right,
                color=c,
                alpha=float(s)
            )
            fig.add_artist(con)
