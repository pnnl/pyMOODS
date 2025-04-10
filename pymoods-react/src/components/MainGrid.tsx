import { useState } from 'react';
import { Box, Tabs, Tab, Typography, Grid } from '@mui/material';
import createPlotlyComponent from 'react-plotly.js/factory';
import * as Plotly from 'plotly.js-basic-dist';
import LMPPlot from './OffshoreWindfarmPlots/LMPPlot';
import OffshoreWindfarmClusterScatterPlot from './OffshoreWindfarmPlots/ClusterScatterPlot';
import ObjectivePlot from './OffshoreWindfarmPlots/ObjectivePlot';
import DecisionPlot from './OffshoreWindfarmPlots/DecisionPlot';

const Plot = createPlotlyComponent(Plotly);

export default function MainGrid() {
  const navbarHeight= 64;
  const [tabIndex, setTabIndex] = useState(0);

  const handleChange = (_event: React.SyntheticEvent, newValue: number) => {
    setTabIndex(newValue);
  };

  return (
    <Box 
      sx={{ 
        width: '100%', 
        maxWidth: { sm: '100%', md: '1700px' }, 
        minHeight: `calc(100vh - ${navbarHeight}px)`,
        mt: `56px`,
        flex: 1,
        flexDirection: 'column',
        overflow: 'hidden',
      }}
    >
      {/* Tabs Navigation */}
      <Tabs 
        value={tabIndex} 
        onChange={handleChange} 
        variant="standard" 
        sx={{
          '.MuiTab-root': { 
        // outline: 'none',
        fontSize: '12px', // Smaller font size
        '&.Mui-selected': { borderBottom: '3px solid'},
          }
        }}
      >
        <Tab label="Decision Making" />
        <Tab label="Scenario Comparison" />
      </Tabs>

      {/* Tab Content */}
      <Box sx={{ mt: 2, ml: 2 }}>
        {/* Decision Making Tab */}
        {tabIndex === 0 && (
          <Box>
            <Grid container spacing={2}>
              {/* Top row with Offshore, Objective, and Decision plots */}
              <Grid item xs={12} md={4}>
                <OffshoreWindfarmClusterScatterPlot />
              </Grid>
              <Grid item xs={12} md={4}>
                <ObjectivePlot />
              </Grid>
              <Grid item xs={12} md={4}>
                <DecisionPlot />
              </Grid>

              {/* Bottom row with 2 LMPPlot components */}
              <Grid item xs={12} md={6}>
                <LMPPlot />
              </Grid>
              <Grid item xs={12} md={6}>
                <LMPPlot />
              </Grid>
            </Grid>
          </Box>
        )}

        {/* Scenario Comparison Tab */}
        {tabIndex === 1 && (
          <Box>
            <Typography variant="h6">Explore</Typography>
            <Plot
              data={[
                { type: 'bar', x: ['A', 'B', 'C'], y: [4, 7, 9] }
              ]}
              layout={{ title: 'Explore Plot' }}
            />
          </Box>
        )}
      </Box>
    </Box>
  )
}
