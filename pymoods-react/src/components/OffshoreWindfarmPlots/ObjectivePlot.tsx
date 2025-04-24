import { useState, useEffect } from 'react';
import Plotly from "plotly.js-basic-dist";
import createPlotlyComponent from "react-plotly.js/factory";
import Box from '@mui/material/Box';
import { Typography } from '@mui/material';

// const Plot = createPlotlyComponent(Plotly);

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

const ObjectivePlot = () => {
  const [objectiveData, setObjectiveData] = useState<ObjectivePlotData | null>(null);
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
    fetch('http://localhost:8080/api/parameters')
      .then((response) => response.json())
      .then((data) => {
        setParamOptions(data);
      })
      .catch((error) => console.error('Error fetching parameters:', error));
  }, []);

  useEffect(() => {
    setLoading(true);
    
    // Build query string for selected parameters
    const queryParams = new URLSearchParams();
    
    selectedParams.location.forEach(loc => queryParams.append('location', loc));
    selectedParams.technology.forEach(tech => queryParams.append('technology', tech));
    selectedParams.duration.forEach(dur => queryParams.append('duration', dur));
    selectedParams.power.forEach(pow => queryParams.append('power', pow));
    
    const queryString = queryParams.toString();
    const url = `http://localhost:8080/api/objective${queryString ? '?' + queryString : ''}`;
    
    fetch(url)
      .then((response) => response.json())
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
  }, [selectedParams]);

  if (loading && !objectiveData) {
    return <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '50vh' }}>Loading...</Box>;
  }

  return (
    <Box display="flex" flexDirection="column" alignItems="center">
      <Box sx={{ 
        display: 'flex', 
        justifyContent: 'center', 
        alignItems: 'center'
      }}>
        <Typography>
          Mean: {objectiveData?.mean}
          <br />
          Standard Deviation: {objectiveData?.std}
        </Typography>
      </Box>
    </Box>
  );
};

export default ObjectivePlot;