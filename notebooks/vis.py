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
from sklearn.cluster import DBSCAN
from sklearn.decomposition import PCA

from scipy.cluster import hierarchy
from scipy.spatial import ConvexHull

class Loader:
    def __init__(self, path):
        self.df = pd.read_json(path)
        self.ovars = [c for c in self.df if c.startswith('f')]
        self.dvars = [c for c in self.df if c.startswith('x')]

lightgray = '#edecea'

def get_cluster_hulls(X, y, color=lightgray, marker_color=None, marker_size=5, ax=None, with_labels=True):
    grouped = pd.DataFrame(X).groupby(y)

    s = marker_size**.5 if type(marker_size) in {int, float}\
        else max(marker_size)**.5

    polys = PolyCollection(
        [
            dfk.iloc[ConvexHull(dfk).vertices] if len(dfk) > 3 else dfk
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
    ax.scatter(*X.T, s=marker_size, c=marker_color)
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

    return all_points

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


class Visualizer(Loader):
    def __init__(
        self, path,
        left=None,
        right=None,
        Projection=UMAP(random_state=123456789, n_jobs=1),
        Cluster=DBSCAN(min_samples=1, eps=.5),
    ):

        super().__init__(path)

        self.left = left or self.ovars
        self.X_left = self.df[self.left]

        self.right = right or self.dvars
        self.X_right = self.df[self.right]

        self.X_joint = self.df[self.left + self.right]

        self.pipe = pipe = Pipeline([
            ('proj', Projection),
            ('clu', Cluster)
        ])
        
        self.y_left =  pipe.fit_predict(self.X_left)
        self.left_xy = pipe['proj'].embedding_
        
        self.y_right =  pipe.fit_predict(self.X_right)
        self.right_xy = pipe['proj'].embedding_

        self.y_joint =  pipe.fit_predict(self.X_joint)
        self.joint_xy = pipe['proj'].embedding_

        # calculate specialization & clusters

        top_k = 10

        label = self.df[self.left]\
            .rank(ascending=False)\
            .idxmin(axis=1)

        rank = self.df[self.left]\
            .rank(ascending=False)\
            .min(axis=1)

        df = pd.DataFrame(self.right_xy, columns=['x', 'y'])\
            .assign(label=label)

        clu = DBSCAN(eps=.5, min_samples=3)

        df_clustered = df.groupby('label')\
            .apply(lambda df: df.assign(cluster=clu.fit_predict(df[['x', 'y']])), include_groups=False)\
            .reset_index('label')\
            .sort_index()

        # update the name of the cluster and 
        mask = (df_clustered.cluster == -1) | (rank > top_k)
        letters = ['i','ii', 'iii', 'iv', 'v', 'vi', 'vii', 'viii', 'ix', 'x']
        # df_clustered.cluster = df_clustered.label + ' (' + df_clustered.cluster.apply(lambda i: labels[i]) + ')'
        df_clustered.cluster = df_clustered.label + ' (' + df_clustered.cluster.map(letters.__getitem__) + ')'
        df_clustered.loc[mask, 'cluster'] = None
        self.df_clustered = df_clustered

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
        s_min = 3,
        s_max = 25,
        selection={}
    ):
        mask = self.df_clustered.cluster.isnull()

        labels, values = np.unique(self.df_clustered.label, return_inverse=True)
        
        marker_color = plt.cm.tab10(values)
        
        marker_size = (s_max - s_min)*(~self.df_clustered.cluster.isnull()) + s_min
        
        fig = plt.figure(figsize=(12, 12))
        
        ax_left = plt.subplot(221)
        get_cluster_hulls(
            self.df_clustered[['x', 'y']].values,
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
            *self.left_xy.T,
            c=marker_color,
            s=marker_size
        )
        
        plt.xticks([], [])
        plt.yticks([], [])
        
        plt.xlabel('Objective Space (reduced)')
        
        selected = self.df_clustered.label.apply(lambda i: i in selection or len(selection) == 0)
        
        for xyA, xyB, c, s in zip(
            self.right_xy[~mask],
            self.left_xy[~mask],
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