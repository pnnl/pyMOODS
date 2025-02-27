import { useState } from 'react';
import { Box, Tabs, Tab, Typography } from '@mui/material';
import Plot from 'react-plotly.js';

export default function MainGrid() {
  const appNavbarHeight = 200;
  const [tabIndex, setTabIndex] = useState(0);

  const handleChange = (_event: React.SyntheticEvent, newValue: number) => {
    setTabIndex(newValue);
  };

  return (
    <Box 
      sx={{ 
        width: '100%', 
        maxWidth: { sm: '100%', md: '1700px' }, 
        minHeight: `calc(100vh - ${appNavbarHeight}px)`,
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
        <Tab label="Overview" />
        <Tab label="Offshore" />
      </Tabs>

      {/* Tab Content */}
      <Box sx={{ mt: 2 }}>
        {tabIndex === 0 && (
          <Box>
            <Typography variant="h6">Overview</Typography>
            <Plot
              data={[
                { type: 'scatter', mode: 'lines+markers', x: [1, 2, 3], y: [2, 6, 3] }
              ]}
              layout={{ title: 'Overview Plot' }}
            />
          </Box>
        )}

        {tabIndex === 1 && (
          <Box>
            <Typography variant="h6">Offshore</Typography>
            <Plot
              data={[
                { type: 'bar', x: ['A', 'B', 'C'], y: [4, 7, 9] }
              ]}
              layout={{ title: 'Offshore Plot' }}
            />
          </Box>
        )}
      </Box>
    </Box>
  )
}
