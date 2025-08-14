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
        return self.specialization.index[:1]

    @property
    def specializers(self):
        return self.specialization.index

    def plot_pcp(
        self,
        ax=None,
        reorder=True,
        use_rank=True,
        subset=None,
        colors=None,
        generalizers=None,
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

        if generalizers is None:
            generalizers = self.generalizers

        if specialization is None:
            specialization = self.specialization

        order = self.optimal_ovar_order() if reorder else specialization.columns

        x = np.arange(len(order))

        if subset is None:
            subset = self.rank.index
        df = (self.rank if use_rank else self.df).loc[subset, order]

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

            if name in generalizers:
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
