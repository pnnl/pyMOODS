import React, { useState, useEffect } from 'react';
import * as Plotly from "plotly.js-basic-dist";
import createPlotlyComponent from "react-plotly.js/factory";
import {
  Box,
  Typography,
  Select,
  MenuItem,
  FormControl,
  InputLabel
} from '@mui/material';

// Import centralized config
import config from '../../config';
const { API_BASE_URL } = config;

const Plot = createPlotlyComponent(Plotly);

interface ScatterplotData {
  data: Plotly.Data[];
  layout: Partial<Plotly.Layout>;
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
          onChange={(e) => {
            const newClusterBy = e.target.value as string;
            setClusterBy(newClusterBy);
            if (onClusterByChange) {
              onClusterByChange(newClusterBy);
            }
          }}
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
          <MenuItem 
            key="AI-Generated" 
            value="AI-Generated"
            sx={{ fontSize: '0.875rem' }}
          >
            AI-Generated
          </MenuItem>
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