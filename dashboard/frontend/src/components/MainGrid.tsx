import React, { useState, useEffect, useMemo, useCallback } from "react";
import {
  Box,
  CircularProgress,
  Drawer,
  Fab,
  Tabs,
  Tab,
  Button,
  LinearProgress,
  Typography,
  Card,
  CardHeader,
  CardContent,
  Alert,
} from "@mui/material";
import AutoAwesomeIcon from "@mui/icons-material/AutoAwesome";
import ScatterPlotOutlinedIcon from "@mui/icons-material/ScatterPlotOutlined";
import AccountTreeOutlinedIcon from "@mui/icons-material/AccountTreeOutlined";
import LaunchOutlinedIcon from "@mui/icons-material/LaunchOutlined";
import { AgentChatPanel } from "./AgentChat/AgentChatPanel";
import { ProactiveInsightBubble } from "./AgentChat/ProactiveInsightBubble";
import { useProactiveInsights } from "../hooks/useProactiveInsights";

// Import Plot Components
import ScatterPlot from './OffshoreWindfarmPlots/ScatterPlot';
import DecisionVariablesChart, { DecisionData } from './OffshoreWindfarmPlots/DecisionVariablesChart';
import BestSolutionPanel, { ComparisonColumn } from './BestSolution/BestSolutionPanel';
import ParallelCoordinatesChart from './OffshoreWindfarmPlots/ParallelCoordinatesChart';
import LMPPlot from './OffshoreWindfarmPlots/LMPPlot';
import NetworkGraphPanel from './OffshoreWindfarmPlots/NetworkGraphPanel';
import TradeoffLatticePlot from "./TradeoffLatticePlot";
import { buildObjectiveColorMap } from "../utils/objectiveColorMap";

import config from "../config";
import { useDashboardStore } from "../store/dashboardStore";
const { API_BASE_URL } = config;

interface MainGridProps {
  selectedUseCase: string;
  filters: Record<string, string[]>;
  weights: Record<string, number>;
  onWeightsChange?: (weights: Record<string, number>) => void;
  onLocationSelect?: (location: string, locationField?: string) => void;
}

interface Solution {
  [key: string]: any;
}

interface UseCaseComparisonState {
  columns: ComparisonColumn[];
  focusedColumnId: string | null;
}

