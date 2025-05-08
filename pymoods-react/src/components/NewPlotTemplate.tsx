import { useState, useEffect } from 'react';
import Plotly from "plotly.js-basic-dist";
import createPlotlyComponent from "react-plotly.js/factory";
import Box from '@mui/material/Box';

const apiBaseUrl = 'http://moods-dev.pnl.gov/8080';
// const apiBaseUrl = 'http://localhost:8080'; // Uncomment this line if you are running the API locally
const Plot = createPlotlyComponent(Plotly);

interface PlotData {
  data: Plotly.Data[];
  layout: Partial<Plotly.Layout>;
  config?: Partial<Plotly.Config>;
}

const NewPlotTemplate = () => {
  const [plotData, setPlotData] = useState<PlotData | null>(null);
  const [loading, setLoading] = useState<boolean>(true);

  // Fetch decision space graph data from the API
  useEffect(() => {
    setLoading(true);
    fetch(`${apiBaseUrl}/api/YOUR_EDNPOINT_HERE`)
      .then((response) => response.json())
      .then((data) => {
        const plotData = JSON.parse(data.plot); // Parse the JSON string
        setPlotData(plotData);
        setLoading(false);
      })
      .catch((error) => {
        console.error('Error fetching graph:', error);
        setLoading(false);
      });
  }, []);

  if (loading && !plotData) {
    return <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '50vh' }}>Loading...</Box>;
  }

  return (
    <Box sx={{ flexGrow: 1 }}>
      {plotData && (
          <Plot
            data={plotData.data}
            layout={{
              ...plotData.layout,
              width: window.innerWidth * 0.33,
              height: window.innerWidth * 0.25,
              autosize: true,
            }}
            config={plotData.config}
            style={{ width: '100%' }}
          />
        )
      }
    </Box>
  );
};

export default NewPlotTemplate;