import { useState } from 'react';
import { Box, Tabs, Tab, Typography } from '@mui/material';
import Plot from 'react-plotly.js';

export default function MainGrid() {
  const [tabIndex, setTabIndex] = useState(0);

  const handleChange = (_event: React.SyntheticEvent, newValue: number) => {
    setTabIndex(newValue);
  };

  return (
    <Box sx={{ flexGrow: 1, p: 3, bgcolor: 'background.default', minHeight: '100vh', pt: 8 }}>
      {/* Tabs Navigation */}
      <Tabs value={tabIndex} onChange={handleChange} variant="fullWidth">
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
  );
}
