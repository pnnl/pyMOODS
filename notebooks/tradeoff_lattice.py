import hashlib

import pandas as pd
import numpy as np

import matplotlib.pyplot as plt
import seaborn as sns

import networkx as nx
import hypernetx as hnx  # pip install hypernetx

from scipy.spatial import Delaunay
from scipy.stats import mannwhitneyu

def test_all(X, Y):
    result = pd.DataFrame([
        mannwhitneyu(X[c], Y[c])
        for c in X
    ], index=X.columns)

    df = pd.DataFrame([X.median(), Y.median()])
    result['magnitude'] = df.max() / df.min()

    result['direction'] = np.sign(result.statistic/(len(X)*len(Y)) - .5)
    
    return result
    
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

def _stable_color(name, cmap=None, n=10):
    """Return a consistent color for *name* regardless of iteration order.

    Uses an MD5 hash of the string representation so the same solution always
    maps to the same tab10 slot even when used across different loop iterations.
    Pass a custom *cmap* (any callable accepting a float in [0, 1]) to override
    the default tab10 palette.
    """
    if cmap is None:
        cmap = plt.cm.tab10
    idx = int(hashlib.md5(str(name).encode()).hexdigest(), 16) % n
    return cmap(idx / n)


class TradeoffLattice:
    def __init__(self, df, ovars, dvars, ascending=[], reorder='corr'):
        """
        Create a tradeoff lattice object

        This will compute and reorder the columns of the rank matrix, which is
        then used for computing generalization, specializers, and tradeoffs.

        Parameters
        ----------
        df: pandas.DataFrame
            DataFrame containing objective and decision variables
        ovars: list
            list of objective variable names (subset of df.columns)
        dvars: list
            list of decision variable names (subset of df.columns)
        ascending: list
            list of objective variable names where larger values are better
        reorder: str
            name of approach to reorder the rank matrix columns, defaults to rank matrix correlation 
        """

        self.df = df
        self.ovars = ovars
        self.dvars = dvars

        self.scale = pd.Series(1, index=ovars)
        self.scale[ascending] = -1

        self.rank, self.rank_order = self._get_rank()

        self.reorder_rank_columns(reorder)

    def _get_rank(self):
        """
        Compute the rank matrix of the input DataFrame

        After the ranking of the input DataFrame is computed, the sorted rank
        tuples are used to break rank ties and sort the rank matrix by
        generalizability.

        Returns
        -------
        pandas.DataFrame
            rank matrix sorted by generalizability
        pandas.Series
            mapping of self.df.index -> sorted rank tuples (used to compute generalizability)
        """

        rank = (self.df[self.ovars] * self.scale).rank(ascending=False)
        rank_order = rank.apply(
            lambda row: tuple(sorted(row, reverse=True)), axis=1
        ).sort_values()

        return rank.loc[rank_order.index].astype(int), rank_order

    def _get_generalizability_str(self):
        X = np.vstack(self.rank_order.values)

        r, c = X.shape
        f = np.ones((1, c), dtype='bool')
        B = X[:-1, :] != X[1:, :]

        Ba = np.vstack((f, B))
        Bb = np.vstack((B, f))

        depth = np.logical_and(Ba, Bb).argmax(axis=1) + 1

        return pd.Series(
            [
                ','.join(str(int(s)) for s in v[:d])
                for v, d in zip(self.rank_order.values, depth)
            ],
            index=self.rank_order.index,
        )

    def _rank_compare(self, other, drop=True):
        result = self.rank == other
        result.iloc[0, :] = False

        if drop:
            return result[result.any(axis=1)]

        return result

    @property
    def specialization(self):
        """
        Finds the specializers.

        Specialzers are solutions (rows) where an objective is ranked *better*
        than all solutions it is less general than. Not all solutions are 
        specializers--these will be omitted from the returned DataFrame.

        Returns
        -------
        pandas.DataFrame
            Boolean DataFrame where cell (i, j) is True if solution i specializes in objective variable j
        """
        return self._rank_compare(self.rank.cummin())

    @property
    def tradeoff(self):
        """
        Finds the tradeoffs.

        Tradeoffs are solutions (rows) where an objective is ranked *worse*
        than all solutions it is less general than.

        Returns
        -------
        pandas.DataFrame
            Boolean DataFrame where cell (i, j) is true if solution i specializes in objective variable j
        """
        return self._rank_compare(self.rank.cummax())

    @property
    def generalizers(self):
        """
        The solutions considered to be generalizers (legacy)

        Returns
        -------
        list
            The most general solution is the only generalizer in this implementation
        """
        return self.rank.index[:1]

    @property
    def specializers(self):
        """
        The set of solutions having a specialization in at least one objective

        Returns
        -------
        list
            list of specializers
        """
        return self.specialization.index

    def to_latex(
        self,
        special='\\cir',
        trade='\\sqr',
        show_score=True,
        columns=None,
        index=None,
        notes=None,
    ):
        order = list(self.rank.columns)

        R = self.rank[order]
        R_str = R.astype(str)

        # fill in specializers
        mask = self.specialization[order].reindex(R.index, fill_value=False)
        R_str[mask] = R.map(lambda s: f'{special}{{{s}}}')[mask]

        # fill in tradeoffs
        mask = self.tradeoff[order].reindex(R.index, fill_value=False)
        R_str[mask] = R.map(lambda s: f'{trade}{{{s}}}')[mask]

        if columns is not None:
            R_str.columns = columns

        if index is not None:
            R.index = index
            R_str.index = index

        if show_score:
            R_str['$g$'] = self._get_generalizability_str().tolist()

        if notes is not None:
            R_str = R_str.assign(notes=notes)

        return R_str.fillna('').to_latex(index=True)

    def specialization_at_k(self, k):
        """
        Alternative implementation of specialization (legacy)

        This approach defines specialization as a solution performing better
        than the k most general solutions in a particular objective.

        Parameters
        ----------
        k : int
            the number of generalizers to consider

        Returns
        -------
        pandas.DataFrame
            Boolean DataFrame where cell (i, j) is true if solution i specializes in objective variable j
        """

        S = self.rank < self.rank.iloc[:k].min(axis=0)
        S.iloc[:k] = self.specialization.iloc[:k]
        return S[S.any(axis=1)]

    def get_node_label(self, v):
        yield f'# {v}'
        if v in self.generalizers:
            yield '(generalizer)'

        # if v in self.anti_generalizers:
        #     yield '(anti-generalizer)'

        if v in self.specialization.index:
            for c in self.specialization.columns[self.specialization.loc[v]]:
                yield f'+{c}'

        # if v in self.anti_specializers.index:
        #     for c in self.anti_specializers.columns[self.anti_specializers.loc[v]]:
        #         yield f'-{c}'
                
    def plot_pcp(
        self,
        ax=None,
        use_rank=True,
        show_generalizability_as='Generalizability',
        subset=None,
        colors=None,
        color_cmap=None,
        specialization_marker='o',
        tradeoff_marker='s',
        generalizers=None,
        specialization=None,
        tradeoff=None,
        show_tradeoff=True,
        specializer_size=75,
        generalizer_linewidth=3,
        specializer_linewidth=3,
        default_linewidth=1,
        generalizer_linestyle='--',
        specializer_linestyle='-',
        default_linestyle='-',
        specializer_alpha=1.0,
        generalizer_alpha=1.0,
        default_alpha=1.0,
        annotation_fontsize=None,
        x_label_rotation=0,
        column_order=None,
        labels={},
        x_labels={},
    ):
        """
        Parallel coordinates plot of objectives including encodings generalzers, specialzers, and tradeoffs

        Parameters
        ----------
        ax : matplotlib Axis
            axis to render plot. Uses current axis by default
        use_rank : bool
            Encode y-axis using rankings; if False, uses original values from input DataFrame
        show_generalizability_as : str
            Label for right most column showing generalizability; if None, do not show this column
        subset : list
            subset of solutions to show
        colors : dict
            mapping of solution name -> color; if None, colors are assigned by hashing the solution
            name so the same solution always receives the same color across loop iterations
        color_cmap : matplotlib colormap
            colormap used when auto-generating colors from solution names (default: tab10)
        specialization_marker : str
            matplotlib marker character to indicate specialization
        tradeoff_marker : str
            matplotlib marker character to indicate tradeoff
        generalizers : list
            solutions to be encoded as generalizers; if None, uses the single the most general solution
        specialization : pandas.DataFrame
            custom specialization DataFrame, if None, uses self.specialization
        tradeoff : pandas.DataFrame
            custom tradeoff DataFrame, if None, uses self.tradeoff
        show_tradeoff : bool
            if False, will not show tradeoffs markers in the visualization
        specializer_size : int
            size of specialization and tradeoff marker
        generalizer_linewidth : int
            width of lines for solutions that are generalizers
        specializer_linewidth : int
            width of lines for solutions that are specializers
        default_linewidth : int
            width of lines for solutions that are neither specializers nor generalizers
        generalizer_linestyle : str
            style of lines for solutions that are generalizers (defaults to dashed)
        specializer_linestyle : str
            style of lines for solutions that are specializers (defaults to solid)
        default_linestyle : str
            style of lines for solutions that are neither specializers nor generalizers
        specializer_alpha : float
            alpha (opacity) for specializer lines and their annotations (default 1.0)
        generalizer_alpha : float
            alpha (opacity) for generalizer lines and their annotations (default 1.0)
        default_alpha : float
            alpha (opacity) for all other lines and their annotations (default 1.0)
        annotation_fontsize : float or None
            font size for right-hand labels; if None uses matplotlib's default
        x_label_rotation : float
            rotation angle in degrees for x-axis tick labels (default 0); use e.g. 45 or 90
            when labels overlap
        column_order : list or None
            custom ordering of objective columns on the x-axis; must be a permutation of the
            objective variable names (excluding the generalizability column). If None, uses the
            order from the rank matrix (set by reorder_rank_columns)
        labels : dict
            mapping of DataFrame index -> human readable string in visualization
        x_labels : dict
            mapping of DataFrame column -> human readable string in visualization
        """

        ax = ax or plt.gca()

        if generalizers is None:
            generalizers = self.generalizers

        if specialization is None:
            specialization = self.specialization.copy()

        if tradeoff is None:
            tradeoff = self.tradeoff.copy()

        order = list(column_order) if column_order is not None else list(specialization.columns)

        if subset is None:
            subset = self.rank.index
        df = (self.rank if use_rank else self.df).loc[subset, order]

        if show_generalizability_as is not None:
            df[show_generalizability_as] = np.arange(len(df)) + 1
            specialization[show_generalizability_as] = False
            tradeoff[show_generalizability_as] = False
            order.append(show_generalizability_as)

        x = np.arange(len(order))

        # Use hash-based stable colors so the same solution name always maps to
        # the same color slot regardless of iteration order in a for loop.
        if colors is None:
            colors = {name: _stable_color(name, cmap=color_cmap) for name in df.index}

        n = len(df)
        for i, (name, y) in enumerate(df.iterrows()):
            facecolor = edgecolor = color = colors[name]

            linewidth = default_linewidth
            linestyle = default_linestyle
            alpha = default_alpha
            fontweight = 'normal'
            fontstyle = 'normal'

            if name in specialization.index:
                linewidth = specializer_linewidth
                linestyle = specializer_linestyle
                alpha = specializer_alpha
                fontstyle = 'italic'

            if name in generalizers:
                linestyle = generalizer_linestyle
                linewidth = generalizer_linewidth
                alpha = generalizer_alpha
                fontweight = 'bold'
                fontstyle = 'normal'
                facecolor = 'none'
                edgecolor = 'none'

            ax.plot(
                x,
                y,
                color=color,
                linewidth=linewidth,
                linestyle=linestyle,
                alpha=alpha,
                zorder=n - i,
            )

            if name in specialization.index:
                marker_size = specializer_size * specialization.loc[name, order]
                ax.scatter(
                    x,
                    y,
                    marker=specialization_marker,
                    facecolor=facecolor,
                    edgecolor=edgecolor,
                    s=marker_size,
                    alpha=alpha,
                    linewidth=generalizer_linewidth / 2,
                    zorder=n - i,
                )

            if show_tradeoff and name in tradeoff.index:
                marker_size = specializer_size * tradeoff.loc[name, order]
                ax.scatter(
                    x,
                    y,
                    marker=tradeoff_marker,
                    facecolor=facecolor,
                    edgecolor=edgecolor,
                    s=marker_size / 2,
                    alpha=alpha,
                    linewidth=generalizer_linewidth / 2,
                    zorder=n - i,
                )

            annotation_kwargs = dict(
                va='center',
                ha='left',
                xytext=(specializer_size**0.5, 0),
                textcoords='offset pixels',
                color=color,
                alpha=alpha,
                fontweight=fontweight,
                fontstyle=fontstyle,
            )
            if annotation_fontsize is not None:
                annotation_kwargs['fontsize'] = annotation_fontsize

            ax.annotate(labels.get(name, name), (x[-1], y.iloc[-1]), **annotation_kwargs)

        ax.xaxis.set_ticks(
            x,
            [x_labels.get(s, s) for s in df.columns],
            rotation=x_label_rotation,
            ha='right' if x_label_rotation else 'center',
        )

        if use_rank:
            ax.invert_yaxis()

        for s in ('right', 'top'):
            ax.spines[s].set_visible(False)

    @property
    def specialization_and_tradeoff(self):
        """
        Combined matrix of specializers with their tradeoffs

        Returns
        -------
        pandas.DataFrame
            integer DataFrame where specialization is +1 and tradeoff is -1 and 0 otherwise
        """

        index = self.specialization.index.union(self.tradeoff.index)

        def reindex(df):
            return df.astype(int).reindex(index, fill_value=0)

        return reindex(self.specialization) - reindex(self.tradeoff)

    def plot_heatmap(
        self,
        cmap=plt.cm.bwr_r,
        vmin=-1,
        vmax=1,
        show_ranks=True,
        **kwargs,
    ):
        """
        Heatmap visualization colored according to specialization versus tradeoff

        Parameters
        ----------
        cmap : matplotlib colormap
            ideally a divergent color scale
        vmin : float
            normalized beginning of color scale; e.g. set to -1.5 to not use some of the colors
        vmax : float
            normalized ending of color scale; e.g. set to 1.5 to not use some of the colors
        show_ranks : bool
            if false, does not annotate each cell with its rank
        **kwargs : dict
            additional keyword arguments passed through to seaborn.clustermap
        """

        n = len(self.rank)
        index = self.specialization.index
        R = self.rank.loc[index]

        data = (((n + 1 - R) * self.specialization) - R * self.tradeoff.loc[index]) / 10

        cm = sns.clustermap(
            data,
            cmap=cmap,
            vmin=vmin,
            vmax=vmax,
            cbar=False,
            annot=R if show_ranks else None,
            **kwargs,
        )

        norm = plt.Normalize(vmin, vmax)

        cm.ax_heatmap.legend(
            [
                plt.Rectangle((0, 0), 0, 0, color=cmap(norm(1))),
                plt.Rectangle((0, 0), 0, 0, color=cmap(norm(-1))),
            ],
            [
                'Specialization',
                'Tradeoff',
            ],
            loc='lower left',
            bbox_to_anchor=(1, 1),
        )

        cm.cax.set_visible(False)

        return cm

    def specializers_as_hypergraph(self, specialization=None, cover=False):
        """
        Hypergraph representation of specialization DataFrame

        Treats the specialization DataFrame as an incidence matrix

        Parameters
        ----------
        specialization : pandas.DataFrame
            provide a custom specialization; if None uses self.specialization
        cover : bool
            if True, reduces the number of nodes in the hypergraph via greedy set cover

        Returns
        -------
        hypernetx.Hypergraph
        """

        if specialization is None:
            specialization = self.specialization

        if cover:
            specialization = specialization.iloc[
                greedy_set_cover(specialization.values)
            ]

        rows = [
            {'edges': c, 'nodes': node}
            for c in specialization
            for node in specialization.index[specialization[c]]
        ]

        return hnx.Hypergraph(pd.DataFrame(rows), edge_col='edges', node_col='nodes')

    def plot_hypergraph_euler(self, cover=False, **kwargs):
        """
        Draw the specialization DataFrame as an Euler diagram

        Parameters
        ----------
        cover : bool
            if True, reduces the number of nodes in the hypergraph via greedy set cover
        **kwargs : dict
            arguments passed through to the hypernetx.draw method
        """

        H = self.specializers_as_hypergraph(cover=cover)
        return hnx.draw(H, **kwargs)

    def plot_hypergraph_upset(self, cover=False, order=None, **kwargs):
        """
        Draw the specialization DataFrame as an UpSet like diagram

        Parameters
        ----------
        cover : bool
            if True, reduces the number of nodes in the hypergraph via greedy set cover
        order : list
            specify the x-axis ordering of ovars
        **kwargs : dict
            arguments passed through to the hypernetx.draw method
        """
        H = self.specializers_as_hypergraph(cover=cover).dual()

        hnx.draw_incidence_upset(
            H,
            edge_order=order,
            edge_labels_kwargs=dict(va='top', ha='left', rotation=-45),
            **kwargs
        )

    @property
    def bipartite(self):
        """
        Bipartite graph representation of specialization and tradeoff

        Returns
        -------
        networkx.Graph
            A bipartite graph G=(V, E) where edge (u, v) is in E if solution u specializes or trades off ovar v
        """
        G = nx.Graph()

        data = self.specialization_and_tradeoff

        ser = data.unstack()

        for (source, target), weight in ser[ser != 0].items():
            G.add_edge(source, target, direction=weight)

        return G

    def plot_tradeoff_lattice(
        self,
        pos=None,
        layout=None,
        layout_kwargs={},
        labels={},
        cmap=plt.cm.bwr_r,
        vmin=-1.5,
        vmax=1.5,
        width=2,
        small_font=8,
        large_font=10,
        ax=None,
    ):
        """
        Tradeoff Lattice bipartite visualization

        Node-link visualization of bipartite tradeoff lattice with color to indicate specialization or tradeoff

        Parameters
        ----------

        pos : dict
            xy coordinates of graph nodes (solutions and ovars)
        layout : func
            function to map graph to xy coordinates if pos is None
        layout_kwargs : dict
            arguments passed to layout function
        labels : dict
            mapping of solution or ovar to string label
        cmap : matplotlib color scale
            color scale to use for edges (tradeoffs and specializers)
        vmin : float
            custom normalized color scale starting point
        vmax : float
            custom normalized color scale ending point
        width : float
            edge width
        small_font : int
            small font size used for solution node labels
        large_font : int
            large font size used for ovar node labels
        ax : matplotlib Axis
            axis for drawing; defaults to current axis
        """
        ax = ax or plt.gca()

        G = self.bipartite

        if pos is None:
            if layout is None:
                try:
                    pos = nx.nx_agraph.graphviz_layout(G, **layout_kwargs)
                except:
                    print('Graphviz failed, using nx.kamada_kawai_layout')
                    pos = nx.kamada_kawai_layout(G)
            else:
                pos = layout(G, **layout_kwargs)

        draw_kwargs = dict(G=G, pos=pos, ax=ax)

        for v, xy in pos.items():
            s = labels.get(v, v)

            c1 = 'black'
            c2 = 'white'
            fontweight = None
            fontsize = small_font

            if v not in self.rank.index:
                c1, c2 = c2, c1
                fontweight = 'bold'
                fontsize = large_font

            ax.annotate(
                s,
                xy,
                ha='center',
                va='center',
                color=c1,
                fontweight=fontweight,
                fontsize=fontsize,
                bbox=dict(edgecolor=c1, facecolor=c2, alpha=0.85),
            )

        norm = plt.Normalize(vmin, vmax)
        color = [cmap(norm(d['direction'])) for u, v, d in G.edges(data=True)]

        nx.draw_networkx_edges(
            **draw_kwargs,
            edge_color=color,
            width=width,
        )

        ax.axis('off')

    def plot_specializers_and_tradeoff_as_hypergraph(
        self,
        node_labels={},
        edge_labels={},
        node_color_by=None,
        node_cmap=plt.cm.viridis,
        node_size_by=None,
        node_size_scale=2,
        smin=None,
        smax=None,
        cmap=plt.cm.bwr_r,
        seed=None,
        figsize=None,
        edge_labels_kwargs=None,
        node_labels_kwargs=None,
        **kwargs,
    ):
        """
        Tradeoff Lattice Euler visualization

        Euler visualization (generalization of a "Venn diagram") of the
        specializers and tradeoffs as a hypergraph. Solutions are represented
        as nodes and ovar specialization or tradeoff are reprseneted as hyper
        edges.

        Parameters
        ----------
        node_labels : dict
            mapping of solution to string label
        edge_labels : dict
            mapping of ovar to string label
        node_color_by : str
            name of column in input DataFrame to color nodes by
        node_cmap : matplotlib color scale
            color maping for nodes
        node_size_by : str
            name of column in input DataFrame to size nodes by
        node_size_scale : float
            constant that affects the size of the nodes relative to the area of the plot
        smin : float
            lower endpoint of the size scale--useful to set to zero to prevent nodes of zero size
        smax : float
            upper endpoint of the size scale
        cmap : matplotlib color scale
            color mapping for edges; ideally a divergent color scale
        edge_labels_kwargs : dict
            keyword arguments passed to the edge label text rendering; defaults add a white
            background box and horizontal (non-rotated) text to reduce overlap
        node_labels_kwargs : dict
            keyword arguments passed to the node label text rendering
        """
        
        # Build edge metadata: string key -> (ovar, sign)
        edge_meta = {}
        rows = []
        for c in self.specialization.columns:
            key = f"{c}__pos"
            edge_meta[key] = (c, 1)
            for node in self.specialization.index[self.specialization[c]]:
                rows.append({'edges': key, 'nodes': node})

        spec_idx = self.specialization.index
        tradeoff_restricted = self.tradeoff.loc[self.tradeoff.index.intersection(spec_idx)]
        for c in tradeoff_restricted.columns:
            members = tradeoff_restricted.index[tradeoff_restricted[c]].tolist()
            if not members:
                continue
            key = f"{c}__neg"
            edge_meta[key] = (c, -1)
            for node in members:
                rows.append({'edges': key, 'nodes': node})

        H = hnx.Hypergraph(pd.DataFrame(rows), edge_col='edges', node_col='nodes')
        all_nodes = list(H.nodes)

        def scale(by, vmin=None, vmax=None, alpha=1, beta=1):
            s = self.df.loc[all_nodes, by]
            vmin = s.min() if vmin is None else vmin
            vmax = s.max() if vmax is None else vmax
            return alpha * (((s - vmin) / (vmax - vmin)) ** beta)

        norm = plt.Normalize(-1, 1)

        nodes_kwargs = {}
        if node_color_by is not None:
            fc = node_cmap(scale(node_color_by))
            nodes_kwargs['facecolors'] = lambda v, _fc=fc, _nodes=all_nodes: (
                _fc[_nodes.index(v)] if v in _nodes else 'white'
            )

        if node_size_by is not None:
            raw = scale(node_size_by, smin, smax, node_size_scale, 0.5)
            node_radius = raw.clip(lower=1e-6).to_dict()
        else:
            node_radius = None

        # Only inject seed into layout_kwargs when using the default spring_layout.
        layout_fn = kwargs.pop('layout', None)
        if layout_fn is not None:
            kwargs['layout'] = layout_fn
        if seed is not None and layout_fn is None:
            lk = kwargs.pop('layout_kwargs', {})
            lk.setdefault('seed', seed)
            kwargs['layout_kwargs'] = lk

        _edge_label_style = dict(
            rotation=0,
            fontsize=9,
            bbox=dict(boxstyle='round,pad=0.2', facecolor='white', edgecolor='black', alpha=1),
        )
        if edge_labels_kwargs is not None:
            _edge_label_style.update(edge_labels_kwargs)

        _node_label_style = dict(
            fontsize=10,
            bbox=dict(boxstyle='round,pad=0.2', facecolor='white', edgecolor='none', alpha=0.75),
        )
        if node_labels_kwargs is not None:
            _node_label_style.update(node_labels_kwargs)

        if figsize is not None and 'ax' not in kwargs:
            _, ax = plt.subplots(figsize=figsize)
            kwargs['ax'] = ax
        ax = kwargs.get('ax') or plt.gca()
        texts_before = set(id(t) for t in ax.texts)

        hnx.draw(
            H,
            node_labels=lambda v, _nl=node_labels: _nl.get(v, v),
            edge_labels=lambda e, _el=edge_labels, _em=edge_meta: (
                _el.get(_em[e][0], _em[e][0]) if e in _em else e
            ),
            edges_kwargs=dict(
                edgecolors=lambda e, _em=edge_meta, _cmap=cmap, _norm=norm: (
                    _cmap(_norm(_em[e][1])) if e in _em else (0.5, 0.5, 0.5, 1)
                ),
                facecolors=lambda e, _em=edge_meta, _cmap=cmap, _norm=norm: (
                    (*_cmap(_norm(_em[e][1]))[:3], 0.2)
                    if e in _em and _em[e][1] > 0
                    else (0, 0, 0, 0)
                ),
                linewidth=2,
            ),
            node_radius=node_radius,
            nodes_kwargs=nodes_kwargs,
            **kwargs
        )

        new_texts = [t for t in ax.texts if id(t) not in texts_before]
        node_set = set(all_nodes)
        label_to_node = {node_labels.get(v, v): v for v in all_nodes}

        edge_texts_to_adjust = [] # Keep track of edge labels for adjustment
        
        # Style every new text: node labels and edge labels both get white background
        # boxes and high zorder. Edge labels keep hnx's original position; rotation=0
        # keeps them horizontal so they are legible even when overlapping.
        for txt in new_texts:
            content = txt.get_text()
            is_node = content in label_to_node or content in node_set
            style = _node_label_style if is_node else _edge_label_style
            txt.set_rotation(style.get('rotation', txt.get_rotation()))
            txt.set_fontsize(style.get('fontsize', txt.get_fontsize()))
            if 'bbox' in style:
                txt.set_bbox(style['bbox'])
            txt.set_zorder(20)
            
            # If it's an edge label, add it to our adjustment list
            if not is_node:
                edge_texts_to_adjust.append(txt)

        # --- NEW CODE TO FIX OVERLAPS ---
        try:
            from adjustText import adjust_text
            # Push the edge labels away from each other
            adjust_text(
                edge_texts_to_adjust, 
                ax=ax,
                expand_points=(1.2, 1.2), # Add a little padding
                arrowprops=dict(arrowstyle='-', color='gray', lw=0.5, alpha=0.5) # Optional: draws a faint line back to the original centroid if moved far
            )
        except ImportError:
            print("Warning: 'adjustText' library not found. Install it to prevent label overlap.")

    def draw(self, ax=None, with_node_labels=True, node_labels_kwargs=dict(), with_edge_labels=True, show_negative=False, show_positive=True, by=None, node_size=1000, alpha=0, edge_labels_kwargs=dict()):
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
                # print(s)
                ax.annotate(s, xy, va='center', ha='center', **node_labels_kwargs)
    
        nx.draw_networkx_edges(
            G, pos,
            node_size=node_size,
            edge_color=[
                'black' if by is None or d['test'].loc[by, 'pvalue'] <= alpha else 'lightgray'
                for u, v, d in G.edges(data=True)
            ]
        )
    
        def create_edge_label(d):
            test = d['test']
            return '\n'.join([
                f'{"+" if ser.direction > 0 else "- "}{k}'
                for k, ser in test[test.pvalue <= alpha].iterrows()
                if (with_edge_labels is True or k in with_edge_labels) and (
                    (show_positive is True and ser.direction > 0) or\
                    (show_negative is True and ser.direction < 0)
                )
            ])
    
        if with_edge_labels is not False:
            nx.draw_networkx_edge_labels(
                G, pos,
                edge_labels={
                    (u, v): create_edge_label(d)
                    for u, v, d in G.edges(data=True)
                },
                **edge_labels_kwargs
            )   

    def reorder_rank_columns(self, method='corr'):
        """
        Reorder the rank matrix

        The columns of the rank matrix can be reoredered to help reveal
        patterns in the rankings or specialization/tradeoff. Two methods are
        implemented here: 'corr' and 'hypergraph'.

        The 'corr' (rank correlation) approach finds the correlation between
        the columns of the rank matrix and constructs a graph where edges
        correspond to positive correlation. The new rank order is found from
        the spectral order of this graph.

        The 'hypergraph' approach represents the specialization matrix as a
        bipartite graph, then finds the new rank order from the spectral order
        of this graph.

        Parameters
        ----------
        method : str
            name of method used to reorder the rank matrix
        """

        # Allow passing a custom column order directly as a list/tuple.
        if not isinstance(method, str):
            self.rank = self.rank[list(method)]
            return

        order = self.rank.columns

        if method == 'corr':
            rows = list(self.specializers)
            C = self.rank.loc[rows].corr()
            C[C < 0] = 0
            C_arr = C.values.copy()
            np.fill_diagonal(C_arr, 0)
            C = pd.DataFrame(C_arr, index=C.index, columns=C.columns)

            A = nx.from_pandas_adjacency(C)
            order = nx.spectral_ordering(A)

        if method == 'hypergraph':
            G = self.specializers_as_hypergraph().bipartite()

            order = [
                s for s in nx.spectral_ordering(G) if s in self.specialization.columns
            ]

        self.rank = self.rank[order]


def greedy_set_cover(subsets_data):
    """
    Approximation of the greedy set cover problem using numpy

    Parameters
    ----------
    subsets_data : 2-d numpy array
        representation of set memberships (rows denote sets, columns denote the "universe" to be covered)
    """
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
