import { useState, useEffect } from 'react';
import Plotly from "plotly.js-basic-dist";
import createPlotlyComponent from "react-plotly.js/factory";
import Box from '@mui/material/Box';

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
    fetch('http://localhost:80/api/YOUR_EDNPOINT_HERE')
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

  return (
    <Box sx={{ flexGrow: 1 }}>
      {loading ? (
        <div>Loading...</div>
      ) : (
        plotData && (
          <Plot
            data={plotData.data}
            layout={plotData.layout}
            config={plotData.config}
          />
        )
      )}
    </Box>
  );
};

export default NewPlotTemplate;