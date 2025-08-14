import matplotlib.pyplot as plt
import pandas as pd
import numpy as np

import networkx as nx
import hypernetx as hnx  # pip install hypernetx


class TradeoffLattice:
    def get_rank(self):
        rank = (self.df[self.ovars] * self.scale).rank(ascending=False)
        rank_order = rank.apply(
            lambda row: tuple(sorted(row, reverse=True)), axis=1
        ).sort_values()

        return rank.loc[rank_order.index].astype(int)

    def get_full_specialization(self, drop=True):
        result = self.rank == self.rank.cummin()

        if drop:
            return result[result.any(axis=1)]

        return result

    def __init__(self, df, ovars, dvars, ascending=[]):
        self.df = df
        self.ovars = ovars
        self.dvars = dvars

        self.scale = pd.Series(1, index=ovars)
        self.scale[ascending] = -1

        self.rank = self.get_rank()
        self.specialization = self.get_full_specialization()

    def to_latex(self, highlight='\\hi', show_score=True, columns=None, index=None):
        R = self.rank
        mask = self.specialization

        R_str = R.map(lambda s: f'{highlight}{{{s}}}')
        R_str[~mask] = (R.astype(str))[~mask]

        if columns is not None:
            R_str.columns = columns

        if index is not None:
            R_str.index = index

        if show_score:
            R_str['$g$'] = R.max(axis=1).astype(str)

        return R_str.fillna('').to_latex(index=True)

    @property
    def generalizers(self):
        return set([self.specialization.index[0]])

    @property
    def specializers(self):
        return self.specialization.index

    # def plot_ovars_parallel_coords(
    #     self,
    #     reorder=True,
    #     use_rank=True,
    #     x_label_format=None,
    #     facets=None,
    #     include_all_generalizers=False,
    #     highlight_generalizers=False,
    #     ax=None,
    # ):

    #     assert (
    #         ax is None or facets is None
    #     ), "When passing an axis, facets=None is required"

    #     data = self.rank

    #     cmap = plt.get_cmap('tab10')
    #     categories = set(data.index.values)
    #     color_map = {cat: cmap(i / len(categories)) for i, cat in enumerate(categories)}

    #     sel_index = self.specializers.index
    #     other_group = self.generalizers
    #     lw_highlight = 1
    #     lw_others = 5
    #     if highlight_generalizers:
    #         sel_index = self.generalizers
    #         other_group = self.specializers.index
    #         lw_highlight = 3
    #         lw_others = 1

    #     if not use_rank:
    #         X = self.df[self.ovars] * self.scale
    #         data = (X - X.mean()) / X.std()

    #     if reorder:
    #         rows = list(set(self.generalizers).union(self.specializers.index))
    #         C = data.loc[rows].corr()
    #         C[C < 0] = 0

    #         A = nx.from_pandas_adjacency(C)
    #         order = nx.spectral_ordering(A)
    #         data = data[order]
    #         # S = sel_index[order]
    #         self.C = C
    #     else:
    #         order = data.columns

    #         self.order = order

    #     x = np.arange(len(data.columns))

    #     # groupby facet for non-generalizers
    #     n = self.n_generalizers

    #     if include_all_generalizers and facets is not None:
    #         grouped = data.iloc[self.n_generalizers :].groupby(
    #             ['All'] * len(data - n) if facets is None else facets[n:]
    #         )
    #     else:
    #         grouped = data.groupby(['All'] * len(data) if facets is None else facets)

    #     for i, (k, data_k) in enumerate(grouped):
    #         # add generalizers back in so they appear in each plot
    #         if include_all_generalizers:
    #             data_k = pd.concat((data.iloc[:n], data_k))

    #         axi = ax or plt.subplot(len(grouped), 1, i + 1)
    #         axi.set_title(k)

    #         if use_rank:
    #             axi.invert_yaxis()

    #         for name, y in data_k.iterrows():
    #             s = None
    #             if name in sel_index:
    #                 kwargs = dict()
    #                 if not highlight_generalizers:
    #                     s = self.specializers.loc[name, order] * 50
    #                 else:
    #                     s = 50
    #                 axi.scatter(x, y, marker='o', s=s, zorder=10, color=color_map[name])
    #                 kwargs = dict(
    #                     linewidth=lw_highlight, color=color_map[name], zorder=8
    #                 )
    #                 s = name
    #             elif name in other_group:
    #                 kwargs = dict(linewidth=lw_others, color='lightgray')
    #                 # s = name
    #             else:
    #                 kwargs = dict(linewidth=0.5, color='lightgray')

    #             if s is not None:
    #                 axi.annotate(
    #                     s,
    #                     (x[-1], y.iloc[-1]),
    #                     va='center',
    #                     ha='left',
    #                     xytext=(5, 0),
    #                     textcoords='offset points',
    #                 )

    #             axi.plot(x, y, **kwargs)

    #         # ax.yaxis.set_label_text('Rank' if use_rank else 'Z-score')
    #         axi.xaxis.set_ticks(
    #             x,
    #             (
    #                 data.columns
    #                 if x_label_format is None
    #                 else map(x_label_format, data.columns)
    #             ),
    #         )

    #         for s in ('right', 'top'):
    #             axi.spines[s].set_visible(False)

    def plot_pcp(
        self,
        ax=None,
        reorder=True,
        use_rank=True,
        colors=None,
        specialization=None,
        specializer_size=75,
        generalizer_linewidth=4,
        specializer_linewidth=2,
        default_linewidth=1,
        specializer_linestyle='-',
        default_linestyle=':',
        labels={},
        x_label_format=None,
    ):
        ax = ax or plt.gca()

        if specialization is None:
            specialization = self.specialization

        order = self.optimal_ovar_order() if reorder else specialization.columns

        x = np.arange(len(order))

        df = (self.rank if use_rank else self.df)[order]

        if colors is None:
            colors = {name: plt.cm.tab10(i % 10) for i, name in enumerate(df.index)}

        n = len(df)
        for i, (name, y) in enumerate(df.iterrows()):
            color = colors[name]

            linewidth = default_linewidth
            linestyle = default_linestyle

            if name in specialization.index:
                linewidth = specializer_linewidth
                linestyle = specializer_linestyle
                facecolor = color
                edgecolor = color

            if name == specialization.index[0]:
                linewidth = generalizer_linewidth
                facecolor = 'white'
                edgecolor = color

            ax.plot(
                x,
                y,
                color=color,
                linewidth=linewidth,
                linestyle=linestyle,
                zorder=n - i,
            )

            if name in self.specializers:
                marker_size = specializer_size * specialization.loc[name, order]
                ax.scatter(
                    x,
                    y,
                    facecolor=facecolor,
                    edgecolor=edgecolor,
                    s=marker_size,
                    linewidth=generalizer_linewidth / 2,
                    zorder=n - i,
                )

            ax.annotate(
                labels.get(name, name),
                (x[-1], y.iloc[-1]),
                va='center',
                ha='left',
                xytext=(specializer_size**0.5, 0),
                textcoords='offset pixels',
            )

        ax.xaxis.set_ticks(
            x,
            (df.columns if x_label_format is None else map(x_label_format, df.columns)),
        )

        if use_rank:
            ax.invert_yaxis()

        for s in ('right', 'top'):
            ax.spines[s].set_visible(False)

    def specializers_as_hypergraph(self, subset=None):
        df = self.specialization

        if subset is not None:
            df = df.loc[subset]

        incidence_dict = {c: df.index[df[c]] for c in df}

        return hnx.Hypergraph(incidence_dict)

    def specializer_cover(self):
        cover = greedy_set_cover(self.specialization.values[1:])
        return self.specialization.index[1:][cover]

    def optimal_ovar_order(self, method='corr'):
        if method == 'corr':
            rows = list(self.specializers)
            C = self.rank.loc[rows].corr()
            C[C < 0] = 0

            A = nx.from_pandas_adjacency(C)
            return nx.spectral_ordering(A)

        if method == 'hypergraph':
            G = self.specializers_as_hypergraph().bipartite()

            return [
                s for s in nx.spectral_ordering(G) if s in self.specialization.columns
            ]


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
