import React, { useState, useEffect } from "react";
import { Box, Tabs, Tab, Grid, LinearProgress, Typography } from "@mui/material";

// Import Plot Components
import ScatterPlot from './OffshoreWindfarmPlots/ScatterPlot';
// import ClusterScatterPlot from './OffshoreWindfarmPlots/ClusterScatterPlot';
import DualRadarChart, { RadarData } from './OffshoreWindfarmPlots/DualRadarChart';
import DecisionPlot from './OffshoreWindfarmPlots/DecisionPlot';
import LMPPlot from './OffshoreWindfarmPlots/LMPPlot';
import Summary from './OffshoreWindfarmPlots/Summary';
import ParallelCoordinatesChart from './OffshoreWindfarmPlots/ParallelCoordinatesChart';

import config from "../config";
const { API_BASE_URL } = config;

interface MainGridProps {
  selectedUseCase: string;
  filters: Record<string, string[]>;
  weights: Record<string, number>;
  onWeightsChange?: (weights: Record<string, number>) => void;
}

interface Solution {
  [key: string]: any;
}

const MainGrid: React.FC<MainGridProps> = ({
  selectedUseCase,
  filters,
  weights,
  onWeightsChange,
}) => {
  const [tabIndex, setTabIndex] = useState(0);
  const [clusterBy, setClusterBy] = useState<string>("AI-Generated");
  const [objectiveNames, setObjectiveNames] = useState<string[]>([]);

  // State for Summary
  const [completeData, setCompleteData] = useState<Solution[]>([]);
  const [summaryData, setSummaryData] = useState<Solution[]>([]);
  const [summaryLoading, setSummaryLoading] = useState<boolean>(true);
  const [selectedSolution, setSelectedSolution] = useState<Solution | null>(null);

  // State for DualRadarChart
  const [radarData, setRadarData] = useState<{
    objectives: RadarData[];
    decisions: RadarData[];
  }>({
    objectives: [],
    decisions: []
  });
  const [radarLoading, setRadarLoading] = useState<boolean>(true);
  const [rankData, setRankData] = useState<Record<string, any>>({});

  const [error, setError] = useState<string | null>(null);

  // Fetch objective names for weight UI
  useEffect(() => {
    const fetchObjectives = async () => {
      try {
        const params = new URLSearchParams();
        params.append("use_case", selectedUseCase);

        Object.entries(weights).forEach(([key, value]) => {
          params.append(`weight_${key}`, value.toString());
        });

        const response = await fetch(`${API_BASE_URL}/api/objective?${params.toString()}`);
        if (!response.ok) throw new Error("Failed to fetch objectives");

        const data = await response.json();

        const objNames = Object.keys(data.weights_used || {});
        setObjectiveNames(objNames);
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
    const fetchData = async () => {
      if (!selectedUseCase || !Object.keys(filters).length || !Object.keys(weights).length) return;
  
      setSummaryLoading(true);
      setRadarLoading(true);
      setError(null);
  
      const queryParams = new URLSearchParams();
  
      // Add filters
      Object.entries(filters).forEach(([key, values]) =>
        values.forEach(value => queryParams.append(key, value))
      );
  
      // Add weights
      Object.entries(weights).forEach(([key, value]) =>
        queryParams.append(`weight_${key}`, value.toString())
      );
  
      // Add use case
      queryParams.append('use_case', selectedUseCase);
  
      try {
        const response = await fetch(`${API_BASE_URL}/api/solutions?${queryParams.toString()}`);
        if (!response.ok) throw new Error("Failed to fetch shared data");
  
        const result = await response.json();
        console.log("Fetched unified data:", result.solutions);
        setCompleteData(result.solutions);
  
        // Process summary data
        const orderedColumns = [...(result.index_keys || []), ...(result.hyperparameter_keys || []), ...(result.decision_keys || []), ...(result.additional_cols || [])];
        const processedSolutions = result.solutions.map(solution => {
          const orderedSolution: Record<string, any> = {};
          orderedColumns.forEach(key => {
            if (solution.hasOwnProperty(key)) {
              orderedSolution[key] = solution[key];
            }
          });
          return orderedSolution;
        });
        console.log("Processed solutions for summary:", processedSolutions);
        setSummaryData(processedSolutions);

        // Save ranks separately
        setRankData(result.ranks || {});
  
        // Radar chart data
        const computeChartData = (keys: string[]) => {
          return keys.map((key) => {
            const values = result.solutions.map(row => parseFloat(row[key]) || 0);
            const min = Math.min(...values);
            const max = Math.max(...values);
            return {
              name: key,
              distribution: values,
              selected: parseFloat(result.solutions[0]?.[key]) || 0,
              min: min || 1,
              max: max || 1
            };
          });
        };
  
        setRadarData({
          objectives: computeChartData(result.objective_keys || []),
          decisions: computeChartData(result.decision_keys || [])
        });
  
      } catch (err) {
        console.error("Error fetching unified data:", err);
        setError("Failed to load visualizations.");
        setSummaryData([]);
        setRadarData({ objectives: [], decisions: [] });
      } finally {
        setSummaryLoading(false);
        setRadarLoading(false);
      }
    };
  
    fetchData();
  }, [
    selectedUseCase,
    JSON.stringify(filters),
    JSON.stringify(weights)
  ]);

  const handleWeightChange = (newWeights: Record<string, number>) => {
    if (onWeightsChange) {
      onWeightsChange(newWeights);
    }
  };

  if (summaryLoading || radarLoading) {
    return (
      <Box sx={{ textAlign: 'center', mt: 12 }}>
        <LinearProgress />
        <Typography>Loading visualizations...</Typography>
      </Box>
    );
  }

  if (error) {
    return (
      <Box sx={{ textAlign: 'center', mt: 12 }}>
        <Typography color="error">{error}</Typography>
      </Box>
    );
  }

  return (
    <Box sx={{ width: "78vw", px: { xs: 1, sm: 2 }, py: 2 }}>
      {/* Tabs */}
      <Box sx={{ borderBottom: 1, borderColor: "divider", mb: 3 }}>
        <Tabs
          value={tabIndex}
          onChange={(_, v) => setTabIndex(v)}
          aria-label="navigation tabs"
          variant="fullWidth"
        >
          <Tab label="Decision Making" />
          <Tab label="Scenario Comparison" />
        </Tabs>
      </Box>

      {/* Tab Content */}
      {tabIndex === 0 && (
        <Box sx={{ width: "100%" }}>
          {/* First Row - Charts */}
          <Grid container spacing={2} sx={{ width: '100%' }}>
            <Grid item xs={12} md={6}>
              <Box sx={{ position: 'relative', zIndex: 10 }}>
                <ScatterPlot
                  useCase={selectedUseCase} 
                  solutionsData={completeData} 
                  onClusterByChange={setClusterBy}
                />
              </Box>
            </Grid>
            <Grid item xs={12} md={6}>
              <Box sx={{ width: '100%' }}>
                <ParallelCoordinatesChart ranks={rankData} />
              </Box>
              <Box sx={{ width: '100%', mt: 4 }}>
                <Summary 
                  data={summaryData} 
                  loading={summaryLoading} 
                  onRowSelect={(solution) => setSelectedSolution(solution)}
                />
              </Box>
            </Grid>
          </Grid>

          {/* Second Row - Summary & LMP */}
          <Grid container spacing={2} sx={{ mt: 2, width: '100%' }}>
            <Grid item xs={12} md={6}>
              <Box sx={{ overflow: 'hidden', position: 'relative', zIndex: 1 }}>
                <LMPPlot 
                  useCase={selectedUseCase} 
                  filters={filters} 
                  selectedSolution={selectedSolution}
                />
              </Box>
            </Grid>
            <Grid item xs={12} md={6}>
              <Box>
                <DualRadarChart
                  objectives={radarData.objectives}
                  decisions={radarData.decisions}
                  loading={radarLoading}
                />
              </Box>
            </Grid>
          </Grid>

          {/* Third Row - Charts */}
          <Grid container spacing={2} sx={{ width: '100%' }}>
            <Grid item xs={12} md={12}>
              <DecisionPlot
                useCase={selectedUseCase}
                filters={filters}
                weights={weights}
                clusterBy={clusterBy}
              />
            </Grid>
          </Grid>
        </Box>
      )}
    </Box>
  );
};

export default MainGrid;