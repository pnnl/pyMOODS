import React, { useState, useEffect } from 'react';
import { styled } from '@mui/material/styles';
import MuiDrawer, { drawerClasses } from '@mui/material/Drawer';
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';
import Select from '@mui/material/Select';
import MenuItem from '@mui/material/MenuItem';
import FormControl from '@mui/material/FormControl';
import InputLabel from '@mui/material/InputLabel';
import Chip from '@mui/material/Chip';
import CircularProgress from '@mui/material/CircularProgress';

import config from '../config';
const { API_BASE_URL } = config;

const drawerWidth = 200;

const Drawer = styled(MuiDrawer)({
  width: drawerWidth,
  flexShrink: 0,
  boxSizing: 'border-box',
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

interface FilterOption {
  key: string;
  name: string;
  values: string[];
}

interface SideMenuProps {
  onFiltersChange?: (filters: Record<string, string[]>) => void;
  onSelectUseCase?: (useCase: string) => void;
}

const SideMenu: React.FC<SideMenuProps> = ({ onFiltersChange, onSelectUseCase }) => {
  const [caseStudies, setCaseStudies] = useState<string[]>([]);
  const [selectedCaseStudy, setSelectedCaseStudy] = useState<string>('');
  const [filterOptions, setFilterOptions] = useState<FilterOption[]>([]);
  const [selectedFilters, setSelectedFilters] = useState<Record<string, string[]>>({});
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  // Load list of case studies
  useEffect(() => {
    setLoading(true);
    fetch(`${API_BASE_URL}/api/case-studies`)
      .then(res => {
        if (!res.ok) throw new Error('Failed to fetch case studies');
        return res.json();
      })
      .then(data => {
        const files = data.files || [];
        setCaseStudies(files);

        // Optionally set default use case
        if (files.includes('MoCoDo_v2')) {
          setSelectedCaseStudy('MoCoDo_v2');
        } else if (files.length > 0) {
          setSelectedCaseStudy(files[0]);
        }
      })
      .catch(err => {
        console.error('Error fetching case studies:', err);
        setError("Failed to load case studies.");
      })
      .finally(() => {
        setLoading(false);
      });
  }, []);

  // Load parameters when case study changes
  useEffect(() => {
    if (!selectedCaseStudy) return;

    setLoading(true);
    setError(null);

    fetch(`${API_BASE_URL}/api/parameters?use_case=${encodeURIComponent(selectedCaseStudy)}`)
      .then(res => {
        if (!res.ok) throw new Error('Failed to fetch file data');
        return res.json();
      })
      .then((data: FilterOption[]) => {
        setFilterOptions(data);

        const newSelectedFilters = data.reduce((acc, item) => {
          acc[item.key] = [];
          return acc;
        }, {} as Record<string, string[]>);

        setSelectedFilters(newSelectedFilters);

        if (onFiltersChange) {
          onFiltersChange(newSelectedFilters);
        }

        if (onSelectUseCase) {
          onSelectUseCase(selectedCaseStudy);
        }

        setLoading(false);
      })
      .catch(err => {
        console.error('Error loading file:', err);
        setError("Failed to load data for selected use case.");
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
        {/* Use Cases Section */}
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
          {loading && caseStudies.length === 0 && (
            <CircularProgress size={20} sx={{ mt: 1, color: 'white' }} />
          )}
          {error && <Typography color="error" sx={{ mt: 1 }}>{error}</Typography>}
        </Box>

        {/* Filters Section */}
        <Box sx={{ p: 2 }}>
          <Typography variant="body1" sx={{ color: 'white', textAlign: 'left', fontSize: '16px' }}>
            Filters
          </Typography>

          {/* Render filters dynamically */}
          {loading && filterOptions.length === 0 ? (
            <Box sx={{ mt: 2, display: 'flex', justifyContent: 'center' }}>
              <CircularProgress size={20} sx={{ color: 'white' }} />
            </Box>
          ) : (
            filterOptions.map((filter) => (
              <React.Fragment key={filter.key}>
                <FormControl fullWidth sx={{ mt: 2 }} size="small">
                  <SidebarInputLabel sx={{ fontSize: '12px' }}>{filter.name}</SidebarInputLabel>
                  <SidebarSelect
                    multiple
                    value={selectedFilters[filter.key] || []}
                    onChange={(e) => handleFilterChange(filter.key, e.target.value)}
                    input={<Select native={false} />}
                    renderValue={() => null}
                    disabled={!selectedCaseStudy || loading}
                    MenuProps={{
                      PaperProps: {
                        style: {
                          maxHeight: 200,
                          width: 250,
                        },
                      },
                      anchorOrigin: {
                        vertical: 'bottom',
                        horizontal: 'left',
                      },
                      transformOrigin: {
                        vertical: 'top',
                        horizontal: 'left',
                      },
                      disableAutoFocusItem: true,
                    }}
                  >
                    {filter.values.map((value) => (
                      <MenuItem key={value} value={value}>
                        {value}
                      </MenuItem>
                    ))}
                  </SidebarSelect>
                </FormControl>
                <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5, mt: 1 }}>
                  {(selectedFilters[filter.key] || []).map((value) => (
                    <Chip
                      key={value}
                      label={value}
                      size="small"
                      onDelete={() => {
                        const newValues = selectedFilters[filter.key].filter(v => v !== value);
                        handleFilterChange(filter.key, newValues);
                      }}
                      sx={{ color: 'black', backgroundColor: 'white' }}
                    />
                  ))}
                </Box>
              </React.Fragment>
            ))
          )}
        </Box>

        {/* Summary Section */}
        <Box sx={{ p: 2 }}>
          <Typography variant="body1" sx={{ color: 'white', textAlign: 'left', fontSize: '16px' }}>
            Summary
          </Typography>
          {/* Optional: Add summary logic based on selected filters */}
        </Box>
      </Box>
    </Drawer>
  );
};

export default SideMenu;