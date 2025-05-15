import { styled } from '@mui/material/styles';
import MuiDrawer, { drawerClasses } from '@mui/material/Drawer';
import Box from '@mui/material/Box';
import {
  Typography,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Chip,
  OutlinedInput,
  SelectChangeEvent,
  CircularProgress,
} from '@mui/material';
import { useState, useEffect } from 'react';
import React from 'react';

// const apiBaseUrl = 'http://moods-dev.pnl.gov:8080';
const apiBaseUrl = 'http://127.0.0.1:8080'; // Use this if running locally

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

interface SideMenuProps {
  onFiltersChange?: (filters: Record<string, string[]>) => void;
}

export default function SideMenu({ onFiltersChange }: SideMenuProps) {
  const [caseStudies, setCaseStudies] = useState<string[]>([]);
  const [selectedCaseStudy, setSelectedCaseStudy] = useState<string>('');
  const [filterOptions, setFilterOptions] = useState<Record<string, string[]>>({});
  const [selectedFilters, setSelectedFilters] = useState<Record<string, string[]>>({});
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  // Load list of case studies
  useEffect(() => {
    fetch(`${apiBaseUrl}/api/case-studies`)
      .then(res => res.json())
      .then(data => {
        setCaseStudies(data.files || []);
      })
      .catch(err => {
        console.error('Error fetching case studies:', err);
        setError('Failed to load case studies.');
      });
  }, []);

  // Load parameters when case study changes
  useEffect(() => {
    if (!selectedCaseStudy) return;

    setLoading(true);
    setError(null);

    fetch(`${apiBaseUrl}/api/files/${selectedCaseStudy}`)
      .then(res => res.json())
      .then(data => {
        // Extract all array fields as filters
        const dynamicFilters: Record<string, string[]> = {};
        Object.keys(data).forEach(key => {
          if (Array.isArray(data[key])) {
            dynamicFilters[key] = data[key];
          }
        });

        setFilterOptions(dynamicFilters);
        setLoading(false);
      })
      .catch(err => {
        console.error('Error loading file:', err);
        setError('Failed to load data for selected case study.');
        setLoading(false);
      });
  }, [selectedCaseStudy]);

  const handleFilterChange = (filterKey: string, newValue: string | string[]) => {
    const valueArray = typeof newValue === 'string' ? newValue.split(',') : newValue;

    const newFilters = {
      ...selectedFilters,
      [filterKey]: valueArray,
    };

    setSelectedFilters(newFilters);

    if (onFiltersChange) {
      onFiltersChange(newFilters);
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
        <Box sx={{ p: 2 }}>
          <Typography variant="body1" sx={{ color: 'white', textAlign: 'left', fontSize: '16px' }}>
            Use Cases
          </Typography>
          <FormControl fullWidth sx={{ mt: 1 }} size="small">
            <SidebarInputLabel sx={{ fontSize: '12px' }}>Select Use Case</SidebarInputLabel>
            <SidebarSelect
              value={selectedCaseStudy}
              onChange={(e) => setSelectedCaseStudy(e.target.value as string)}
              displayEmpty
              disabled={loading}
            >
              <MenuItem value="" disabled>
                Select a file
              </MenuItem>
              {caseStudies.map((fileName) => (
                <MenuItem key={fileName} value={fileName}>
                  {fileName}
                </MenuItem>
              ))}
            </SidebarSelect>
          </FormControl>
          {loading && <CircularProgress size={20} sx={{ mt: 1, color: 'white' }} />}
          {error && <Typography color="error" sx={{ mt: 1 }}>{error}</Typography>}
        </Box>

        <Box sx={{ p: 2 }}>
          <Typography variant="body1" sx={{ color: 'white', textAlign: 'left', fontSize: '16px' }}>
            Filters
          </Typography>

          {/* Render filters dynamically */}
          {Object.keys(filterOptions).map((key) => (
            <React.Fragment key={key}>
              <FormControl fullWidth sx={{ mt: 2 }} size="small">
                <SidebarInputLabel sx={{ fontSize: '12px' }}>{key}</SidebarInputLabel>
                <SidebarSelect
                  multiple
                  value={selectedFilters[key] || []}
                  onChange={(e) => handleFilterChange(key, e.target.value)}
                  input={<OutlinedInput label={key} />}
                  renderValue={() => null}
                  disabled={!selectedCaseStudy || loading}
                >
                  {filterOptions[key].map((value) => (
                    <MenuItem key={value} value={value}>
                      {value}
                    </MenuItem>
                  ))}
                </SidebarSelect>
              </FormControl>
              <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5, mt: 1 }}>
                {(selectedFilters[key] || []).map((value) => (
                  <Chip key={value} label={value} size="small" sx={{ color: 'black', backgroundColor: 'white' }} />
                ))}
              </Box>
            </React.Fragment>
          ))}
        </Box>

        <Box sx={{ p: 2 }}>
          <Typography variant="body1" sx={{ color: 'white', textAlign: 'left', fontSize: '16px' }}>
            Summary
          </Typography>
          {/* Optional: Add summary logic based on selected filters */}
        </Box>
      </Box>
    </Drawer>
  );
}