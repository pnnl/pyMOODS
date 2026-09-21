import React, { useState, useEffect, useCallback } from 'react';
import {
  Box,
  Typography,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  IconButton,
  CircularProgress,
  Tooltip,
  Chip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  List,
  ListItemButton,
  ListItemText,
  Divider,
  LinearProgress,
} from '@mui/material';
import AddIcon from '@mui/icons-material/Add';
import CloseIcon from '@mui/icons-material/Close';
import config from '../../config';

const { API_BASE_URL } = config;

type MCDMTechnique = 'generalizer_specializer' | 'weighted_sum' | 'topsis' | 'vikor';

export interface Solution {
  [key: string]: any;
}

export interface ComparisonColumn {
  id: string;
  label: string;
  sublabel: string;
  solution: Solution;
  isRecommended: boolean;
  mcdmScore?: number;
}

export interface BestSolutionPanelProps {
  loading: boolean;
  filters: Record<string, string[]>;
  weights: Record<string, number>;
  useCase: string;
  decisionKeys: string[];
  objectiveKeys: string[];
  objectiveUnits: Record<string, string>;
  onSolutionFocus: (solution: Solution | null) => void;
  focusedSolution?: Solution | null;
  comparisonColumns?: ComparisonColumn[];
  focusedColumnId?: string | null;
  onComparisonColumnsChange?: (columns: ComparisonColumn[]) => void;
  onFocusedColumnIdChange?: (focusedColumnId: string | null) => void;
}

const TECHNIQUE_OPTIONS: {
  value: MCDMTechnique;
  label: string;
  description: string;
}[] = [
  {
    value: 'generalizer_specializer',
    label: 'Generalizer / Specializer',
    description: 'Pareto dominance-based analysis',
  },
  {
    value: 'weighted_sum',
    label: 'Weighted Sum',
    description: 'Combined weighted objectives',
  },
  {
    value: 'topsis',
    label: 'TOPSIS',
    description: 'Closest to ideal solution',
  },
  {
    value: 'vikor',
    label: 'VIKOR',
    description: 'Multi-criteria compromise ranking',
  },
];

const ATTR_COL_WIDTH = 155;
const SOL_COL_WIDTH = 175;
const ROW_HEIGHT = 38;
const HEADER_HEIGHT = 84;
const SECTION_ROW_HEIGHT = 26;

