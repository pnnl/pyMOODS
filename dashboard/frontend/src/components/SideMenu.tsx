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
import Tooltip from '@mui/material/Tooltip';
import Button from '@mui/material/Button';
import LinearProgress from '@mui/material/LinearProgress';
import InfoOutlinedIcon from '@mui/icons-material/InfoOutlined';
import AutoAwesomeIcon from '@mui/icons-material/AutoAwesome';
import pyMOODSLogo from "../assets/pymoods-logo-updated.svg";
import config from '../config';
import { SIDEBAR_WIDTH } from '../layout';
import { useDashboardStore } from '../store/dashboardStore';
const { API_BASE_URL } = config;

const Drawer = styled(MuiDrawer)({
  width: SIDEBAR_WIDTH,
  flexShrink: 0,
  boxSizing: 'border-box',
  [`& .${drawerClasses.paper}`]: {
    width: SIDEBAR_WIDTH,
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
  filters?: Record<string, string[]>;
  weights?: Record<string, number>; // Agent-applied weight overrides from parent
}

const SideMenu: React.FC<SideMenuProps> = ({ onFiltersChange, onSelectUseCase, onWeightsChange, filters, weights }) => {
  const agentAppliedFilters = useDashboardStore((s) => s.dashboardState.activeFilters);
  const agentAppliedWeights = useDashboardStore((s) => s.dashboardState.agentWeightOverrides);

  const [caseStudies, setCaseStudies] = useState<string[]>([]);
  const [selectedCaseStudy, setSelectedCaseStudy] = useState<string>('');
  const [filterOptions, setFilterOptions] = useState<FilterOption[]>([]);
  const [selectedFilters, setSelectedFilters] = useState<Record<string, string[]>>({});
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [openFilter, setOpenFilter] = useState<string | null>(null);

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

  // Sync with external filter changes (e.g., from summary table clicks or agent)
  useEffect(() => {
    if (filters) {
      setSelectedFilters(filters);
    }
  }, [filters]);

  // Sync with agent-applied weight overrides.
  // Returns the same `prev` reference when nothing changed so the downstream
  // `onWeightsChange` effect doesn't fire and re-enter an infinite loop.
  useEffect(() => {
    if (!weights || Object.keys(weights).length === 0) return;
    setObjectiveWeights((prev) => {
      const hasChange = prev.some(
        (obj) => obj.name in weights && weights[obj.name] !== obj.weight,
      );
      if (!hasChange) return prev;
      return prev.map((obj) =>
        obj.name in weights ? { ...obj, weight: weights[obj.name] } : obj,
      );
    });
  }, [weights]);

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
    <Drawer className="sidebar" variant="permanent">
      <Box
        className="sidebar__scroll"
        sx={{
          overflowY: 'auto',
          flexGrow: 1,
          scrollbarWidth: 'thin',
          scrollbarColor: 'rgba(255,255,255,0.2) transparent',
          '&::-webkit-scrollbar': { width: 4 },
          '&::-webkit-scrollbar-thumb': {
            backgroundColor: 'rgba(255,255,255,0.2)',
            borderRadius: 2,
          },
        }}
      >
        {/* Base container with consistent top/bottom padding */}
        <Box className="sidebar__content" sx={{ p: 2 }}>
          <Box
            className="sidebar__logo"
            sx={{
              display: 'flex',
              justifyContent: 'center',
              mb: 2,
              mx: 'auto',
              width: '120px',
              height: '120px',
              overflow: 'hidden',
              borderRadius: '8px',
              bgcolor: '#FAF9F6',
            }}
          >
            <img
              src={pyMOODSLogo}
              alt="pyMOODS Logo"
              style={{
                width: '100%',
                height: '100%',
                objectFit: 'contain',
                transform: 'scale(1.35)',
                transformOrigin: 'center center',
              }}
            />
          </Box>
          {/* Use Case Section */}
          <Box className="sidebar__section sidebar__section--use-case" sx={{ mb: 3, mt: 0 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.75 }}>
              <Typography variant="body1" sx={{ color: 'white', fontWeight: 500 }}>
                Use Case
              </Typography>
              <Tooltip title="Select the dataset to analyze. Each use case has its own solution set, objectives, and decision variables." placement="right" arrow>
                <InfoOutlinedIcon sx={{ fontSize: 14, color: 'rgba(255,255,255,0.55)', cursor: 'help' }} />
              </Tooltip>
            </Box>
            <Box sx={{ borderBottom: '1px solid', borderColor: 'white', width: '100%', mb: 1.5 }} />
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
          <Box className="sidebar__section sidebar__section--filters" sx={{ mb: 3 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.75 }}>
                <Typography variant="body1" sx={{ color: 'white', fontWeight: 500 }}>
                  Filters
                </Typography>
                <Tooltip title="Select values to narrow the solution set. Leaving a filter empty includes all values for that dimension." placement="right" arrow>
                  <InfoOutlinedIcon sx={{ fontSize: 14, color: 'rgba(255,255,255,0.55)', cursor: 'help' }} />
                </Tooltip>
              </Box>
              {Object.values(selectedFilters).some(arr => arr.length > 0) && (
                <Button
                  size="small"
                  onClick={() => {
                    const cleared = Object.keys(selectedFilters).reduce((acc, key) => {
                      acc[key] = [];
                      return acc;
                    }, {} as Record<string, string[]>);
                    setSelectedFilters(cleared);
                    if (onFiltersChange) onFiltersChange(cleared);
                  }}
                  sx={{ color: 'rgba(255,255,255,0.65)', fontSize: '0.72rem', textTransform: 'none', minWidth: 0, px: 0.75, py: 0.25, '&:hover': { color: 'white', bgcolor: 'rgba(255,255,255,0.08)' } }}
                >
                  Clear all
                </Button>
              )}
            </Box>
            <Box sx={{ borderBottom: '1px solid', borderColor: 'white', width: '100%', mb: 1.5 }} />
            {loading && filterOptions.length === 0 ? (
              <Box sx={{ my: 1.5, display: 'flex', justifyContent: 'center' }}>
                <CircularProgress size={20} sx={{ color: 'white' }} />
              </Box>
            ) : (
              filterOptions.map((filter) => {
                const isFilterAgentSet = filter.key in agentAppliedFilters && agentAppliedFilters[filter.key].length > 0;
                return (
                <Box key={filter.key} sx={{ mb: 2 }}>
                  <FormControl fullWidth size="small">
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5, mb: 0.5 }}>
                      <SidebarInputLabel sx={{ mb: '0 !important' }}>{filter.name}</SidebarInputLabel>
                      {isFilterAgentSet && (
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.3 }}>
                          <AutoAwesomeIcon sx={{ fontSize: 10, color: 'rgba(255,255,255,0.55)' }} />
                          <Typography variant="caption" sx={{ fontSize: '0.6rem', color: 'rgba(255,255,255,0.55)', lineHeight: 1 }}>
                            set by AI
                          </Typography>
                        </Box>
                      )}
                    </Box>
                    <SidebarSelect
                      multiple
                      open={openFilter === filter.key}
                      onOpen={() => setOpenFilter(filter.key)}
                      onClose={() => setOpenFilter(null)}
                      value={selectedFilters[filter.key] || []}
                      onChange={(e) => {
                        handleFilterChange(filter.key, e.target.value as string[]);
                        setOpenFilter(null);
                      }}
                      renderValue={(selected) =>
                        (selected as string[]).length === 0
                          ? <em style={{ color: '#aaa', fontStyle: 'italic', fontSize: '0.85em' }}>All</em>
                          : null
                      }
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
                );
              })
            )}
          </Box>

          {/* Objective Weights Section */}
          <Box className="sidebar__section sidebar__section--weights" sx={{ mb: 3 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.75 }}>
              <Typography variant="body1" sx={{ color: 'white', fontWeight: 500 }}>
                Objective Weights
              </Typography>
              <Tooltip
                title="Higher values prioritize minimizing this objective. Weights are relative — doubling one value halves the effective importance of the others. Range: 0–100."
                placement="right"
                arrow
              >
                <InfoOutlinedIcon sx={{ fontSize: 14, color: 'rgba(255,255,255,0.55)', cursor: 'help' }} />
              </Tooltip>
            </Box>
            <Box sx={{ borderBottom: '1px solid', borderColor: 'white', width: '100%',  mb: 1.5 }} />
            {objectiveWeights.length === 0 ? (
              <Typography variant="body2" color="text.secondary">No objectives found.</Typography>
            ) : (() => {
              const totalWeight = objectiveWeights.reduce((sum, o) => sum + Math.max(0, Number(o.weight) || 0), 0);
              return objectiveWeights.map((obj, index) => {
                const isAgentModified = obj.name in agentAppliedWeights;
                const pct = totalWeight > 0 ? Math.round((Math.max(0, Number(obj.weight) || 0) / totalWeight) * 100) : 0;
                return (
                <Box key={obj.name} sx={{ mb: 1.5 }}>
                  {/* Name + input row */}
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 1 }}>
                    <Box sx={{ flex: 1, minWidth: 0 }}>
                      <Typography variant="body2" color="white" sx={{ fontSize: '14px', wordBreak: 'break-word', overflowWrap: 'anywhere', textAlign: 'left' }}>
                        {obj.name}
                      </Typography>
                      {isAgentModified && (
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.4, mt: 0.3 }}>
                          <AutoAwesomeIcon sx={{ fontSize: 10, color: 'rgba(255,255,255,0.55)' }} />
                          <Typography variant="caption" sx={{ fontSize: '0.6rem', color: 'rgba(255,255,255,0.55)', lineHeight: 1 }}>set by AI</Typography>
                        </Box>
                      )}
                    </Box>
                    <TextField
                      type="number"
                      value={obj.weight}
                      onChange={(e) => handleWeightChange(index, e.target.value)}
                      size="small"
                      slotProps={{ htmlInput: { min: 0, max: 100, step: 1, style: { textAlign: 'center', padding: '4px', width: '5ch', backgroundColor: 'white', borderRadius: '4px' } } }}
                      sx={{
                        '& .MuiOutlinedInput-root': { backgroundColor: 'white', borderRadius: '4px', height: '30px', input: { padding: '6px' }, outline: isAgentModified ? '2px solid rgba(255,255,255,0.4)' : 'none' },
                        '& .MuiOutlinedInput-notchedOutline': { borderColor: isAgentModified ? 'rgba(255,255,255,0.6)' : '#ccc' },
                        '&:hover .MuiOutlinedInput-notchedOutline': { borderColor: '#888' },
                        '&.Mui-focused .MuiOutlinedInput-notchedOutline': { borderColor: '#007FFF' },
                      }}
                    />
                  </Box>
                  {/* Relative-weight progress bar */}
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.75, mt: 0.5 }}>
                    <LinearProgress
                      variant="determinate"
                      value={pct}
                      sx={{ flex: 1, height: 3, borderRadius: 2, bgcolor: 'rgba(255,255,255,0.15)', '& .MuiLinearProgress-bar': { bgcolor: 'rgba(255,255,255,0.65)', borderRadius: 2 } }}
                    />
                    <Typography variant="caption" sx={{ fontSize: '0.6rem', color: 'rgba(255,255,255,0.55)', minWidth: '26px', textAlign: 'right' }}>
                      {pct}%
                    </Typography>
                  </Box>
                </Box>
                );
              });
            })()
            }
          </Box>
        </Box>
      </Box>
    </Drawer>
  );
};

export default SideMenu;