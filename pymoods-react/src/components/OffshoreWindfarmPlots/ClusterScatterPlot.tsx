import { useEffect, useState } from 'react';
import * as Plotly from "plotly.js-basic-dist";
import createPlotlyComponent from "react-plotly.js/factory";
import { Box } from '@mui/material';
import SideMenu from '../SideMenu';

const Plot = createPlotlyComponent(Plotly);

interface ParameterOptions {
  location: string[];
  technology: string[];
  duration: string[];
  power: string[];
}

const OffshoreWindfarmClusterScatterPlot = () => {
  interface ScatterplotData {
    data: Plotly.Data[];
    layout: Partial<Plotly.Layout>;
    config?: Partial<Plotly.Config>;
  }

  const [scatterplotData, setScatterplotData] = useState<ScatterplotData | null>(null);
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
    const url = `http://localhost:80/api/scatterplot${queryString ? '?' + queryString : ''}`;
    
    fetch(url)
      .then((response) => response.json())
      .then((data) => {
        const plotData = JSON.parse(data.scatterplot); // Parse the JSON string
        setScatterplotData(plotData);
        setLoading(false);
      })
      .catch((error) => {
        console.error('Error fetching scatterplot:', error);
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

  if (loading && !scatterplotData) {
    return <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '50vh' }}>Loading...</Box>;
  }

  return (
    <Box sx={{ width: '100%' }}>
      <Box sx={{ mb: 2, display: 'flex', flexWrap: 'wrap', gap: 2 }}>
        {/* Duration Filter has been moved to SideMenu */}
        {/* Power Filter has been moved to SideMenu */}
      </Box>
      <SideMenu 
        onLocationChange={handleLocationChange} 
        selectedLocations={selectedParams.location}
        onTechnologyChange={handleTechnologyChange}
        selectedTechnologies={selectedParams.technology}
        onDurationChange={handleDurationChange}
        selectedDurations={selectedParams.duration}
        onPowerChange={(powers: string[]) => {
          setSelectedParams({
            ...selectedParams,
            power: powers,
          });
        }}
        selectedPowers={selectedParams.power}
      />

      <Box sx={{ flexGrow: 1 }}>
        {scatterplotData && (
          <Plot
            data={scatterplotData.data}
            layout={{
              ...scatterplotData.layout,
              width: window.innerWidth * 0.40,
              height: window.innerWidth * 0.20,
              autosize: true,
            }}
            config={scatterplotData.config}
            style={{ width: '100%' }}
          />
        )}
      </Box>
    </Box>
  );
};

export default OffshoreWindfarmClusterScatterPlot;