const MainGrid: React.FC<MainGridProps> = ({
  selectedUseCase,
  filters,
  weights,
  // onWeightsChange,
}) => {
  const {
    setAvailableMetadata,
    setActiveWeights,
    setActiveSolutionSample,
    setActiveTabIndex,
    dashboardState,
    proactiveBubble,
  } = useDashboardStore();

  // Merge sidebar filters (from props) with agent-applied filter overrides (from store).
  // Agent filters win for any key they set; empty-array overrides are ignored so a
  // REMOVE_FILTER command falls back to the sidebar selection rather than showing nothing.
  const effectiveFilters = useMemo(() => {
    const merged: Record<string, string[]> = { ...filters };
    for (const [key, values] of Object.entries(dashboardState.activeFilters)) {
      if (values.length > 0) merged[key] = values;
    }
    return merged;
  }, [filters, dashboardState.activeFilters]);

  useProactiveInsights();

  const [tabIndex, setTabIndex] = useState(0);
  const [deepDiveTab, setDeepDiveTab] = useState(0);
  const [chatOpen, setChatOpen] = useState(false);
  const [clusterBy, setClusterBy] = useState<string>("AI-Generated");
  const [, setObjectiveNames] = useState<string[]>([]);
  const [objectiveColorMap, setObjectiveColorMap] = useState<Record<string, string>>({});
  // State for Summary
  const [completeData, setCompleteData] = useState<Solution[]>([]);
  const [decisionKeys, setDecisionKeys] = useState<string[]>([]);
  const [objectiveKeys, setObjectiveKeys] = useState<string[]>([]);
  const [objectiveUnits, setObjectiveUnits] = useState<Record<string, string>>({});
  const [hyperparameterKeys, setHyperparameterKeys] = useState<string[]>([]);
  const [inputParameterKeys, setInputParameterKeys] = useState<string[]>([]);
  const [summaryLoading, setSummaryLoading] = useState<boolean>(true);
  const [selectedSolutionByUseCase, setSelectedSolutionByUseCase] = useState<Record<string, Solution | null>>({});
  const [comparisonStateByUseCase, setComparisonStateByUseCase] = useState<Record<string, UseCaseComparisonState>>({});

  const getSolutionIdentity = useCallback((solution: Solution | null | undefined): string | null => {
    if (!solution) return null;
    const raw = solution['Solution ID'] ?? solution['solution_id'];
    return raw === undefined || raw === null ? null : String(raw);
  }, []);

  const isSameSolution = useCallback((a: Solution, b: Solution): boolean => {
    const aId = getSolutionIdentity(a);
    const bId = getSolutionIdentity(b);
    if (aId && bId) return aId === bId;
    return JSON.stringify(a) === JSON.stringify(b);
  }, [getSolutionIdentity]);

  const activeComparisonState = useMemo<UseCaseComparisonState>(() => {
    if (!selectedUseCase) return { columns: [], focusedColumnId: null };
    return comparisonStateByUseCase[selectedUseCase] ?? { columns: [], focusedColumnId: null };
  }, [comparisonStateByUseCase, selectedUseCase]);

  const selectedSolution = useMemo<Solution | null>(() => {
    if (!selectedUseCase) return null;
    const explicitSelection = selectedSolutionByUseCase[selectedUseCase] ?? null;
    if (explicitSelection) return explicitSelection;

    const focusedColumn = activeComparisonState.columns.find(
      (col) => col.id === activeComparisonState.focusedColumnId,
    );
    return focusedColumn?.solution ?? null;
  }, [activeComparisonState.columns, activeComparisonState.focusedColumnId, selectedSolutionByUseCase, selectedUseCase]);

  const setSelectedSolutionForUseCase = useCallback((solution: Solution | null) => {
    if (!selectedUseCase) return;
    setSelectedSolutionByUseCase((prev) => ({ ...prev, [selectedUseCase]: solution }));
  }, [selectedUseCase]);

  const upsertScatterSelectionIntoComparison = useCallback((solution: Solution) => {
    if (!selectedUseCase) return;

    setComparisonStateByUseCase((prev) => {
      const current = prev[selectedUseCase] ?? { columns: [], focusedColumnId: null };
      const existingIndex = current.columns.findIndex((col) => isSameSolution(col.solution, solution));

      if (existingIndex >= 0) {
        const focusedId = current.columns[existingIndex].id;
        return {
          ...prev,
          [selectedUseCase]: {
            columns: current.columns,
            focusedColumnId: focusedId,
          },
        };
      }

      const solutionId = getSolutionIdentity(solution);
      const nextId = `scatter_${solutionId ?? Date.now()}`;
      const newColumn: ComparisonColumn = {
        id: nextId,
        label: 'Pinned',
        sublabel: solutionId ? `Solution #${solutionId}` : 'Added from scatter plot',
        solution,
        isRecommended: false,
      };

      return {
        ...prev,
        [selectedUseCase]: {
          columns: [...current.columns, newColumn],
          focusedColumnId: nextId,
        },
      };
    });

    setSelectedSolutionForUseCase(solution);
  }, [getSolutionIdentity, isSameSolution, selectedUseCase, setSelectedSolutionForUseCase]);

  const handleComparisonColumnsChange = useCallback((columns: ComparisonColumn[]) => {
    if (!selectedUseCase) return;

    setComparisonStateByUseCase((prev) => {
      const current = prev[selectedUseCase] ?? { columns: [], focusedColumnId: null };
      let nextFocusedId = current.focusedColumnId;
      if (nextFocusedId && !columns.some((col) => col.id === nextFocusedId)) {
        nextFocusedId = columns.length > 0 ? columns[0].id : null;
      }

      return {
        ...prev,
        [selectedUseCase]: {
          columns,
          focusedColumnId: nextFocusedId,
        },
      };
    });
  }, [selectedUseCase]);

  const handleFocusedColumnIdChange = useCallback((focusedColumnId: string | null) => {
    if (!selectedUseCase) return;

    setComparisonStateByUseCase((prev) => {
      const current = prev[selectedUseCase] ?? { columns: [], focusedColumnId: null };
      return {
        ...prev,
        [selectedUseCase]: {
          columns: current.columns,
          focusedColumnId,
        },
      };
    });

    const focusedColumn = activeComparisonState.columns.find((col) => col.id === focusedColumnId);
    setSelectedSolutionForUseCase(focusedColumn?.solution ?? null);
  }, [activeComparisonState.columns, selectedUseCase, setSelectedSolutionForUseCase]);

  const pinnedSolutions = useMemo(() => {
    return activeComparisonState.columns.map((col) => ({
      id: col.id,
      label: col.label,
      solution: col.solution,
      isFocused: col.id === activeComparisonState.focusedColumnId,
    }));
  }, [activeComparisonState.columns, activeComparisonState.focusedColumnId]);

  const selectedSolutionsForPcp = useMemo(
    () => activeComparisonState.columns.map((col) => col.solution),
    [activeComparisonState.columns],
  );

  // State for DualRadarChart
  const [decisionData, setDecisionData] = useState<{
    decisions: DecisionData[];
  }>({
    decisions: [],
  });
  const [radarLoading, setRadarLoading] = useState<boolean>(true);
  const [rankData, setRankData] = useState<Record<string, any>>({});

  const [error, setError] = useState<string | null>(null);
  const [cameoLoading, setCameoLoading] = useState(false);

  useEffect(() => {
    if (tabIndex === 2) setCameoLoading(true);
  }, [tabIndex]);

  // Fetch objective names for weight UI
  useEffect(() => {
    const fetchObjectives = async () => {
      try {
        const params = new URLSearchParams();
        params.append("use_case", selectedUseCase);

        Object.entries(weights).forEach(([key, value]) => {
          params.append(`weight_${key}`, value.toString());
        });

        const response = await fetch(
          `${API_BASE_URL}/api/objective?${params.toString()}`
        );
        if (!response.ok) throw new Error("Failed to fetch objectives");

        const data = await response.json();

        const objNames = Object.keys(data.weights_used || {});
        setObjectiveNames(objNames);
        setObjectiveColorMap(buildObjectiveColorMap(objNames));
      } catch (err) {
        console.error("Error fetching objectives:", err);
      }
    };

    if (selectedUseCase) fetchObjectives();
  }, [selectedUseCase, weights]);

  // Automatically select clusterBy based on available filters
  useEffect(() => {
    if (Object.keys(filters).length > 0 && !clusterBy) {
      const availableKeys = [
        ...new Set([...Object.keys(filters), "AI-Generated"]),
      ];
      setClusterBy(
        availableKeys.includes("AI-Generated")
          ? "AI-Generated"
          : availableKeys[0]
      );
    }
  }, [filters]);

  useEffect(() => {
    const abortController = new AbortController();

    const fetchData = async () => {
      if (
        !selectedUseCase ||
        !Object.keys(filters).length ||
        !Object.keys(weights).length
      )
        return;

      setSummaryLoading(true);
      setRadarLoading(true);
      setError(null);

      const queryParams = new URLSearchParams();

      // Add filters (sidebar selection merged with any agent-applied overrides)
      Object.entries(effectiveFilters).forEach(([key, values]) =>
        values.forEach((value) => queryParams.append(key, value))
      );

      // Add weights
      Object.entries(weights).forEach(([key, value]) =>
        queryParams.append(`weight_${key}`, value.toString())
      );

      // Add use case
      queryParams.append("use_case", selectedUseCase);

      try {
        const response = await fetch(
          `${API_BASE_URL}/api/solutions?${queryParams.toString()}`,
          { signal: abortController.signal }
        );
        if (!response.ok) throw new Error("Failed to fetch shared data");

        const result = await response.json();
        console.log("Fetched unified data:", result.solutions);
        setCompleteData(result.solutions);
        setDecisionKeys(result.decision_keys || []);
        setObjectiveKeys(result.objective_keys || []);
        setObjectiveUnits(result.objective_units || {});
        setHyperparameterKeys(result.hyperparameter_keys || []);
        setInputParameterKeys(result.input_parameter_keys || []);

        // Save ranks separately
        setRankData(result.ranks || {});

        // Populate agent context so the AI knows the data schema and current state.
        setAvailableMetadata({
          useCaseName: selectedUseCase,
          objectiveKeys: result.objective_keys || [],
          decisionKeys: result.decision_keys || [],
          hyperparameterKeys: result.hyperparameter_keys || [],
          inputParameterKeys: result.input_parameter_keys || [],
          objectiveUnits: result.objective_units || {},
          availableFilterValues: filters,
        });
        setActiveWeights(weights);
        setActiveSolutionSample((result.solutions || []).slice(0, 5));

        // Radar chart data
        const computeChartData = (keys: string[]) => {
          return keys.map((key) => {
            const values = result.solutions.map(
              (row: { [x: string]: string; }) => parseFloat(row[key]) || 0
            );
            const min = Math.min(...values);
            const max = Math.max(...values);
            return {
              name: key,
              distribution: values,
              selected: 0,
              min: min || 1,
              max: max || 1,
            };
          });
        };

        setDecisionData({
          decisions: computeChartData(result.decision_keys || []),
        });
      } catch (err: any) {
        if (err.name === 'AbortError') return;
        console.error("Error fetching unified data:", err);
        setError("Failed to load visualizations.");
        setCompleteData([]);
        setDecisionData({ decisions: [] });
      } finally {
        if (!abortController.signal.aborted) {
          setSummaryLoading(false);
          setRadarLoading(false);
        }
      }
    };

    fetchData();
  // Agent filter overrides (effectiveFilters) intentionally excluded — they update
  // individual visualizations directly without triggering a full solutions re-fetch.
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedUseCase, JSON.stringify(filters), JSON.stringify(weights)]);

  // const handleWeightChange = (newWeights: Record<string, number>) => {
  //   if (onWeightsChange) {
  //     onWeightsChange(newWeights);
  //   }
  // };

  const decisionDataForSelection = useMemo(() => {
    const normalizeKey = (value: string) => value.toLowerCase().replace(/[^a-z0-9]/g, '');
    const effectiveSolution = selectedSolution ?? (completeData.length > 0 ? completeData[0] : null);

    const getSelectedDecisionValue = (decisionName: string, solution: Solution | null | undefined): number | null => {
      if (!solution) return null;

      const direct = solution[decisionName];
      const directNum = typeof direct === 'number' ? direct : Number(direct);
      if (Number.isFinite(directNum)) return directNum;

      const target = normalizeKey(decisionName);
      const candidateEntries = Object.entries(solution)
        .map(([key, value]) => ({ key, normalized: normalizeKey(key), value }))
        .filter((entry) =>
          entry.normalized === target
          || entry.normalized.includes(target)
          || target.includes(entry.normalized)
        );

      if (candidateEntries.length === 0) return null;

      // Prefer the closest key-name match to avoid accidental partial matches.
      candidateEntries.sort((a, b) => Math.abs(a.normalized.length - target.length) - Math.abs(b.normalized.length - target.length));
      const fallbackNum = typeof candidateEntries[0].value === 'number'
        ? candidateEntries[0].value
        : Number(candidateEntries[0].value);

      return Number.isFinite(fallbackNum) ? fallbackNum : null;
    };

    return {
      decisions: decisionData.decisions.map((decision) => {
        const selectedValue = getSelectedDecisionValue(decision.name, effectiveSolution);
        return {
          ...decision,
          selected: selectedValue ?? decision.selected,
        };
      }),
    };
  }, [completeData, decisionData, selectedSolution]);

  // Loading and error are shown inline so the nav tabs remain visible at all times.

  const tabContentSx = {
    maxWidth: '100%',
    flex: 1,
    minHeight: 0,
    overflow: 'hidden',
    px: 1.5,
    pb: 1.5,
    boxSizing: 'border-box' as const,
  };

  const panelSx = {
    maxWidth: '100%',
    width: '100%',
    height: '100%',
    minHeight: 0,
    overflow: 'hidden',
  };

  const cardSx = {
    display: 'flex',
    flexDirection: 'column' as const,
    width: '100%',
    height: '100%',
    minHeight: 0,
    overflow: 'hidden',
  };

  const filteredCount = completeData.length;

  const mainMenuItems = [
    { label: "Decision Making",   value: 0, icon: <ScatterPlotOutlinedIcon sx={{ fontSize: 16 }} /> },
    { label: "Scenario Comparison", value: 1, icon: <AccountTreeOutlinedIcon sx={{ fontSize: 16 }} /> },
    { label: "Access Cameo",      value: 2, icon: <LaunchOutlinedIcon sx={{ fontSize: 16 }} /> },
  ];

  const cardHeaderSx = {
    pb: 0,
    pt: 1,
    px: 1.5,
    flexShrink: 0,
    '& .MuiCardHeader-title': { fontSize: '1rem', fontWeight: 700 },
    '& .MuiCardHeader-subheader': { fontSize: '0.76rem' },
  };

  const cardContentSx = {
    flex: 1,
    minHeight: 0,
    overflow: 'hidden',
    p: '0 !important',
    display: 'flex',
    flexDirection: 'column' as const,
  };

  return (
    <Box
      className="main-grid"
      sx={{
        maxWidth: "100%",
        px: 0,
        py: 0,
        height: "100%",
        minHeight: 0,
        display: "flex",
        flexDirection: "column",
        overflow: "hidden",
      }}
    >
      {/* Top Navigation Menu */}
      <Box
        className="main-grid__menu"
        sx={{
          borderBottom: 1,
          borderColor: "divider",
          mb: 1,
          mt: 1,
          px: 1.5,
        }}
      >
        <Box
          component="nav"
          aria-label="Main views"
          sx={{
            display: "flex",
            alignItems: "center",
            gap: 0.5,
            overflowX: "auto",
            pb: 0.5,
            '&::-webkit-scrollbar': { height: 6 },
          }}
        >
          {mainMenuItems.map((item) => {
            const isActive = tabIndex === item.value;
            return (
              <Button
                key={item.value}
                className={`main-grid__menu-item ${isActive ? "main-grid__menu-item--active" : ""}`}
                onClick={() => { setTabIndex(item.value); setActiveTabIndex(item.value); }}
                startIcon={item.icon}
                sx={{
                  borderRadius: 0,
                  px: 1.25,
                  py: 1,
                  textTransform: "none",
                  fontWeight: isActive ? 700 : 500,
                  fontSize: "0.92rem",
                  color: isActive ? "primary.main" : "text.secondary",
                  borderBottom: "2px solid",
                  borderBottomColor: isActive ? "primary.main" : "transparent",
                  minWidth: "max-content",
                  gap: 0.5,
                }}
              >
                {item.label}
              </Button>
            );
          })}
        </Box>
      </Box>

      {/* Inline loading bar — nav tabs remain visible while data is fetched */}
      {(summaryLoading || radarLoading) && (
        <LinearProgress sx={{ flexShrink: 0, height: 2 }} />
      )}
      {error && (
        <Box sx={{ px: 1.5, pb: 0.5, flexShrink: 0 }}>
          <Alert severity="error" onClose={() => setError(null)} sx={{ py: 0.5 }}>{error}</Alert>
        </Box>
      )}

      {/* Tab Content */}
      {/* Decision Making Tab */}
      {tabIndex === 0 && (
        <Box className="main-grid__tab-panel main-grid__tab-panel--decision" sx={tabContentSx}>
          <Box
            className="main-grid__decision-layout"
            sx={{
              maxWidth: "100%",
              height: "100%",
              minHeight: 0,
              pt: 1,
              display: "grid",
              gridTemplateColumns: {
                xs: "1fr",
                md: "minmax(0, 1.7fr) minmax(320px, 1fr)",
              },
              gap: 2,
            }}
          >
            <Box className="main-grid__panel-slot main-grid__panel-slot--hero" sx={{ display: "flex", minHeight: 0 }}>
              <Card
                variant="outlined"
                sx={{
                  ...cardSx,
                  borderRadius: 2.5,
                  background:
                    "linear-gradient(180deg, rgba(255,255,255,0.98) 0%, rgba(247,250,255,0.95) 100%)",
                  boxShadow: "0 10px 36px rgba(17, 38, 63, 0.09)",
                  borderColor: "rgba(19, 71, 125, 0.14)",
                }}
              >
                <CardHeader
                  title="Solution Space"
                  subheader="Explore and select candidate solutions in objective space"
                  action={
                    !summaryLoading && filteredCount > 0 ? (
                      <Typography variant="caption" color="text.secondary" sx={{ mt: 1.5, mr: 1, display: 'block' }}>
                        {filteredCount} solution{filteredCount !== 1 ? 's' : ''}
                      </Typography>
                    ) : undefined
                  }
                  sx={cardHeaderSx}
                />
                <CardContent sx={cardContentSx}>
                  <Box
                    className="main-grid__panel main-grid__panel--scatter"
                    sx={{
                      ...panelSx,
                      position: 'relative',
                      zIndex: 10,
                      display: 'flex',
                      flexDirection: 'column',
                      minHeight: 0,
                      px: 1.5,
                      pb: 1,
                      gap: 1,
                    }}
                  >
                    {!summaryLoading && filteredCount === 0 && (
                      <Alert severity="warning" sx={{ py: 0.25 }}>
                        No solutions match the current filters. Try broadening Scenario Filters or objective weights.
                      </Alert>
                    )}
                    {!summaryLoading && filteredCount > 0 && filteredCount < 5 && (
                      <Alert severity="info" sx={{ py: 0.25 }}>
                        Showing only {filteredCount} solution{filteredCount === 1 ? '' : 's'} with the current filters.
                      </Alert>
                    )}
                    <Box sx={{ flex: 1, minHeight: { xs: 300, md: 390 }, display: 'flex', position: 'relative' }}>
                      {summaryLoading && (
                        <Box sx={{ position: 'absolute', inset: 0, zIndex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: 1.5, bgcolor: 'rgba(255,255,255,0.8)', borderRadius: 1 }}>
                          <CircularProgress size={28} />
                          <Typography variant="caption" color="text.secondary">
                            Loading solutions{selectedUseCase ? ` for ${selectedUseCase}` : ''}…
                          </Typography>
                        </Box>
                      )}
                      <ScatterPlot
                        useCase={selectedUseCase}
                        solutionsData={completeData}
                        decision_keys={decisionKeys}
                        objective_keys={objectiveKeys}
                        objectiveUnits={objectiveUnits}
                        hyperparameter_keys={hyperparameterKeys}
                        input_parameter_keys={inputParameterKeys}
                        objectiveColorMap={objectiveColorMap}
                        onColorByChange={setClusterBy}
                        colorByField={clusterBy}
                        selectedSolution={selectedSolution ?? undefined}
                        onSolutionSelect={upsertScatterSelectionIntoComparison}
                        pinnedSolutions={pinnedSolutions}
                      />
                    </Box>
                  </Box>
                </CardContent>
              </Card>
            </Box>
            <Box className="main-grid__panel-slot main-grid__panel-slot--deep-dive" sx={{ display: "flex", minHeight: 0 }}>
              <Card
                variant="outlined"
                sx={{
                  ...cardSx,
                  borderRadius: 2.5,
                  background:
                    "linear-gradient(180deg, rgba(245,247,250,0.96) 0%, rgba(239,243,248,0.92) 100%)",
                  boxShadow: "0 6px 24px rgba(17, 38, 63, 0.06)",
                  borderColor: "rgba(79, 104, 129, 0.16)",
                }}
              >
                <CardHeader
                  title="Analysis Views"
                  subheader={
                    selectedSolution
                      ? `Viewing Solution #${selectedSolution['Solution ID'] ?? selectedSolution['solution_id'] ?? '—'}`
                      : 'Click a point on the chart to inspect a solution'
                  }
                  sx={{
                    ...cardHeaderSx,
                    '& .MuiCardHeader-subheader': { fontSize: '0.76rem', color: selectedSolution ? 'primary.main' : 'text.secondary', fontWeight: selectedSolution ? 600 : 400 },
                  }}
                />
                <Box sx={{ px: 1.25, pb: 0.5, flexShrink: 0 }}>
                  <Tabs
                    value={deepDiveTab}
                    onChange={(_, value) => setDeepDiveTab(value)}
                    variant="fullWidth"
                    sx={{
                      minHeight: 38,
                      '& .MuiTab-root': {
                        minHeight: 38,
                        fontSize: '0.84rem',
                        fontWeight: 600,
                        textTransform: 'none',
                      },
                      '& .MuiTabs-indicator': {
                        height: 3,
                        borderRadius: '3px 3px 0 0',
                      },
                    }}
                  >
                    <Tab label="Best Solution" />
                    <Tab label="Decision Space" />
                    <Tab label="Trade-offs" />
                  </Tabs>
                </Box>
                <CardContent sx={cardContentSx}>
                  <Box
                    className="main-grid__panel main-grid__panel--deep-dive-content"
                    sx={{ ...panelSx, px: 1.25, pb: 1.1, display: 'flex', flexDirection: 'column', gap: 1, minHeight: 0 }}
                  >
                    {deepDiveTab === 0 && (
                      <Box sx={{ flex: 1, minHeight: { xs: 250, md: 330 }, borderRadius: 1.5, pb: 0.5 }}>
                        <BestSolutionPanel
                          loading={summaryLoading}
                          filters={effectiveFilters}
                          weights={weights}
                          useCase={selectedUseCase}
                          decisionKeys={decisionKeys}
                          objectiveKeys={objectiveKeys}
                          objectiveUnits={objectiveUnits}
                          onSolutionFocus={setSelectedSolutionForUseCase}
                          focusedSolution={selectedSolution}
                          comparisonColumns={activeComparisonState.columns}
                          focusedColumnId={activeComparisonState.focusedColumnId}
                          onComparisonColumnsChange={handleComparisonColumnsChange}
                          onFocusedColumnIdChange={handleFocusedColumnIdChange}
                        />
                      </Box>
                    )}
                    {deepDiveTab === 1 && (
                      <>
                        <Typography variant="subtitle2" sx={{ textAlign: 'left', fontWeight: 600, color: 'text.secondary', fontSize: '0.78rem' }}>
                          {selectedUseCase === 'Cameo_datacenter' ? 'Network' : 'Decision Space'}
                        </Typography>
                        <Typography variant="caption" sx={{ textAlign: 'left', color: 'text.secondary' }}>
                          {selectedUseCase === 'Cameo_datacenter' ? 'Network distribution for the selected solution' : 'How this solution compares to all others'}
                        </Typography>
                        <Box sx={{ flex: 1, minHeight: { xs: 250, md: 330 }, borderRadius: 1.5, bgcolor: 'rgba(255,255,255,0.55)' }}>
                          {selectedUseCase === 'Cameo_datacenter' ? (
                            <NetworkGraphPanel
                              filters={filters}
                            />
                          ) : (
                            <DecisionVariablesChart
                              decisions={decisionDataForSelection.decisions}
                              loading={radarLoading}
                            />
                          )}
                        </Box>
                      </>
                    )}
                    {deepDiveTab === 2 && (
                      <>
                        <Typography variant="subtitle2" sx={{ textAlign: 'left', fontWeight: 700, color: 'text.primary' }}>
                          Trade-offs
                        </Typography>
                        <Typography variant="caption" sx={{ textAlign: 'left', color: 'text.secondary' }}>
                          Multi-objective trade-offs for the selected solution vs top N.
                        </Typography>
                        <Box sx={{  minHeight: { xs: 250, md: 300 }, borderRadius: 1.5, bgcolor: 'rgba(255,255,255,0.5)' }}>
                          <ParallelCoordinatesChart
                            ranks={rankData}
                            useCase={selectedUseCase}
                            filters={effectiveFilters}
                            weights={weights}
                            selectedSolutions={selectedSolutionsForPcp}
                            focusedSolution={selectedSolution ?? undefined}
                          />
                        </Box>
                      </>
                    )}
                  </Box>
                </CardContent>
              </Card>
            </Box>
          </Box>
        </Box>
      )}

      {/* Scenario Comparison Tab */}
      {tabIndex === 1 && (
        <Box className="main-grid__tab-panel main-grid__tab-panel--scenario" sx={tabContentSx}>
          <Box
            className="main-grid__scenario-layout"
            sx={{
              width: '100%',
              height: '100%',
              minHeight: 0,
              display: 'flex',
            }}
          >
            <Box sx={{ minHeight: 0, display: "flex", width: "100%" }}>
              <Card variant="outlined" sx={{ ...cardSx }}>
                <CardHeader
                  title="Scenario Comparison"
                  subheader="Each node is a group of solutions sharing the same scenario attributes. Edges show which group dominates another — click nodes to compare them."
                  sx={cardHeaderSx}
                />
                <CardContent sx={cardContentSx}>
                  <Box sx={{ width: "100%", height: "100%", minHeight: 0, display: "flex" }}>
                    <TradeoffLatticePlot
                      useCase={selectedUseCase}
                      filters={effectiveFilters}
                      weights={weights}
                    />
                  </Box>
                </CardContent>
              </Card>
            </Box>
            <Box sx={{ minHeight: 0, display: "none" }}>
              <Box
                sx={{
                  width: "100%",
                  height: "100%",
                  minHeight: 0,
                  border: '1px solid',
                  borderColor: 'divider',
                  borderRadius: 2,
                  bgcolor: 'background.paper',
                  overflow: 'hidden',
                }}
              >
                <LMPPlot
                  useCase={selectedUseCase}
                  filters={effectiveFilters}
                  selectedSolution={selectedSolution ?? undefined}
                />
              </Box>
            </Box>
          </Box>
        </Box>
      )}

      {/* mooCHAT FAB — hidden when drawer is open to prevent overlap */}
      {!chatOpen && (
        <Fab
          variant="extended"
          color="primary"
          onClick={() => setChatOpen(true)}
          sx={{
            position: "fixed",
            bottom: 28,
            right: 28,
            zIndex: 1300,
            gap: 0.75,
            px: 2.5,
            textTransform: 'none',
            boxShadow: proactiveBubble
              ? '0 4px 16px rgba(25,118,210,0.35), 0 0 0 4px rgba(25,118,210,0.25), 0 0 0 9px rgba(25,118,210,0.1)'
              : '0 4px 16px rgba(25,118,210,0.35)',
            '@keyframes fabRing': {
              '0%,100%': {
                boxShadow: '0 4px 16px rgba(25,118,210,0.35), 0 0 0 4px rgba(25,118,210,0.25), 0 0 0 9px rgba(25,118,210,0.1)',
              },
              '50%': {
                boxShadow: '0 4px 16px rgba(25,118,210,0.35), 0 0 0 6px rgba(25,118,210,0.18), 0 0 0 13px rgba(25,118,210,0.06)',
              },
            },
            animation: proactiveBubble ? 'fabRing 2.4s ease-in-out infinite' : 'none',
            '&:hover': { boxShadow: '0 6px 20px rgba(25,118,210,0.5)' },
          }}
        >
          <AutoAwesomeIcon />
          mooCHAT
        </Fab>
      )}

      <Drawer
        anchor="right"
        open={chatOpen}
        onClose={() => setChatOpen(false)}
        slotProps={{ paper: { sx: { width: 420, p: 1.5, background: '#fafafa' } } }}
      >
        <AgentChatPanel onClose={() => setChatOpen(false)} />
      </Drawer>

      {!chatOpen && <ProactiveInsightBubble onOpenChat={() => setChatOpen(true)} />}

      {/* Cameo Tab */}
      {tabIndex === 2 && (
        <Box className="main-grid__tab-panel main-grid__tab-panel--cameo" sx={tabContentSx}>
          <Box
            className="main-grid__cameo-layout"
            sx={{ width: '100%', height: '100%', minHeight: 0, display: 'flex', flexDirection: 'column', gap: 1 }}
          >
            <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexShrink: 0 }}>
              <Typography variant="body2" color="text.secondary">
                Access the Cameo system model browser. If blocked by your organization's auth policy, use the button to open it directly.
              </Typography>
              <Button
                variant="outlined"
                size="small"
                href="https://cameo.pnl.gov/"
                target="_blank"
                rel="noreferrer"
                sx={{ ml: 2, flexShrink: 0, whiteSpace: 'nowrap' }}
              >
                Open in new tab
              </Button>
            </Box>
            <Box
              className="main-grid__cameo-frame-wrapper"
              sx={{
                flex: 1,
                minHeight: 0,
                border: '1px solid',
                borderColor: 'divider',
                borderRadius: 1,
                overflow: 'hidden',
                bgcolor: 'background.paper',
                position: 'relative',
              }}
            >
              {cameoLoading && (
                <Box sx={{
                  position: 'absolute', inset: 0, zIndex: 1,
                  display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center',
                  gap: 1.5, bgcolor: 'background.paper',
                }}>
                  <CircularProgress size={32} />
                  <Typography variant="body2" color="text.secondary">Loading Cameo…</Typography>
                </Box>
              )}
              <Box
                component="iframe"
                title="Cameo"
                src="https://cameo.pnl.gov/"
                onLoad={() => setCameoLoading(false)}
                sx={{ width: '100%', height: '100%', border: 0 }}
                referrerPolicy="strict-origin-when-cross-origin"
              />
            </Box>
          </Box>
        </Box>
      )}
    </Box>
  );
};

export default MainGrid;
