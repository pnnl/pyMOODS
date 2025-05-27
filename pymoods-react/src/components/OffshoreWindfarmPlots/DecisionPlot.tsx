import { useState, useEffect } from 'react';
import Plotly from "plotly.js-basic-dist";
import createPlotlyComponent from "react-plotly.js/factory";
import { Box, Typography } from '@mui/material';

// Import centralized config
import config from '../../config';
const { API_BASE_URL } = config;

const Plot = createPlotlyComponent(Plotly);

interface DecisionPlotData {
  data: Plotly.Data[];
  layout: Partial<Plotly.Layout>;
  config?: Partial<Plotly.Config>;
}

interface DecisionPlotProps {
  useCase: string;
  filters: Record<string, string[]>;
}

const DecisionPlot: React.FC<DecisionPlotProps> = ({ useCase, filters }) => {
  const [decisionPlotData, setDecisionPlotData] = useState<DecisionPlotData | null>(null);
  const [loading, setLoading] = useState<boolean>(true);

  // Fetch decision space graph data from the API
  useEffect(() => {
    if (!useCase || !filters) return;

    setLoading(true);

    const queryParams = new URLSearchParams();

    Object.entries(filters).forEach(([key, values]) => {
      if (Array.isArray(values)) {
        values.forEach(value => queryParams.append(key, value));
      }
    });

    const url = `${API_BASE_URL}/api/decision?${queryParams.toString()}&use_case=${useCase}`;

    fetch(url)
      .then((response) => {
        if (!response.ok) throw new Error("Failed to fetch decision plot data");
        return response.json();
      })
      .then((data) => {
        const plotData = JSON.parse(data.plot); // Parse the JSON string
        setDecisionPlotData(plotData);
        setLoading(false);
      })
      .catch((error) => {
        console.error('Error fetching decision space graph:', error);
        setLoading(false);
      });
  }, [useCase, filters]);

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '50vh' }}>
        <Typography variant="body1">Loading Decision Plot...</Typography>
      </Box>
    );
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
      )}
    </Box>
  );
};

export default DecisionPlot;