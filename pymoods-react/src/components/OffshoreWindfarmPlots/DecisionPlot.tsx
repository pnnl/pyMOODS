import { useState, useEffect } from 'react';
import Plotly from "plotly.js-basic-dist";
import createPlotlyComponent from "react-plotly.js/factory";
import { Box } from '@mui/material';

const apiBaseUrl = 'http://moods-dev.pnl.gov/8080';
// const apiBaseUrl = 'http://localhost:8080'; // Uncomment this line if you are running the API locally

const Plot = createPlotlyComponent(Plotly);

interface DecisionPlotData {
  data: Plotly.Data[];
  layout: Partial<Plotly.Layout>;
  config?: Partial<Plotly.Config>;
}

const DecisionPlot = () => {
  const [decisionPlotData, setDecisionPlotData] = useState<DecisionPlotData | null>(null);
  const [loading, setLoading] = useState<boolean>(true);

  // Fetch decision space graph data from the API
  useEffect(() => {
    setLoading(true);
    fetch(`${apiBaseUrl}/api/decision`)
      .then((response) => response.json())
      .then((data) => {
        const plotData = JSON.parse(data.plot); // Parse the JSON string
        setDecisionPlotData(plotData);
        setLoading(false);
      })
      .catch((error) => {
        console.error('Error fetching decision space graph:', error);
        setLoading(false);
      });
  }, []);

  if (loading && !decisionPlotData) {
    return <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '50vh' }}>Loading...</Box>;
  }

  return (
    <Box sx={{ flexGrow: 1 }}>
      {decisionPlotData && (
          <Plot
            data={decisionPlotData.data}
            layout={{
              ...decisionPlotData.layout,
              width: window.innerWidth * 0.34,
              height: window.innerWidth * 0.30,
              autosize: true,
            }}
            config={decisionPlotData.config}
          />
        )
      }
    </Box>
  );
};

export default DecisionPlot;