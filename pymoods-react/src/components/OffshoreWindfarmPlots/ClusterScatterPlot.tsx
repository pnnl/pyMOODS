import React, { useState, useEffect } from 'react';
import * as Plotly from "plotly.js-basic-dist";
import createPlotlyComponent from "react-plotly.js/factory";
import { Box, Typography, Select, MenuItem, FormControl, InputLabel } from '@mui/material';

// Import centralized config
import config from '../../config';
const { API_BASE_URL } = config;

const Plot = createPlotlyComponent(Plotly);

interface ScatterplotData {
  data: Plotly.Data[];
  layout: Partial<Plotly.Layout>;
  config?: Partial<Plotly.Config>;
}

interface ClusterScatterPlotProps {
  useCase: string;
  filters: Record<string, string[]>;
}

const ClusterScatterPlot: React.FC<ClusterScatterPlotProps> = ({ useCase, filters }) => {
  const [scatterplotData, setScatterplotData] = useState<ScatterplotData | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [clusterBy, setClusterBy] = useState<string>('location'); // Default value

  // Extract available filter keys for cluster options
  const clusterOptions = Object.keys(filters);

  // Fetch scatterplot data
  useEffect(() => {
    if (!useCase) return;

    setLoading(true);

    const queryParams = new URLSearchParams();

    // Add selected cluster field
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
  }, [useCase, filters, clusterBy]); // Refetch when clusterBy changes

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

  return (
    <Box sx={{ width: '100%',
      mt: 1,
      mb: 1, 
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center', 
      gap: 1, 
      flexGrow: 1 
    }}>
      {/* Clustering Dropdown */}
      <FormControl fullWidth sx={{ minWidth: 150, maxWidth: 250, width: '100%' }}>
        <InputLabel id="cluster-by-select-label">Cluster By</InputLabel>
        <Select
          labelId="cluster-by-select-label"
          value={clusterBy}
          label="Cluster By"
          onChange={(e) => setClusterBy(e.target.value)}
          sx={{
            height: 40
          }}
        >
          {clusterOptions.map((option) => (
            <MenuItem key={option} value={option}>
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
    </Box>
  );
};

export default ClusterScatterPlot;