const BestSolutionPanel: React.FC<BestSolutionPanelProps> = ({
  loading: parentLoading,
  filters,
  weights,
  useCase,
  decisionKeys,
  objectiveKeys,
  objectiveUnits,
  onSolutionFocus,
  focusedSolution,
  comparisonColumns,
  focusedColumnId: focusedColumnIdProp,
  onComparisonColumnsChange,
  onFocusedColumnIdChange,
}) => {
  const [technique, setTechnique] = useState<MCDMTechnique>('generalizer_specializer');
  const [columns, setColumns] = useState<ComparisonColumn[]>(comparisonColumns ?? []);
  const [recommendedLoading, setRecommendedLoading] = useState(false);
  const [addDialogOpen, setAddDialogOpen] = useState(false);
  const [availableSolutions, setAvailableSolutions] = useState<Solution[]>([]);
  const [availableScoreLabel, setAvailableScoreLabel] = useState('Score');
  const [addDialogLoading, setAddDialogLoading] = useState(false);
  const [focusedColumnId, setFocusedColumnId] = useState<string | null>(focusedColumnIdProp ?? null);

  const updateColumns = useCallback(
    (updater: ComparisonColumn[] | ((prev: ComparisonColumn[]) => ComparisonColumn[])) => {
      setColumns((prev) => {
        const next = typeof updater === 'function'
          ? (updater as (prev: ComparisonColumn[]) => ComparisonColumn[])(prev)
          : updater;
        if (onComparisonColumnsChange) onComparisonColumnsChange(next);
        return next;
      });
    },
    [onComparisonColumnsChange],
  );

  const updateFocusedColumnId = useCallback(
    (next: string | null) => {
      setFocusedColumnId(next);
      if (onFocusedColumnIdChange) onFocusedColumnIdChange(next);
    },
    [onFocusedColumnIdChange],
  );

  useEffect(() => {
    if (comparisonColumns) {
      setColumns(comparisonColumns);
    }
  }, [comparisonColumns]);

  useEffect(() => {
    if (focusedColumnIdProp !== undefined) {
      setFocusedColumnId(focusedColumnIdProp);
    }
  }, [focusedColumnIdProp]);

  // Single source of truth: whenever the focused column changes, push it to the scatter plot.
  // Using a useEffect (rather than imperative calls inside event handlers) avoids React
  // batching edge-cases where setSelectedSolution could be called before state settles.
  useEffect(() => {
    const col = columns.find(c => c.id === focusedColumnId);
    onSolutionFocus(col?.solution ?? null);
    // onSolutionFocus is a stable React state dispatcher — safe to omit from deps
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [focusedColumnId, columns]);

  const buildQueryParams = useCallback((): URLSearchParams => {
    const params = new URLSearchParams();
    params.append('use_case', useCase);
    Object.entries(filters).forEach(([key, values]) =>
      values.forEach(v => params.append(key, v))
    );
    Object.entries(weights).forEach(([key, value]) =>
      params.append(`weight_${key}`, value.toString())
    );
    return params;
  }, [useCase, filters, weights]);

  // Fetch the recommended (first) solution whenever technique / filters / weights change.
  useEffect(() => {
    if (!useCase) return;

    if (columns.length > 0) {
      if (!focusedColumnId || !columns.some((c) => c.id === focusedColumnId)) {
        updateFocusedColumnId(columns[0].id);
      }
      return;
    }

    const controller = new AbortController();

    const fetchRecommended = async () => {
      setRecommendedLoading(true);

      try {
        const params = buildQueryParams();
        let solution: Solution | null = null;
        let label = 'Recommended';
        let sublabel = '';

        if (technique === 'generalizer_specializer') {
          const res = await fetch(`${API_BASE_URL}/api/generalizers?${params}`, {
            signal: controller.signal,
          });
          const data = await res.json();
          if (data.solutions?.length > 0) {
            solution = data.solutions[0];
            label = 'Generalizer';
            sublabel = 'Best overall compromise';
          }
        } else {
          params.append('technique', technique);
          params.append('top_n', '1');
          const res = await fetch(`${API_BASE_URL}/api/mcdm-solutions?${params}`, {
            signal: controller.signal,
          });
          const data = await res.json();
          if (data.solutions?.length > 0) {
            solution = data.solutions[0];
            const scoreLabel = data.score_label || 'Score';
            label = 'Rank 1';
            const score = solution?.['mcdm_score'];
            sublabel = `${scoreLabel}: ${typeof score === 'number' ? score.toFixed(3) : '—'}`;
          }
        }

        if (solution) {
          const col: ComparisonColumn = {
            id: 'recommended',
            label,
            sublabel,
            solution,
            isRecommended: true,
          };
          updateColumns([col]);
          updateFocusedColumnId('recommended');
        }
      } catch (err: any) {
        if (err.name !== 'AbortError') console.error('BestSolutionPanel fetch error:', err);
      } finally {
        setRecommendedLoading(false);
      }
    };

    fetchRecommended();
    return () => controller.abort();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [technique, useCase, JSON.stringify(filters), JSON.stringify(weights), columns, focusedColumnId, updateColumns, updateFocusedColumnId]);

  const handleOpenAddDialog = async () => {
    setAddDialogOpen(true);
    setAddDialogLoading(true);
    setAvailableSolutions([]);

    try {
      const params = buildQueryParams();

      if (technique === 'generalizer_specializer') {
        params.append('min_specializers', '10');
        const res = await fetch(`${API_BASE_URL}/api/specializers?${params}`);
        const data = await res.json();
        setAvailableSolutions(data.solutions || []);
        setAvailableScoreLabel('Specializer');
      } else {
        params.append('technique', technique);
        params.append('top_n', '15');
        const res = await fetch(`${API_BASE_URL}/api/mcdm-solutions?${params}`);
        const data = await res.json();
        setAvailableSolutions(data.solutions || []);
        setAvailableScoreLabel(data.score_label || 'Score');
      }
    } catch (err) {
      console.error('Error fetching solutions for add dialog:', err);
    } finally {
      setAddDialogLoading(false);
    }
  };

  const handleSelectSolution = (solution: Solution, index: number) => {
    const id = `col_${Date.now()}_${index}`;
    const isGS = technique === 'generalizer_specializer';
    const score = solution['mcdm_score'];

    const newCol: ComparisonColumn = {
      id,
      label: isGS ? 'Specializer' : `Rank ${index + 1}`,
      sublabel: isGS
        ? `Solution #${solution['Solution ID'] ?? index + 1}`
        : `${availableScoreLabel}: ${typeof score === 'number' ? score.toFixed(3) : '—'}`,
      solution,
      isRecommended: false,
      mcdmScore: score,
    };

    updateColumns(prev => [...prev, newCol]);
    setAddDialogOpen(false);
    updateFocusedColumnId(id);
  };

  const handleRemoveColumn = (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    updateColumns(prev => {
      const remaining = prev.filter(c => c.id !== id);
      if (focusedColumnId === id) {
        updateFocusedColumnId(remaining.length > 0 ? remaining[0].id : null);
      }
      return remaining;
    });
  };

  const handleColumnClick = (col: ComparisonColumn) => {
    updateFocusedColumnId(col.id);
  };

  const formatValue = (key: string, value: any): string => {
    if (value === undefined || value === null) return '—';
    if (typeof value === 'number') {
      const unit = objectiveUnits[key];
      const formatted = Number.isInteger(value)
        ? value.toLocaleString('en-US')
        : value.toLocaleString('en-US', {
            minimumFractionDigits: 2,
            maximumFractionDigits: 2,
          });
      return unit ? `${formatted} ${unit}` : formatted;
    }
    return String(value);
  };

  // Highlight a column that matches the externally selected solution (scatter plot click).
  const matchesFocused = (col: ComparisonColumn): boolean => {
    if (!focusedSolution) return false;
    const fid = focusedSolution['Solution ID'];
    const cid = col.solution['Solution ID'];
    return fid !== undefined && fid === cid;
  };

  interface RowDef {
    key: string;
    label: string;
    isSection: boolean;
  }

  const rows: RowDef[] = [
    { key: 'Solution ID', label: 'Solution ID', isSection: false },
    { key: '_dec', label: 'Decision Variables', isSection: true },
    ...decisionKeys.map(k => ({ key: k, label: k, isSection: false })),
    { key: '_obj', label: 'Objective Functions', isSection: true },
    ...objectiveKeys.map(k => ({ key: k, label: k, isSection: false })),
  ];

  const isLoading = parentLoading || recommendedLoading;

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', height: '100%', gap: 1, minHeight: 0, pt: 1.5 }}>
      {/* ── Technique selector ─────────────────────────────────────────────── */}
      <FormControl size="small" sx={{ flexShrink: 0, minWidth: 240, maxWidth: 320 }}>
        <InputLabel id="mcdm-technique-label">MCDM Technique</InputLabel>
        <Select
          labelId="mcdm-technique-label"
          value={technique}
          label="MCDM Technique"
          onChange={e => setTechnique(e.target.value as MCDMTechnique)}
          sx={{ fontSize: '0.82rem' }}
        >
          {TECHNIQUE_OPTIONS.map(opt => (
            <MenuItem
              key={opt.value}
              value={opt.value}
              sx={{ flexDirection: 'column', alignItems: 'flex-start', py: 0.75 }}
            >
              <Typography variant="body2" fontWeight={600}>
                {opt.label}
              </Typography>
              <Typography variant="caption" color="text.secondary" sx={{ lineHeight: 1.3 }}>
                {opt.description}
              </Typography>
            </MenuItem>
          ))}
        </Select>
      </FormControl>

      {/* ── Comparison table ───────────────────────────────────────────────── */}
      <Box
        sx={{
          flex: 1,
          minHeight: 0,
          overflow: 'auto',
          borderRadius: 1.5,
          border: '1px solid',
          borderColor: 'divider',
          bgcolor: 'background.paper',
          position: 'relative',
        }}
      >
        {isLoading ? (
          <Box
            sx={{
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              justifyContent: 'center',
              height: '100%',
              gap: 1,
            }}
          >
            <LinearProgress sx={{ width: '60%' }} />
            <Typography variant="caption" color="text.secondary">
              Loading best solution…
            </Typography>
          </Box>
        ) : (
          <Box sx={{ display: 'flex', minWidth: 'max-content', minHeight: '100%' }}>
            {/* ── Fixed attribute-label column ─────────────────────────────── */}
            <Box
              sx={{
                width: ATTR_COL_WIDTH,
                flexShrink: 0,
                position: 'sticky',
                left: 0,
                zIndex: 2,
                bgcolor: 'background.paper',
                borderRight: '2px solid',
                borderColor: 'divider',
              }}
            >
              {/* spacer matches header height */}
              <Box
                sx={{
                  height: HEADER_HEIGHT,
                  borderBottom: '1px solid',
                  borderColor: 'divider',
                  bgcolor: 'grey.50',
                  display: 'flex',
                  alignItems: 'flex-end',
                  px: 1.25,
                  pb: 0.75,
                }}
              >
                <Typography variant="caption" sx={{ fontWeight: 700, color: 'text.secondary', fontSize: '0.68rem', textTransform: 'uppercase', letterSpacing: 0.5 }}>
                  Attribute
                </Typography>
              </Box>
              {rows.map(row => (
                <Box
                  key={row.key}
                  sx={{
                    height: row.isSection ? SECTION_ROW_HEIGHT : ROW_HEIGHT,
                    display: 'flex',
                    alignItems: 'center',
                    px: 1.25,
                    bgcolor: row.isSection ? 'grey.50' : 'transparent',
                    borderBottom: '1px solid',
                    borderColor: 'divider',
                  }}
                >
                  <Typography
                    variant="caption"
                    sx={{
                      fontWeight: row.isSection ? 700 : 400,
                      color: row.isSection ? 'text.primary' : 'text.secondary',
                      textTransform: row.isSection ? 'uppercase' : 'none',
                      fontSize: row.isSection ? '0.62rem' : '0.74rem',
                      letterSpacing: row.isSection ? 0.6 : 0,
                      whiteSpace: 'nowrap',
                      overflow: 'hidden',
                      textOverflow: 'ellipsis',
                      display: 'block',
                      maxWidth: ATTR_COL_WIDTH - 20,
                    }}
                    title={row.label}
                  >
                    {row.label}
                  </Typography>
                </Box>
              ))}
            </Box>

            {/* ── Solution columns ──────────────────────────────────────────── */}
            {columns.map(col => {
              const isFocused = focusedColumnId === col.id;
              const isExtFocused = !isFocused && matchesFocused(col);

              return (
                <Box
                  key={col.id}
                  onClick={() => handleColumnClick(col)}
                  sx={{
                    width: SOL_COL_WIDTH,
                    flexShrink: 0,
                    cursor: 'pointer',
                    borderRight: '1px solid',
                    borderColor: 'divider',
                    outline: '2px solid',
                    outlineColor: isFocused
                      ? 'primary.main'
                      : isExtFocused
                      ? 'primary.light'
                      : 'transparent',
                    outlineOffset: '-2px',
                    borderRadius: 0.5,
                    transition: 'outline-color 0.15s, background-color 0.1s',
                    '&:hover': {
                      bgcolor: 'rgba(25, 118, 210, 0.04)',
                      outlineColor: isFocused ? 'primary.main' : 'primary.light',
                    },
                  }}
                >
                  {/* Column header */}
                  <Box
                    sx={{
                      height: HEADER_HEIGHT,
                      borderBottom: '1px solid',
                      borderColor: 'divider',
                      p: 1,
                      display: 'flex',
                      flexDirection: 'column',
                      justifyContent: 'center',
                      gap: 0.25,
                      bgcolor: isFocused
                        ? 'rgba(25, 118, 210, 0.08)'
                        : 'grey.50',
                      position: 'relative',
                    }}
                  >
                    {col.isRecommended && (
                      <Chip
                        label="Recommended"
                        size="small"
                        color="primary"
                        sx={{ height: 16, fontSize: '0.58rem', width: 'fit-content', mb: 0.25 }}
                      />
                    )}
                    <Typography variant="body2" fontWeight={700} noWrap sx={{ fontSize: '0.82rem' }}>
                      {col.label}
                    </Typography>
                    <Typography
                      variant="caption"
                      color="text.secondary"
                      noWrap
                      sx={{ fontSize: '0.69rem' }}
                    >
                      {col.sublabel}
                    </Typography>
                    {isFocused && (
                      <Chip
                        label="Highlighted on plot"
                        size="small"
                        variant="outlined"
                        color="primary"
                        sx={{ height: 14, fontSize: '0.54rem', width: 'fit-content', mt: 0.25 }}
                      />
                    )}
                    {!col.isRecommended && (
                      <Tooltip title="Remove column">
                        <IconButton
                          size="small"
                          onClick={e => handleRemoveColumn(col.id, e)}
                          sx={{
                            position: 'absolute',
                            top: 4,
                            right: 4,
                            p: 0.25,
                            '&:hover': { color: 'error.main' },
                          }}
                        >
                          <CloseIcon sx={{ fontSize: 13 }} />
                        </IconButton>
                      </Tooltip>
                    )}
                  </Box>

                  {/* Value rows */}
                  {rows.map(row => (
                    <Box
                      key={row.key}
                      sx={{
                        height: row.isSection ? SECTION_ROW_HEIGHT : ROW_HEIGHT,
                        display: 'flex',
                        alignItems: 'center',
                        px: 1.25,
                        bgcolor: row.isSection
                          ? 'grey.50'
                          : isFocused
                          ? 'rgba(25, 118, 210, 0.03)'
                          : 'transparent',
                        borderBottom: '1px solid',
                        borderColor: 'divider',
                      }}
                    >
                      {!row.isSection && (
                        <Tooltip
                          title={formatValue(row.key, col.solution[row.key])}
                          placement="top"
                          disableHoverListener={
                            formatValue(row.key, col.solution[row.key]).length < 18
                          }
                        >
                          <Typography
                            variant="body2"
                            fontWeight={500}
                            noWrap
                            sx={{ fontSize: '0.76rem' }}
                          >
                            {formatValue(row.key, col.solution[row.key])}
                          </Typography>
                        </Tooltip>
                      )}
                    </Box>
                  ))}
                </Box>
              );
            })}

            {/* ── Add-column button ─────────────────────────────────────────── */}
            <Box
              sx={{
                width: 76,
                flexShrink: 0,
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                pt: `${HEADER_HEIGHT / 2 - 28}px`,
                px: 1,
              }}
            >
              <Tooltip
                title={
                  technique === 'generalizer_specializer'
                    ? 'Add a specializer to compare'
                    : 'Add a solution to compare'
                }
              >
                <Box
                  onClick={handleOpenAddDialog}
                  role="button"
                  sx={{
                    width: 44,
                    height: 44,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    border: '1.5px dashed',
                    borderColor: 'action.active',
                    borderRadius: 1.5,
                    cursor: 'pointer',
                    transition: 'border-color 0.15s, background-color 0.15s',
                    '&:hover': {
                      borderColor: 'primary.main',
                      bgcolor: 'rgba(25, 118, 210, 0.06)',
                    },
                  }}
                >
                  <AddIcon sx={{ fontSize: 20, color: 'action.active' }} />
                </Box>
              </Tooltip>
              <Typography
                variant="caption"
                color="text.secondary"
                sx={{ mt: 0.5, textAlign: 'center', fontSize: '0.58rem' }}
              >
                Compare
              </Typography>
            </Box>
          </Box>
        )}
      </Box>

      {/* ── Add-solution dialog ────────────────────────────────────────────── */}
      <Dialog
        open={addDialogOpen}
        onClose={() => setAddDialogOpen(false)}
        maxWidth="sm"
        fullWidth
        PaperProps={{ sx: { maxHeight: '72vh' } }}
      >
        <DialogTitle sx={{ pb: 0.5 }}>
          <Box sx={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between' }}>
            <Box>
              <Typography variant="h6" sx={{ fontSize: '1rem', fontWeight: 700 }}>
                {technique === 'generalizer_specializer'
                  ? 'Select a Specializer'
                  : 'Select a Solution to Compare'}
              </Typography>
              <Typography variant="caption" color="text.secondary">
                {technique === 'generalizer_specializer'
                  ? 'Specializers excel in one or more specific objectives at the cost of overall balance.'
                  : `Solutions ranked by ${availableScoreLabel} for the current filters and weights.`}
              </Typography>
            </Box>
            <IconButton size="small" onClick={() => setAddDialogOpen(false)} sx={{ mt: -0.5 }}>
              <CloseIcon sx={{ fontSize: 18 }} />
            </IconButton>
          </Box>
        </DialogTitle>
        <Divider />
        <DialogContent sx={{ p: 0 }}>
          {addDialogLoading ? (
            <Box
              sx={{
                display: 'flex',
                justifyContent: 'center',
                alignItems: 'center',
                py: 5,
              }}
            >
              <CircularProgress size={24} />
            </Box>
          ) : availableSolutions.length === 0 ? (
            <Box sx={{ p: 3 }}>
              <Typography variant="body2" color="text.secondary">
                No solutions available for the current filters.
              </Typography>
            </Box>
          ) : (
            <List dense disablePadding>
              {availableSolutions.map((sol, idx) => {
                const alreadyAdded = columns.some(
                  c => c.solution['Solution ID'] !== undefined &&
                       c.solution['Solution ID'] === sol['Solution ID']
                );
                const score = sol['mcdm_score'];

                return (
                  <React.Fragment key={idx}>
                    <ListItemButton
                      onClick={() => !alreadyAdded && handleSelectSolution(sol, idx)}
                      disabled={alreadyAdded}
                      sx={{ px: 2, py: 1 }}
                    >
                      <ListItemText
                        primary={
                          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                            <Typography variant="body2" fontWeight={700}>
                              {technique === 'generalizer_specializer'
                                ? `Specializer — Solution #${sol['Solution ID'] ?? idx + 1}`
                                : `Rank ${idx + 1} — Solution #${sol['Solution ID'] ?? idx + 1}`}
                            </Typography>
                            {alreadyAdded && (
                              <Chip
                                label="Added"
                                size="small"
                                color="default"
                                sx={{ height: 16, fontSize: '0.58rem' }}
                              />
                            )}
                          </Box>
                        }
                        secondary={
                          <Box sx={{ display: 'flex', gap: 1.5, flexWrap: 'wrap', mt: 0.25 }}>
                            {objectiveKeys.slice(0, 3).map(key => (
                              <Typography key={key} variant="caption" color="text.secondary">
                                {key}: {formatValue(key, sol[key])}
                              </Typography>
                            ))}
                            {technique !== 'generalizer_specializer' &&
                              score !== undefined && (
                                <Typography
                                  variant="caption"
                                  color="primary.main"
                                  fontWeight={700}
                                >
                                  {availableScoreLabel}: {typeof score === 'number' ? score.toFixed(4) : '—'}
                                </Typography>
                              )}
                          </Box>
                        }
                      />
                    </ListItemButton>
                    {idx < availableSolutions.length - 1 && <Divider />}
                  </React.Fragment>
                );
              })}
            </List>
          )}
        </DialogContent>
        <DialogActions sx={{ px: 2, py: 1 }}>
          <Button size="small" onClick={() => setAddDialogOpen(false)}>
            Cancel
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default BestSolutionPanel;
