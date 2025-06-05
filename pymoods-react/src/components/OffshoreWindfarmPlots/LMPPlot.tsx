import { useState, useEffect } from 'react';
import * as Plotly from "plotly.js-basic-dist";
import createPlotlyComponent from "react-plotly.js/factory";
import { Box, Typography } from '@mui/material';

// Import centralized config
import config from '../../config';
const { API_BASE_URL } = config;

const Plot = createPlotlyComponent(Plotly);

interface CsvRow {
  INTERVALSTARTTIME_GMT: string;
  LMP: string;
  [key: string]: any;
}

interface LMPPlotProps {
  useCase: string;
  filters: Record<string, string[]>;
}

const LMPPlot: React.FC<LMPPlotProps> = ({ useCase, filters }) => {
  const [data, setData] = useState<CsvRow[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Fetch filtered LMP data from backend based on useCase and filters
  useEffect(() => {
    if (!useCase) return;

    setLoading(true);
    setError(null);

    const queryParams = new URLSearchParams();

    Object.entries(filters).forEach(([key, values]) => {
      if (Array.isArray(values)) {
        values.forEach(value => queryParams.append(key, value));
      }
    });

    const url = `${API_BASE_URL}/api/lmp?${queryParams.toString()}&use_case=${useCase}`;

    fetch(url)
      .then(res => {
        if (!res.ok) throw new Error("Failed to fetch LMP data");
        return res.json();
      })
      .then(jsonData => {
        const parsedData = jsonData.data.map((row: any) => ({
          ...row,
          INTERVALSTARTTIME_GMT: new Date(row.INTERVALSTARTTIME_GMT)
        }));
        setData(parsedData);
      })
      .catch(err => {
        console.error('Error fetching LMP data:', err);
        setError("Failed to load LMP data.");
      })
      .finally(() => {
        setLoading(false);
      });
  }, [useCase, filters]);

  const plotData = (): Partial<Plotly.Data>[] => {
    if (data.length === 0) return [];

    const hourlyLMP = data.reduce((acc, row) => {
      const hour = row.INTERVALSTARTTIME_GMT.getUTCHours();
      if (!acc[hour]) acc[hour] = [];
      acc[hour].push(parseFloat(row.LMP)); // Ensure numeric values
      return acc;
    }, {} as Record<number, number[]>);

    const hourlyLMPMean = Object.keys(hourlyLMP).map(hourStr => {
      const hour = parseInt(hourStr);
      const values = hourlyLMP[hour];
      const mean = values.reduce((sum, val) => sum + val, 0) / values.length;
      return { hour, LMP: mean };
    });

    const x = hourlyLMPMean.map(d => d.hour);
    const y = hourlyLMPMean.map(d => d.LMP);

    return [
      {
        x,
        y,
        type: 'scatter' as const,
        mode: 'lines',
        marker: { color: 'blue' },
        name: 'Avg. LMP'
      }
    ];
  };

  if (loading && !data.length) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '50vh' }}>
        <Typography variant="body1">Loading LMP Data...</Typography>
      </Box>
    );
  }

  if (error) {
    return (
      <Box sx={{ p: 2, color: 'error.main' }}>
        <Typography>{error}</Typography>
      </Box>
    );
  }

  return (
    <Box display="flex" flexDirection="column" alignItems="center">
      <Plot
        data={plotData()}
        layout={{
          width: window.innerWidth * 0.30,
          height: window.innerWidth * 0.25,
          autosize: true,
          title: { text: 'LMP' },
          xaxis: {
            title: { text: 'Hour', standoff: 10 },
            showgrid: true,
            showline: true,
            zeroline: true,
            linecolor: 'black',
            tickcolor: 'black',
            ticks: 'outside',
            ticklen: 5
          },
          yaxis: {
            title: { text: 'LMP', standoff: 10 },
            showgrid: true,
            showline: true,
            zeroline: true,
            linecolor: 'black',
            tickcolor: 'black',
            ticks: 'outside',
            ticklen: 5
          },
          paper_bgcolor: 'transparent',
          plot_bgcolor: 'transparent'
        }}
      />
    </Box>
  );
};

export default LMPPlot;