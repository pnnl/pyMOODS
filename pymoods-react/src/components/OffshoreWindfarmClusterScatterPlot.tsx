import { useEffect, useState } from 'react';
import * as Plotly from "plotly.js-basic-dist";
import createPlotlyComponent from "react-plotly.js/factory";
import { Box, FormControl, InputLabel, Select, MenuItem, Chip, OutlinedInput, SelectChangeEvent } from '@mui/material';
import SideMenu from './SideMenu';

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
    fetch('http://localhost:5000/api/parameters')
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
    const url = `http://localhost:5000/api/scatterplot${queryString ? '?' + queryString : ''}`;
    
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

  // Handle parameter selection changes
  const handleParamChange = (param: keyof ParameterOptions) => (event: SelectChangeEvent<string[]>) => {
    const value = event.target.value;
    setSelectedParams({
      ...selectedParams,
      [param]: typeof value === 'string' ? value.split(',') : value,
    });
  };

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

  if (loading && !scatterplotData) {
    return <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '50vh' }}>Loading...</Box>;
  }

  return (
    <Box sx={{ width: '100%' }}>
      <Box sx={{ mb: 2, display: 'flex', flexWrap: 'wrap', gap: 2 }}>
        {/* Technology Filter has been moved to SideMenu */}

        {/* Duration Filter */}
        <FormControl sx={{ m: 1, width: 200 }} size="small">
          <InputLabel id="duration-label">Duration</InputLabel>
          <Select
            labelId="duration-label"
            id="duration-select"
            multiple
            value={selectedParams.duration}
            onChange={handleParamChange('duration')}
            input={<OutlinedInput label="Duration" />}
            renderValue={(selected) => (
              <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                {selected.map((value) => (
                  <Chip key={value} label={value} size="small" />
                ))}
              </Box>
            )}
          >
            {paramOptions.duration.map((name) => (
              <MenuItem key={name} value={name}>
                {name}
              </MenuItem>
            ))}
          </Select>
        </FormControl>

        {/* Power Filter */}
        <FormControl sx={{ m: 1, width: 200 }} size="small">
          <InputLabel id="power-label">Power</InputLabel>
          <Select
            labelId="power-label"
            id="power-select"
            multiple
            value={selectedParams.power}
            onChange={handleParamChange('power')}
            input={<OutlinedInput label="Power" />}
            renderValue={(selected) => (
              <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                {selected.map((value) => (
                  <Chip key={value} label={value} size="small" />
                ))}
              </Box>
            )}
          >
            {paramOptions.power.map((name) => (
              <MenuItem key={name} value={name}>
                {name}
              </MenuItem>
            ))}
          </Select>
        </FormControl>
      </Box>

      {/* Render SideMenu with location and technology filters */}
      <SideMenu 
        onLocationChange={handleLocationChange} 
        selectedLocations={selectedParams.location}
        onTechnologyChange={handleTechnologyChange}
        selectedTechnologies={selectedParams.technology}
      />

      {scatterplotData && (
        <Plot
          data={scatterplotData.data}
          layout={scatterplotData.layout}
          config={scatterplotData.config}
          style={{ width: '100%', height: '500px' }}
        />
      )}
    </Box>
  );
};

export default OffshoreWindfarmClusterScatterPlot;