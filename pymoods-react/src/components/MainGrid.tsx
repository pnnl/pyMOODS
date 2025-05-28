import React, { useState, useEffect } from 'react';
import { Box, Tabs, Tab, Grid } from '@mui/material';

// Import Plot Components
import ClusterScatterPlot from './OffshoreWindfarmPlots/ClusterScatterPlot';
import ObjectivePlot from './OffshoreWindfarmPlots/ObjectivePlot';
import DecisionPlot from './OffshoreWindfarmPlots/DecisionPlot';
import LMPPlot from './OffshoreWindfarmPlots/LMPPlot';

import config from '../config';
const { API_BASE_URL } = config;

interface MainGridProps {
  selectedUseCase: string;
  filters: Record<string, string[]>;
  weights: Record<string, number>;
  onWeightsChange?: (weights: Record<string, number>) => void;
}

const MainGrid: React.FC<MainGridProps> = ({
  selectedUseCase,
  filters,
  weights,
  onWeightsChange,
}) => {
  const [tabIndex, setTabIndex] = useState(0);
  const [objectiveNames, setObjectiveNames] = useState<string[]>([]);
  const [clusterBy, setClusterBy] = useState<string>(
    Object.keys(filters).length > 0 ? Object.keys(filters)[0] : ''
  );

  // Fetch objectives and set default weights if necessary
  useEffect(() => {
    const fetchObjectives = async () => {
      try {
        const params = new URLSearchParams();
        params.append('use_case', selectedUseCase);

        Object.entries(weights).forEach(([key, value]) => {
          params.append(`weight_${key}`, value.toString());
        });

        const response = await fetch(`${API_BASE_URL}/api/objective?${params.toString()}`);
        const data = await response.json();

        const objNames = Object.keys(data.weights_used || {});
        setObjectiveNames(objNames);
      } catch (err) {
        console.error('Error fetching objectives:', err);
      }
    };

    if (selectedUseCase) fetchObjectives();
  }, [selectedUseCase, weights]);

  const handleWeightChange = (newWeights: Record<string, number>) => {
    console.log('MainGrid - Received weights from child:', newWeights);
    if (onWeightsChange) {
      onWeightsChange(newWeights);
    }
  };

  const handleClusterByChange = (newClusterBy: string) => {
    setClusterBy(newClusterBy);
  };

  // Automatically select the first filter key as clusterBy when filters change
  useEffect(() => {
    if (Object.keys(filters).length > 0 && !clusterBy) {
      const availableKeys = Object.keys(filters);
      setClusterBy(availableKeys[0]);
    }
  }, [filters]);

  return (
    <Box sx={{ width: '100%' }}>
      {/* Tabs */}
      <Box sx={{ borderBottom: 1, borderColor: 'divider', mb: 2, pt: 0 }}>
        <Tabs value={tabIndex} onChange={(_, v) => setTabIndex(v)} aria-label="navigation tabs">
          <Tab label="Decision Making" />
          <Tab label="Scenario Comparison" />
        </Tabs>
      </Box>

      {/* Tab Content */}
      {tabIndex === 0 && (
        <Box>
          <Grid container spacing={2}>
            <Grid item xs={12} md={4}>
              <ClusterScatterPlot
                useCase={selectedUseCase}
                filters={filters}
                weights={weights}
                onWeightsChange={handleWeightChange}
                onClusterByChange={handleClusterByChange}
              />
            </Grid>
            <Grid item xs={12} md={3}>
              <ObjectivePlot
                useCase={selectedUseCase}
                filters={filters}
                onWeightsChange={handleWeightChange}
              />
            </Grid>
            <Grid item xs={12} md={5}>
              <DecisionPlot
                useCase={selectedUseCase}
                filters={filters}
                weights={weights}
                clusterBy={clusterBy}
              />
            </Grid>

            <Grid item xs={12} md={6}>
              <LMPPlot useCase={selectedUseCase} filters={filters} />
            </Grid>
            <Grid item xs={12} md={6}>
              <LMPPlot useCase={selectedUseCase} filters={filters} />
            </Grid>
          </Grid>
        </Box>
      )}
    </Box>
  );
};

export default MainGrid;
