import { useState } from 'react';
import { Box, Tabs, Tab, Typography } from '@mui/material';
import createPlotlyComponent from 'react-plotly.js/factory';
import Plotly from 'plotly.js-basic-dist';
import OffshoreScatterPlot from './OffshoreScatterPlot';
import LMPPlot from './LMPPlot';

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
        // display: 'flex',
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
            outline: 'none',
            '&.Mui-selected': { borderBottom: '3px solid'},
          }
        }}
      >
        <Tab label="Use Cases" />
        <Tab label="Exploratory Analysis" />
      </Tabs>

      {/* Tab Content */}
      <Box sx={{ mt: 2 }}>
        {/* Use Case Tab */}
        {tabIndex === 0 && (
          <Box>
            <Typography variant="h6">Solution Space</Typography>
            <LMPPlot  />
          </Box>
        )}

        {/* Exploratory Analysis Tab */}
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
