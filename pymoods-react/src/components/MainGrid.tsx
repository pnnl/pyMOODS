import React, { useState } from 'react';
import { Box, Tabs, Tab, Typography, Grid } from '@mui/material';

// Import Plot Components
import ClusterScatterPlot from './OffshoreWindfarmPlots/ClusterScatterPlot';
import ObjectivePlot from './OffshoreWindfarmPlots/ObjectivePlot';
import DecisionPlot from './OffshoreWindfarmPlots/DecisionPlot';
import LMPPlot from './OffshoreWindfarmPlots/LMPPlot';

interface MainGridProps {
  selectedUseCase: string;
  filters: Record<string, string[]>;
}

const MainGrid: React.FC<MainGridProps> = ({ selectedUseCase, filters }) => {
  const [tabIndex, setTabIndex] = useState(0);
  // console.log("MainGrid props:", { selectedUseCase, filters });

  const handleChange = (_event: React.SyntheticEvent, newValue: number) => {
    setTabIndex(newValue);
  };

  return (
    <Box
      sx={{
        width: '100%',
        maxWidth: { sm: '100%', md: '1700px' },
        minHeight: `calc(100vh - 64px)`,
        mt: `56px`,
        display: 'flex',
        flexDirection: 'column',
        overflow: 'auto',
      }}
    >
      {/* Tabs Navigation */}
      <Tabs
        value={tabIndex}
        onChange={handleChange}
        variant="standard"
        sx={{
          '.MuiTab-root': {
            outline: 'none',
            fontSize: '12px',
            '&.Mui-selected': {
              borderBottom: '3px solid',
              borderColor: 'primary.main',
            },
          },
        }}
      >
        <Tab label="Decision Making" />
        <Tab label="Scenario Comparison" />
      </Tabs>

      {/* Tab Content */}
      <Box sx={{ mt: 1 }}>
        {/* Decision Making Tab */}
        {tabIndex === 0 && (
          <Box>
            <Grid container spacing={2}>
              {/* Top row with Offshore, Objective, and Decision plots */}
              <Grid item xs={12} md={5}>
                <ClusterScatterPlot useCase={selectedUseCase} filters={filters} />
              </Grid>
              <Grid item xs={12} md={2}>
                <ObjectivePlot useCase={selectedUseCase} filters={filters} />
              </Grid>
              <Grid item xs={12} md={5}>
                <DecisionPlot useCase={selectedUseCase} filters={filters} />
              </Grid>

              {/* Bottom row with 2 LMPPlot components */}
              <Grid item xs={12} md={6}>
                <LMPPlot useCase={selectedUseCase} filters={filters} />
              </Grid>
              <Grid item xs={12} md={6}>
                <LMPPlot useCase={selectedUseCase} filters={filters} />
              </Grid>
            </Grid>
          </Box>
        )}

        {/* Scenario Comparison Tab */}
        {tabIndex === 1 && (
          <Box>
            <Typography variant="h6">Explore</Typography>
            <Typography variant="body1">
              Use filters in the sidebar to dynamically update scenario data.
            </Typography>
            {/* Optional: Add Plotly Explore tab later */}
          </Box>
        )}
      </Box>
    </Box>
  );
};

export default MainGrid;