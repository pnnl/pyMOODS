import { useState, useEffect } from 'react';
import Plotly from "plotly.js-basic-dist";
import createPlotlyComponent from "react-plotly.js/factory";
import Box from '@mui/material/Box';
import { Typography } from '@mui/material';

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
    fetch('http://localhost:80/api/parameters')
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

  const plotData = (): Partial<Plotly.Data>[] => {
    if (!objectiveData) return [];

    console.log("Objective Data:", objectiveData.mean, objectiveData.std);
    
    return [{
      type: 'indicator',
      mode: 'number',
      value: objectiveData.mean,
      title: {
        text: `Standard Deviation: ${objectiveData.std.toFixed(2)} & <br> Mean:`,
        font: { size: 15 }
      },
      number: {
        font: { size: 50 },
        valueformat: '.2f'
      },
      domain: { x: [0, 1], y: [0, 1] }
    }];
  };

  return (
    <Box display="flex" flexDirection="column" alignItems="center">
      <Box sx={{ 
        display: 'flex', 
        justifyContent: 'center', 
        alignItems: 'center'
      }}>
        {/* {loading ? (
          <div>Loading objective data...</div>
        ) : !objectiveData ? (
          <div>No objective data available</div>
        ) : (
          <Plot
          data={[
            {
              type: 'indicator',
              mode: 'number',
              value: 42,
              title: {
                text: `Standard Deviation: 5.00 & <br> Mean:`,
                font: { size: 15 }
              },
              number: {
                font: { size: 50 },
                valueformat: '.2f'
              },
              domain: { x: [0, 1], y: [0, 1] }
            }
          ]}
          layout={{
            width: width,
            height: height,
            paper_bgcolor: 'rgba(0,0,0,0)',
            plot_bgcolor: 'rgba(0,0,0,0)',
            font: {
              family: 'Helvetica',
              color: 'black',
              size: 10
            },
            margin: { t: 0, b: 0, l: 0, r: 0 }
          }}
          config={{ responsive: true }}
          />
        )} */}
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