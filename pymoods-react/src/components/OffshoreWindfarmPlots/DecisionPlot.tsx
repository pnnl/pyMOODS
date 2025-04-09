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

  return (
    <Box sx={{ flexGrow: 1 }}>
      {decisionPlotData && (
        <Plot
          data={decisionPlotData.data}
          layout={{
            ...decisionPlotData.layout,
            width: window.innerWidth * 0.40,
            height: window.innerWidth * 0.20,
            autosize: true,
          }}
          config={decisionPlotData.config}
          style={{ width: '100%' }}
        />
      )}
    </Box>
  );
};

export default DecisionPlot;