import { styled } from '@mui/material/styles';
import MuiDrawer, { drawerClasses } from '@mui/material/Drawer';
import Box from '@mui/material/Box';
import { Typography, Select, MenuItem, FormControl, InputLabel, Chip, OutlinedInput, SelectChangeEvent } from '@mui/material';
import { useState, useEffect} from 'react';

const drawerWidth = 200;

const Drawer = styled(MuiDrawer)({
  width: drawerWidth,
  flexShrink: 0,
  boxSizing: 'border-box',
  mt: 10,
  [`& .${drawerClasses.paper}`]: {
    width: drawerWidth,
    boxSizing: 'border-box',
  },
});

const SidebarSelect = styled(Select)({
  color: 'black',
  backgroundColor: 'white',
  height: '32px',
  '.MuiOutlinedInput-input': {
    padding: '6px 14px',
  },
  '.MuiOutlinedInput-notchedOutline': {
    borderColor: '#f7f7f7',
  },
  '&:hover .MuiOutlinedInput-notchedOutline': {
    borderColor: '#ccc',
  },
  '&.Mui-focused .MuiOutlinedInput-notchedOutline': {
    borderColor: 'white',
  },
  '& .MuiSvgIcon-root': {
    color: '#616265',
  }
});

const SidebarInputLabel = styled(InputLabel)({
  color: 'white',
  position: 'relative',
  fontSize: '14px',
  top: 'unset',
  left: 'unset',
  transform: 'none',
  marginBottom: '4px',
  textAlign: 'left',
  whiteSpace: 'normal',
  overflowWrap: 'break-word',
  '&.Mui-focused': {
    color: 'white',
  }
});

interface ParameterOptions {
  location: string[];
  technology: string[];
  duration: string[];
  power: string[];
}

interface SideMenuProps {
  onLocationChange?: (locations: string[]) => void;
  selectedLocations?: string[];
  onTechnologyChange?: (technologies: string[]) => void;
  selectedTechnologies?: string[];
  onDurationChange?: (durations: string[]) => void;
  selectedDurations?: string[];
  onPowerChange?: (powers: string[]) => void;
  selectedPowers?: string[];
}

