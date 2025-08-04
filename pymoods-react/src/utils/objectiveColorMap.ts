import { COLORS } from './colors';

export function buildObjectiveColorMap(objectiveNames: string[]): Record<string, string> {
  // Sort for cross-dataset consistency
  const sortedObjectives = [...objectiveNames].sort();
  const map: Record<string, string> = {};
  sortedObjectives.forEach((name, idx) => {
    map[name] = COLORS[idx % COLORS.length];
  });
  return map;
}