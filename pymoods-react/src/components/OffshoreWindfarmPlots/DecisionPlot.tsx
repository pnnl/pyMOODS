import React, { useState, useEffect } from 'react';
import Plotly from "plotly.js-basic-dist";
import createPlotlyComponent from "react-plotly.js/factory";
import { Box } from '@mui/material';

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
  weights?: Record<string, number>;
  clusterBy?: string;
}

const DecisionPlot: React.FC<DecisionPlotProps> = ({ useCase, filters, weights = {}, clusterBy }) => {
  const [decisionPlotData, setDecisionPlotData] = useState<DecisionPlotData | null>(null);
  const [loadingPlot, setLoadingPlot] = useState<boolean>(true);

  // Fetch decision space graph data
  useEffect(() => {
    if (!useCase || !filters) return;

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
        setLoadingPlot(false);
      })
      .catch((error) => {
        console.error('Error fetching decision space graph:', error);
        setLoadingPlot(false);
      });
  }, [useCase, filters]);

  return (
    <Box sx={{ flexGrow: 1 }}>
      {/* Plot */}
      {!loadingPlot && decisionPlotData && (
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