export default function SideMenu({ 
  onLocationChange, 
  selectedLocations = [],
  onTechnologyChange,
  selectedTechnologies = [],
  onDurationChange,
  selectedDurations = [],
  onPowerChange,
  selectedPowers = []
}: SideMenuProps) {
  const [paramOptions, setParamOptions] = useState<ParameterOptions>({
    location: [],
    technology: [],
    duration: [],
    power: []
  });

  // Fetch available parameter options
  useEffect(() => {
    fetch('http://localhost:80/api/parameters')
      .then((response) => response.json())
      .then((data) => {
        setParamOptions(data);
      })
      .catch((error) => console.error('Error fetching parameters:', error));
  }, []);

  const handleLocationChange = (event: SelectChangeEvent<unknown>) => {
      const value = event.target.value as string | string[];
      const locations = typeof value === 'string' ? value.split(',') : value;
      if (onLocationChange) {
        onLocationChange(locations);
      }
    };

  const handleTechnologyChange = (event: SelectChangeEvent<unknown>) => {
      const value = event.target.value as string | string[];
      const technologies = typeof value === 'string' ? value.split(',') : value;
      if (onTechnologyChange) {
        onTechnologyChange(technologies);
      }
    };

  const handleDurationChange = (event: SelectChangeEvent<unknown>) => {
    const value = event.target.value as string | string[];
    const durations = typeof value === 'string' ? value.split(',') : value;
    if (onDurationChange) {
      onDurationChange(durations);
    }
  };

  const handlePowerChange = (event: SelectChangeEvent<unknown>) => {
    const value = event.target.value as string | string[];
    const powers = typeof value === 'string' ? value.split(',') : value;
    if (onPowerChange) {
      onPowerChange(powers);
    }
  };

  return (
    <Drawer
      variant="permanent"
      sx={{
      display: { xs: 'none', md: 'block' },
      [`& .${drawerClasses.paper}`]: {
        backgroundColor: '#1B293B',
      },
      }}
    >
      <Box
        sx={{
          overflow: 'auto',
          height: '100%',
          display: 'flex',
          flexDirection: 'column',
        }}
      >
        {/* <Button variant="contained">Upload Data</Button> */}
        <Box sx={{ p: 2 }}>
            <Typography variant="body1" sx={{ color: 'white', textAlign: 'left', fontSize: '16px' }}>
            Use Cases
            </Typography>
          <FormControl fullWidth sx={{ mt: 1, minWidth: 120 }} size="small">
            <SidebarInputLabel sx={{ fontSize: '12px' }}>
              Select Use Case
            </SidebarInputLabel>
            <SidebarSelect>
              <MenuItem value={10}>Use Case 1</MenuItem>
              <MenuItem value={20}>Use Case 2</MenuItem>
              <MenuItem value={30}>Use Case 3</MenuItem>
            </SidebarSelect >
          </FormControl>
        </Box>

        <Box sx={{ p: 2 }}>
          <Typography variant="body1" sx={{ color: 'white', textAlign: 'left', fontSize: '16px' }}>
            Filters
          </Typography>
          {/* Location Filter (moved from OffshoreWindfarmClusterScatterPlot) */}
          <FormControl fullWidth sx={{ mt: 1, minWidth: 120 }} size="small">
            <SidebarInputLabel sx={{ color: 'white', fontSize: '12px' }}>Location</SidebarInputLabel>
            <SidebarSelect
              multiple
              value={selectedLocations}
              onChange={handleLocationChange}
              input={<OutlinedInput label="Location" />}
              renderValue={(selected) => (
                <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                  {(selected as string[]).map((value: string) => (
                    <Chip key={value} label={value} size="small" sx={{ color: 'black', backgroundColor: 'white' }} />
                  ))}
                </Box>
              )}
            >
              {paramOptions.location.map((name) => (
                <MenuItem key={name} value={name}>
                  {name}
                </MenuItem>
              ))}
            </SidebarSelect>
          </FormControl>
          
          <FormControl fullWidth sx={{ mt: 2, minWidth: 120 }} size="small">
            <SidebarInputLabel sx={{ color: 'white', fontSize: '12px' }}>Battery Technology</SidebarInputLabel>
            <SidebarSelect
              multiple
              value={selectedTechnologies}
              onChange={handleTechnologyChange}
              input={<OutlinedInput label="Technology" />}
              renderValue={(selected) => (
                <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                  {(selected as string[]).map((value: string) => (
                    <Chip key={value} label={value} size="small" sx={{ color: 'black', backgroundColor: 'white' }} />
                  ))}
                </Box>
              )}
            >
              {paramOptions.technology.map((name) => (
                <MenuItem key={name} value={name}>
                  {name}
                </MenuItem>
              ))}
            </SidebarSelect>
          </FormControl>

          <FormControl fullWidth sx={{ mt: 2, minWidth: 120 }} size="small">
            <SidebarInputLabel sx={{ color: 'white', fontSize: '12px' }}>Battery Power Rating (MW)</SidebarInputLabel>
            <SidebarSelect
              multiple
              value={selectedPowers}
              onChange={handlePowerChange}
              input={<OutlinedInput label="Power" />}
              renderValue={(selected) => (
                <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                  {(selected as string[]).map((value: string) => (
                    <Chip key={value} label={value} size="small" sx={{ color: 'black', backgroundColor: 'white' }} />
                  ))}
                </Box>
              )}
            >
              {paramOptions.power.map((name) => (
                <MenuItem key={name} value={name}>
                  {name}
                </MenuItem>
              ))}
            </SidebarSelect>
          </FormControl>
          <FormControl fullWidth sx={{ mt: 2, minWidth: 120 }} size="small">
            <SidebarInputLabel sx={{ color: 'white', fontSize: '12px' }}>Battery Duration (Hours)</SidebarInputLabel>
            <SidebarSelect
              multiple
              value={selectedDurations}
              onChange={handleDurationChange}
              input={<OutlinedInput label="Duration" />}
              renderValue={(selected) => (
                <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                  {(selected as string[]).map((value: string) => (
                    <Chip key={value} label={value} size="small" sx={{ color: 'black', backgroundColor: 'white' }} />
                  ))}
                </Box>
              )}
            >
              {paramOptions.duration.map((name) => (
                <MenuItem key={name} value={name}>
                  {name}
                </MenuItem>
              ))}
            </SidebarSelect>
          </FormControl>
        </Box>

        <Box sx={{ p: 2 }}>
          <Typography variant="body1" sx={{ color: 'white', textAlign: 'left', fontSize: '16px' }}>
            Summary
          </Typography>
          {/* Add summary content here */}
        </Box>
      </Box>
    </Drawer>
  );
}