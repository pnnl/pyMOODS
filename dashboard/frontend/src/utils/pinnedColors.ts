export const PINNED_COLORS = ['#1565c0', '#c62828', '#2e7d32', '#e65100', '#6a1b9a', '#00838f'];

export const getPinnedColor = (index: number): string =>
  PINNED_COLORS[index % PINNED_COLORS.length];
