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
import TextField from '@mui/material/TextField';
import Stack from "@mui/material/Stack";
import pyMOODSLogo from "../assets/pymoods-logo-updated.svg";
import config from '../config';
const { API_BASE_URL } = config;

const drawerWidth = 250;

const Drawer = styled(MuiDrawer)({
  width: drawerWidth,
  flexShrink: 0,
  boxSizing: 'border-box',
  [`& .${drawerClasses.paper}`]: {
    width: drawerWidth,
    boxSizing: 'border-box',
    backgroundColor: '#1B293B',
    color: 'white',
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
  fontFamily:'Inter, system-ui, Avenir, Helvetica, Arial, sans-serif',
  top: 'unset',
  left: 'unset',
  transform: 'none',
  marginBottom: '4px',
  textAlign: 'left',
  whiteSpace: 'normal',
  wordWrap: 'break-word',
  overflowWrap: 'anywhere',
  '&.Mui-focused': {
    color: 'white',
  }
});

interface FilterOption {
  key: string;
  name: string;
  values: string[];
}

interface ObjectiveWeight {
  name: string;
  weight: number;
}

interface SideMenuProps {
  onFiltersChange?: (filters: Record<string, string[]>) => void;
  onSelectUseCase?: (useCase: string) => void;
  onWeightsChange?: (weights: Record<string, number>) => void;
}

const SideMenu: React.FC<SideMenuProps> = ({ onFiltersChange, onSelectUseCase, onWeightsChange }) => {
  const [caseStudies, setCaseStudies] = useState<string[]>([]);
  const [selectedCaseStudy, setSelectedCaseStudy] = useState<string>('');
  const [filterOptions, setFilterOptions] = useState<FilterOption[]>([]);
  const [selectedFilters, setSelectedFilters] = useState<Record<string, string[]>>({});
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  // State for objective weights
  const [objectiveWeights, setObjectiveWeights] = useState<ObjectiveWeight[]>([]);

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

        // Set default use case
        let defaultUseCase = '';
        if (files.includes('MoCoDo_v3')) {
          defaultUseCase = 'MoCoDo_v3';
        } else if (files.length > 0) {
          defaultUseCase = files[0];
        }

        setSelectedCaseStudy(defaultUseCase);
        if (onSelectUseCase && defaultUseCase) {
          onSelectUseCase(defaultUseCase);
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

  // Unified call to fetch parameters and weights
  useEffect(() => {
    if (!selectedCaseStudy) return;

    setLoading(true);
    setError(null);

    fetch(`${API_BASE_URL}/api/init?use_case=${encodeURIComponent(selectedCaseStudy)}`)
      .then(res => {
        if (!res.ok) throw new Error('Failed to initialize use case data');
        return res.json();
      })
      .then(data => {
        // Set filter options
        setFilterOptions(data.filters || []);
        const newSelectedFilters = (data.filters || []).reduce((acc: Record<string, string[]>, item: any) => {
          acc[item.key] = [];
          return acc;
        }, {});
        setSelectedFilters(newSelectedFilters);
        if (onFiltersChange) onFiltersChange(newSelectedFilters);

        // Set objective weights
        const weightsData = data.objectives || {};
        const weights = Object.keys(weightsData).map((name) => ({
          name,
          weight: weightsData[name]
        }));
        setObjectiveWeights(weights);
      })
      .catch(err => {
        console.error('Error loading data:', err);
        setError("Failed to load data for selected use case.");
      })
      .finally(() => {
        setLoading(false);
      });
  }, [selectedCaseStudy]);

  // Notify parent whenever weights change
  useEffect(() => {
    if (onWeightsChange && objectiveWeights.length > 0) {
      const weights = objectiveWeights.reduce((acc, obj) => {
        acc[obj.name] = obj.weight;
        return acc;
      }, {} as Record<string, number>);
      onWeightsChange(weights);
    }
  }, [objectiveWeights]);

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

  const handleWeightChange = (index: number, value: string) => {
    const numValue = parseInt(value, 10);
    if (isNaN(numValue) || numValue < 0) return;

    const updated = [...objectiveWeights];
    updated[index].weight = numValue;
    setObjectiveWeights(updated);
  };

  return (
    <Drawer variant="permanent">
      <Box sx={{ overflowY: 'auto', flexGrow: 1 }}>
        {/* Base container with consistent top/bottom padding */}
        <Box sx={{ p: 2 }}>
        <Box sx={{ display: 'flex', justifyContent: 'center', mb: 2 }}>
          <img
            src={pyMOODSLogo}
            alt="pyMOODS Logo"
            style={{ height: "110px", width:"110px", objectFit:"contain",alignItems: "center", backgroundColor:"white"}}
          /></Box>
          {/* Use Case Section */}
          <Box sx={{ mb: 3, mt: 6.2 }}>
            <Typography variant="body1" sx={{ color: 'white', fontWeight: 500}}>
              Use Case
            </Typography>
            <Box sx={{ borderBottom: '1px solid', borderColor: 'white', width: '100%',  mb: 1.5 }} />
            <FormControl fullWidth size="small">
              <SidebarInputLabel>Select Use Case</SidebarInputLabel>
              <SidebarSelect
                value={selectedCaseStudy}
                onChange={(e) => {
                  const newValue = e.target.value as string;
                  setSelectedCaseStudy(newValue);
                  if (onSelectUseCase && newValue) {
                    onSelectUseCase(newValue);
                  }
                }}
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
              <CircularProgress size={20} sx={{ mt: 1.5, color: 'white' }} />
            )}
            {error && <Typography color="error" sx={{ mt: 1.5 }}>{error}</Typography>}
          </Box>

          {/* Filters Section */}
          <Box sx={{ mb: 3 }}>
            <Typography variant="body1" sx={{ color: 'white', fontWeight: 500 }}>
              Filters
            </Typography>
            <Box sx={{ borderBottom: '1px solid', borderColor: 'white', width: '100%',  mb: 1.5 }} />
            {loading && filterOptions.length === 0 ? (
              <Box sx={{ my: 1.5, display: 'flex', justifyContent: 'center' }}>
                <CircularProgress size={20} sx={{ color: 'white' }} />
              </Box>
            ) : (
              filterOptions.map((filter) => (
                <Box key={filter.key} sx={{ mb: 2 }}>
                  <FormControl fullWidth size="small">
                    <SidebarInputLabel>{filter.name}</SidebarInputLabel>
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
                </Box>
              ))
            )}
          </Box>

          {/* Objective Weights Section */}
          <Box sx={{ mb: 3 }}>
            <Typography variant="body1" sx={{ color: 'white', fontWeight: 500}}>
              Objective Weights
            </Typography>
            <Box sx={{ borderBottom: '1px solid', borderColor: 'white', width: '100%',  mb: 1.5 }} />
            {objectiveWeights.length === 0 ? (
              <Typography variant="body2" color="text.secondary">No objectives found.</Typography>
            ) : (
              objectiveWeights.map((obj, index) => (
                <Box
                  key={obj.name}
                  sx={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                    mb: 1.5,
                    gap: 1,
                  }}
                >
                  <Typography
                    variant="body2"
                    color="white"
                    sx={{
                      fontSize: '14px',
                      wordBreak: 'break-word',
                      overflowWrap: 'anywhere',
                      textAlign: 'left',
                      flex: 1,
                    }}
                  >
                    {obj.name}
                  </Typography>
                  <TextField
                    type="number"
                    value={obj.weight}
                    onChange={(e) => handleWeightChange(index, e.target.value)}
                    size="small"
                    inputProps={{
                      min: 0,
                      max: 100,
                      step: 1,
                      style: {
                        textAlign: 'center',
                        padding: '4px',
                        width: '5ch',
                        backgroundColor: 'white',
                        borderRadius: '4px',
                      },
                    }}
                    sx={{
                      '& .MuiOutlinedInput-root': {
                        backgroundColor: 'white',
                        borderRadius: '4px',
                        height: '30px',
                        input: {
                          padding: '6px',
                        },
                      },
                      '& .MuiOutlinedInput-notchedOutline': {
                        borderColor: '#ccc',
                      },
                      '&:hover .MuiOutlinedInput-notchedOutline': {
                        borderColor: '#888',
                      },
                      '&.Mui-focused .MuiOutlinedInput-notchedOutline': {
                        borderColor: '#007FFF',
                      },
                    }}
                  />
                </Box>
              ))
            )}
          </Box>
        </Box>
      </Box>
    </Drawer>
  );
};

export default SideMenu;