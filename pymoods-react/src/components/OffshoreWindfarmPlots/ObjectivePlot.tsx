import { useState, useEffect } from 'react';
import Plotly from "plotly.js-basic-dist";
import createPlotlyComponent from "react-plotly.js/factory";
import Box from '@mui/material/Box';
import { Typography } from '@mui/material';

// Import centralized config
import config from '../../config';
const { API_BASE_URL } = config;

const Plot = createPlotlyComponent(Plotly);

interface ParameterOptions {
  location: string[];
  technology: string[];
  duration: string[];
  power: string[];
}

interface ObjectivePlotData {
  data: Plotly.Data[];
  layout: Partial<Plotly.Layout>;
  config?: Partial<Plotly.Config>;
  mean: number;
  std: number;
  title: string;
}

interface ObjectivePlotProps {
  useCase: string;
  filters: Record<string, string[]>;
}

const ObjectivePlot: React.FC<ObjectivePlotProps> = ({ useCase, filters }) => {
  const [objectiveData, setObjectiveData] = useState<ObjectivePlotData | null>(null);
  const [paramOptions, setParamOptions] = useState<ParameterOptions>({
    location: [],
    technology: [],
    duration: [],
    power: []
  });
  const [loading, setLoading] = useState<boolean>(true);

  // Fetch parameter options dynamically for the selected use case
  useEffect(() => {
    if (!useCase) return;

    fetch(`${API_BASE_URL}/api/parameters?use_case=${useCase}`)
      .then((response) => {
        if (!response.ok) throw new Error("Failed to fetch parameters");
        return response.json();
      })
      .then((data) => {
        setParamOptions(data);
      })
      .catch((error) => {
        console.error('Error fetching parameter options:', error);
      });
  }, [useCase]);

  // Fetch objective data based on selected filters and use case
  useEffect(() => {
    if (!useCase || !filters) return;

    setLoading(true);

    const queryParams = new URLSearchParams();

    Object.entries(filters).forEach(([key, values]) => {
      if (Array.isArray(values)) {
        values.forEach(value => queryParams.append(key, value));
      }
    });

    const url = `${API_BASE_URL}/api/objective?${queryParams.toString()}&use_case=${useCase}`;

    fetch(url)
      .then((response) => {
        if (!response.ok) throw new Error("Failed to fetch objective data");
        return response.json();
      })
      .then((data) => {
        setObjectiveData({
          data: [],
          layout: {},
          config: data.config,
          mean: data.mean,
          std: data.std,
          title: ''
        });
        setLoading(false);
      })
      .catch((error) => {
        console.error('Error fetching objective data:', error);
        setLoading(false);
      });

  }, [useCase, filters]);

  if (loading && !objectiveData) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '50vh' }}>
        <Typography variant="body1">Loading...</Typography>
      </Box>
    );
  }

  return (
    <Box display="flex" flexDirection="column" sx={{ p: 2 }}>
      <Box sx={{ textAlign: 'center' }}>
        <Typography variant="subtitle1">Objective Metrics</Typography>
        <Box sx={{ mt: 2 }}>
          <Typography variant="body2">
            <strong>Mean:</strong> {objectiveData?.mean.toFixed(2)}
          </Typography>
          <br />
          <Typography variant="body2">
            <strong>Standard Deviation:</strong> {objectiveData?.std.toFixed(2)}
          </Typography>
        </Box>
      </Box>
    </Box>
  );
};

export default ObjectivePlot;