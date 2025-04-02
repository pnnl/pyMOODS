import { useState, useEffect } from 'react';
import Plotly from "plotly.js-basic-dist";
import createPlotlyComponent from "react-plotly.js/factory";
import Box from '@mui/material/Box';

const Plot = createPlotlyComponent(Plotly);

interface ObjectiveData {
  mean: number;
  std: number;
  title: string;
}

interface ObjectivePlotProps {
  location?: string[];
  technology?: string[];
  duration?: string[];
  power?: string[];
  width?: number;
  height?: number;
}

const ObjectivePlot: React.FC<ObjectivePlotProps> = ({ 
  location = [], 
  technology = [], 
  duration = [], 
  power = [],
  width = 450,
  height = 325
}) => {
  const [objectiveData, setObjectiveData] = useState<ObjectiveData | null>(null);
  const [loading, setLoading] = useState<boolean>(true);

  useEffect(() => {
    setLoading(true);
    
    // Build query string for selected parameters
    const queryParams = new URLSearchParams();
    
    location.forEach(loc => queryParams.append('location', loc));
    technology.forEach(tech => queryParams.append('technology', tech));
    duration.forEach(dur => queryParams.append('duration', dur));
    power.forEach(pow => queryParams.append('power', pow));
    
    const queryString = queryParams.toString();
    const url = `http://localhost:5000/api/objective${queryString ? '?' + queryString : ''}`;
    
    fetch(url)
      .then((response) => response.json())
      .then((data: ObjectiveData) => {
        setObjectiveData(data);
        setLoading(false);
      })
      .catch((error) => {
        console.error('Error fetching objective data:', error);
        setLoading(false);
      });
  }, [location, technology, duration, power]);

  const plotData = (): Partial<Plotly.Data>[] => {
    if (!objectiveData) return [];
    
    // Ensure we have proper values
    const mean = typeof objectiveData.mean === 'number' ? objectiveData.mean : 0;
    const std = typeof objectiveData.std === 'number' ? objectiveData.std : 0;
    
    return [{
      type: 'indicator',
      mode: 'number',
      value: mean,
      title: {
        text: `Standard Deviation: ${std.toFixed(2)} & <br> Mean:`,
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
        width: width, 
        height: height, 
        display: 'flex', 
        justifyContent: 'center', 
        alignItems: 'center'
      }}>
        {loading ? (
          <div>Loading objective data...</div>
        ) : !objectiveData ? (
          <div>No objective data available</div>
        ) : (
          <Plot
            data={plotData()}
            layout={{
              width: width,
              height: height,
              paper_bgcolor: 'rgba(0,0,0,0)',
              plot_bgcolor: 'rgba(0,0,0,0)',
              margin: { l: 20, r: 40, t: 30, b: 10 },
              font: {
                family: 'Helvetica',
                color: 'black',
                size: 10
              }
            }}
            config={{
              displayModeBar: false,
              responsive: true
            }}
          />
        )}
      </Box>
    </Box>
  );
};

export default ObjectivePlot;