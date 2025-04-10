import { useState, useEffect } from 'react';
import Plotly from "plotly.js-basic-dist";
import createPlotlyComponent from "react-plotly.js/factory";
import { Box } from '@mui/material';

const Plot = createPlotlyComponent(Plotly);

interface ParameterOptions {
  location: string[];
  technology: string[];
  duration: string[];
  power: string[];
}

interface DecisionPlotData {
  data: Plotly.Data[];
  layout: Partial<Plotly.Layout>;
  config?: Partial<Plotly.Config>;
}

const DecisionPlot = () => {
  const [decisionPlotData, setDecisionPlotData] = useState<DecisionPlotData | null>(null);
  const [paramOptions, setParamOptions] = useState<ParameterOptions>({
    location: [],
    technology: [],
    duration: [],
    power: []
  });
  const [selectedParams, setSelectedParams] = useState<{
    location: string[];
    technology: string[];
    duration: string[];
    power: string[];
  }>({
    location: [],
    technology: [],
    duration: [],
    power: []
  });
  const [loading, setLoading] = useState<boolean>(true);

  // Fetch available parameter options
  useEffect(() => {
    fetch('http://localhost:80/api/parameters')
      .then((response) => response.json())
      .then((data) => {
        setParamOptions(data);
      })
      .catch((error) => console.error('Error fetching parameters:', error));
  }, []);

  // Fetch scatterplot data with selected filters
  useEffect(() => {
    setLoading(true);
    
    // Build query string for selected parameters
    const queryParams = new URLSearchParams();
    
    selectedParams.location.forEach(loc => queryParams.append('location', loc));
    selectedParams.technology.forEach(tech => queryParams.append('technology', tech));
    selectedParams.duration.forEach(dur => queryParams.append('duration', dur));
    selectedParams.power.forEach(pow => queryParams.append('power', pow));
    
    const queryString = queryParams.toString();
    const url = `http://localhost:80/api/decision${queryString ? '?' + queryString : ''}`;
    
    fetch(url)
      .then((response) => response.json())
      .then((data) => {
        const plotData = JSON.parse(data.scatterplot); // Parse the JSON string
        setDecisionPlotData(plotData);
        setLoading(false);
      })
      .catch((error) => {
        console.error('Error fetching decision plot:', error);
        setLoading(false);
      });
  }, [selectedParams]);

  // Handle location change from SideMenu
  const handleLocationChange = (locations: string[]) => {
    setSelectedParams({
      ...selectedParams,
      location: locations,
    });
  };

  // Handle technology change from SideMenu
  const handleTechnologyChange = (technologies: string[]) => {
    setSelectedParams({
      ...selectedParams,
      technology: technologies,
    });
  };

  // Handle duration change from SideMenu
  const handleDurationChange = (durations: string[]) => {
    setSelectedParams({
      ...selectedParams,
      duration: durations,
    });
  };

  // dummy data
  const sizeData = [
    10, 20, 22, 25, 30, 30, 35, 38, 40, 42, 45, 48, 50, 52, 55, 58, 60, 62, 65, 68, 70, 72, 75, 78, 80, 85, 90, 92, 95
  ];

  const cableData = [
    1400, 1450, 1500, 1500, 1550, 1600, 1650, 1700, 1750, 1800, 1850, 1900, 2000,
    2100, 2200, 2300, 2400, 2500, 2600, 2700, 2750, 2780
  ];

  return (
    <Box sx={{ flexGrow: 1 }}>
      <Plot
        data={[
          {
            type: 'histogram',
            x: sizeData,
            xaxis: 'x1',
            yaxis: 'y1',
            marker: { color: 'skyblue' },
            name: 'Size',
          },
          {
            type: 'histogram',
            x: cableData,
            xaxis: 'x2',
            yaxis: 'y2',
            marker: { color: 'salmon' },
            name: 'Cable',
          },
        ]}
        layout={{
          grid: { rows: 2, columns: 1, pattern: 'independent' },
          height: 600,
          width: 800,
          title: 'Stacked Histograms: Size & Cable',
          xaxis: {
            anchor: 'y',
            title: 'Size',
            dtick: 20,
          },
          yaxis: {
            title: 'Frequency',
            dtick: 5,
            range: [0, 25],
          },
          xaxis2: {
            anchor: 'y2',
            title: 'Cable',
            dtick: 200,
          },
          yaxis2: {
            title: 'Frequency',
            tickmode: 'linear',
            dtick: 10,
            range: [0, 40],
          },
        }}
      />
    </Box>
  );
};

export default DecisionPlot;