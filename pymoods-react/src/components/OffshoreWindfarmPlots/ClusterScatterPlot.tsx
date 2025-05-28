import React, { useState, useEffect } from 'react';
import * as Plotly from "plotly.js-basic-dist";
import createPlotlyComponent from "react-plotly.js/factory";
import {
  Box,
  Typography,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper
} from '@mui/material';

// Import centralized config
import config from '../../config';
const { API_BASE_URL } = config;

const Plot = createPlotlyComponent(Plotly);

interface ScatterplotData {
  data: Plotly.Data[];
  layout: Partial<Plotly.Layout>;
}

interface ClusterSummary {
  cluster: string | number;
  count: number;
  avg_weighted_score: number;
}

interface ClusterScatterPlotProps {
  useCase: string;
  filters: Record<string, string[]>;
  weights: Record<string, number>; // ✅ Required prop
  onWeightsChange?: (weights: Record<string, number>) => void;
  onClusterByChange?: (clusterBy: string) => void;
}

const ClusterScatterPlot: React.FC<ClusterScatterPlotProps> = ({
  useCase,
  filters,
  weights,
  onClusterByChange
}) => {
  const [scatterplotData, setScatterplotData] = useState<ScatterplotData | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [clusterBy, setClusterBy] = useState<string>(() => {
    const availableOptions = Object.keys(filters);
    return availableOptions.length > 0 ? availableOptions[0] : 'unknown';
  });

  const [clusterSummaries, setClusterSummaries] = useState<ClusterSummary[]>([]);
  const [summaryLoading, setSummaryLoading] = useState<boolean>(false);

  // Update clusterBy if filters change and value is invalid
  useEffect(() => {
    const availableOptions = Object.keys(filters);
    if (availableOptions.length > 0 && !availableOptions.includes(clusterBy)) {
      const newClusterBy = availableOptions[0];
      setClusterBy(newClusterBy);
      if (onClusterByChange) {
        onClusterByChange(newClusterBy);
      }
    }
  }, [filters]);

  // Fetch scatterplot data
  useEffect(() => {
    if (!useCase) return;

    setLoading(true);

    const queryParams = new URLSearchParams();

    // Add selected cluster field
    console.log(clusterBy)
    queryParams.append('cluster_by', clusterBy);

    // Add other filters
    Object.entries(filters).forEach(([key, values]) => {
      if (Array.isArray(values) && values.length > 0) {
        values.forEach(value => queryParams.append(key, value));
      }
    });

    const url = `${API_BASE_URL}/api/scatterplot?${queryParams.toString()}&use_case=${encodeURIComponent(useCase)}`;

    fetch(url)
      .then((response) => {
        if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
        return response.json();
      })
      .then((data) => {
        try {
          const plotData = JSON.parse(data.scatterplot);
          setScatterplotData(plotData);
        } catch (parseError) {
          console.error("Failed to parse Plotly JSON:", parseError);
        }
      })
      .catch((error) => {
        console.error('Error fetching or parsing scatterplot:', error);
      })
      .finally(() => {
        setLoading(false);
      });
  }, [useCase, filters, clusterBy]);

  // Fetch cluster summaries from /api/solutions
  useEffect(() => {
    if (!useCase || !filters || !clusterBy || !weights) return;

    const queryParams = new URLSearchParams();

    // Add filters
    Object.entries(filters).forEach(([key, values]) => {
      if (Array.isArray(values)) {
        values.forEach(value => queryParams.append(key, value));
      }
    });

    // Add objective weights
    Object.entries(weights).forEach(([key, value]) => {
      queryParams.append(`weight_${key}`, value.toString());
    });

    // Add use_case and cluster_by
    queryParams.append('use_case', useCase);
    queryParams.append('cluster_by', clusterBy);

    setSummaryLoading(true);
    setClusterSummaries([]);

    fetch(`${API_BASE_URL}/api/solutions?${queryParams.toString()}`)
      .then((response) => {
        if (!response.ok) throw new Error("Failed to fetch cluster summaries");
        return response.json();
      })
      .then((data) => {
        const sorted = [...data.clusters].sort((a, b) => b.avg_weighted_score - a.avg_weighted_score);
        setClusterSummaries(sorted);
      })
      .catch((error) => {
        console.error('Error fetching cluster summaries:', error);
      })
      .finally(() => {
        setSummaryLoading(false);
      });
  }, [useCase, filters, clusterBy, weights]); // ✅ Now depends on weights

  const handleClusterByChange = (e: React.ChangeEvent<{ value: unknown }>) => {
    const newClusterBy = e.target.value as string;
    setClusterBy(newClusterBy);
    if (onClusterByChange) {
      onClusterByChange(newClusterBy);
    }
  };

  if (loading || !scatterplotData) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '50vh' }}>
        <Typography variant="body1">Loading Scatterplot...</Typography>
      </Box>
    );
  }

  const improvedLayout = {
    ...scatterplotData.layout
  };

  // Define consistent colors for each cluster
  const clusterColors = [
    "#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd",
    "#8c564b", "#e377c2", "#7f7f7f", "#bcbd22", "#17becf"
  ];

  return (
    <Box sx={{ width: '100%', mt: 1, mb: 1, display: 'flex', flexDirection: 'column', gap: 1 }}>
      {/* Clustering Dropdown */}
      <FormControl 
        fullWidth 
        sx={{ 
          display: 'flex', 
          justifyContent: 'center',
          mb: 2,
          maxWidth: 150,
          margin: '0 auto'
        }}
      >
        <InputLabel 
          id="cluster-by-select-label" 
          sx={{ fontSize: '0.875rem' }}
        >
          Cluster By
        </InputLabel>
        <Select
          labelId="cluster-by-select-label"
          value={clusterBy}
          label="Cluster By"
          onChange={handleClusterByChange}
          sx={{ 
            height: 40,
            fontSize: '0.875rem',
            textAlign: 'center'
          }}
        >
          {Object.keys(filters).map((option) => (
            <MenuItem 
              key={option} 
              value={option}
              sx={{ fontSize: '0.875rem' }}
            >
              {option}
            </MenuItem>
          ))}
        </Select>
      </FormControl>

      {/* Plot */}
      <Box sx={{ width: '100%' }}>
        <Plot
          data={scatterplotData.data}
          layout={improvedLayout}
          config={{
            responsive: true,
            scrollZoom: true,
            modeBarButtonsToRemove: ['toggleSpikelines']
          }}
          style={{ width: '100%' }}
          useResizeHandler
        />
      </Box>

      {/* Cluster Summary Table */}
      <Box sx={{ mt: 2 }}>
        <TableContainer component={Paper}>
          <Table size="small">
            <TableHead>
              <TableRow>
                <TableCell align="left" sx={{ fontWeight: 'bold', width: '100px' }}>Cluster</TableCell>
                <TableCell align="center" sx={{ fontWeight: 'bold', width: '90px' }}>#Solutions</TableCell>
                <TableCell align="right" sx={{ fontWeight: 'bold', width: '110px' }}>Score</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {summaryLoading ? (
                <TableRow>
                  <TableCell colSpan={3} align="center">Loading...</TableCell>
                </TableRow>
              ) : clusterSummaries.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={3} align="center">No clusters found.</TableCell>
                </TableRow>
              ) : (
                clusterSummaries.map((row, index) => (
                  <TableRow
                    key={`cluster-${index}`}
                    sx={{
                      backgroundColor: clusterColors[index % clusterColors.length],
                      color: 'white',
                      '& .MuiTableCell-root': {
                        color: 'white'
                      }
                    }}
                  >
                    <TableCell>{row.cluster}</TableCell>
                    <TableCell align="center">{row.count}</TableCell>
                    <TableCell align="right">{row.avg_weighted_score.toFixed(2)}</TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </TableContainer>
      </Box>
    </Box>
  );
};

export default ClusterScatterPlot;