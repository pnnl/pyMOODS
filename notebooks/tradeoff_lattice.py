import pandas as pd
import numpy as np

import matplotlib.pyplot as plt
import seaborn as sns

import networkx as nx
import hypernetx as hnx  # pip install hypernetx


class TradeoffLattice:
    def __init__(self, df, ovars, dvars, ascending=[]):
        self.df = df
        self.ovars = ovars
        self.dvars = dvars

        self.scale = pd.Series(1, index=ovars)
        self.scale[ascending] = -1

        self.rank, self.rank_order = self._get_rank()

    def _get_rank(self):
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
        return self._rank_compare(self.rank.cummin())

    @property
    def tradeoff(self):
        return self._rank_compare(self.rank.cummax())

    @property
    def generalizers(self):
        return self.rank.index[:1]

    @property
    def specializers(self):
        return self.specialization.index

    def to_latex(
        self,
        special='\\cir',
        trade='\\sqr',
        show_score=True,
        columns=None,
        index=None,
        notes=None,
        reorder='corr',
    ):
        order = (
            self.rank.columns if reorder is False else self.optimal_ovar_order(reorder)
        )

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
        S = self.rank < self.rank.iloc[:k].min(axis=0)
        S.iloc[:k] = self.specialization.iloc[:k]
        return S[S.any(axis=1)]

    def plot_pcp(
        self,
        ax=None,
        reorder='corr',
        use_rank=True,
        show_generalizability_as='Generalizability',
        subset=None,
        colors=None,
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
        labels={},
        x_labels={},
    ):
        ax = ax or plt.gca()

        if generalizers is None:
            generalizers = self.generalizers

        if specialization is None:
            specialization = self.specialization.copy()

        if tradeoff is None:
            tradeoff = self.tradeoff.copy()

        order = (
            self.optimal_ovar_order(reorder)
            if reorder is not None
            else specialization.columns
        )

        if subset is None:
            subset = self.rank.index
        df = (self.rank if use_rank else self.df).loc[subset, order]

        if show_generalizability_as is not None:
            df[show_generalizability_as] = np.arange(len(df)) + 1
            specialization[show_generalizability_as] = False
            tradeoff[show_generalizability_as] = False
            order.append(show_generalizability_as)

        x = np.arange(len(order))

        if colors is None:
            colors = {name: plt.cm.tab10(i % 10) for i, name in enumerate(df.index)}

        n = len(df)
        for i, (name, y) in enumerate(df.iterrows()):
            facecolor = edgecolor = color = colors[name]

            linewidth = default_linewidth
            linestyle = default_linestyle

            if name in specialization.index:
                linewidth = specializer_linewidth
                linestyle = specializer_linestyle

            if name in generalizers:
                linestyle = generalizer_linestyle
                linewidth = generalizer_linewidth
                facecolor = 'none'
                edgecolor = 'none'

            ax.plot(
                x,
                y,
                color=color,
                linewidth=linewidth,
                linestyle=linestyle,
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
            [x_labels.get(s, s) for s in df.columns],
        )

        if use_rank:
            ax.invert_yaxis()

        for s in ('right', 'top'):
            ax.spines[s].set_visible(False)

    def plot_heatmap(self, cmap=plt.cm.bwr_r, vmin=-1.5, vmax=1.5, **kwargs):

        index = self.specialization.index.union(self.tradeoff.index)

        def reindex(df):
            return df.astype(int).reindex(index, fill_value=0)

        data = reindex(self.specialization) - reindex(self.tradeoff)

        cm = sns.clustermap(
            data,
            cmap=cmap,
            vmin=vmin,
            vmax=vmax,
            cbar=False,
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
        if specialization is None:
            specialization = self.specialization

        if cover:
            specialization = specialization.iloc[
                greedy_set_cover(specialization.values)
            ]

        incidence_dict = {
            c: specialization.index[specialization[c]] for c in specialization
        }

        return hnx.Hypergraph(incidence_dict)

    def plot_hypergraph_euler(self, cover=False, **kwargs):
        H = self.specializers_as_hypergraph(cover=cover)
        return hnx.draw(H, **kwargs)

    def plot_hypergraph_upset(self, cover=False, order=None, **kwargs):
        H = self.specializers_as_hypergraph(cover=cover).dual()

        hnx.draw_incidence_upset(
            H,
            edge_order=order,
            edge_labels_kwargs=dict(va='top', ha='left', rotation=-45),
        )

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
