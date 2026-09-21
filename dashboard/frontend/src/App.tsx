import { useState, useEffect } from 'react';
import { Box, CircularProgress, Typography } from '@mui/material';
import AppNavbar from './components/AppNavbar';
import SideMenu from './components/SideMenu';
import MainGrid from './components/MainGrid';
import { SIDEBAR_WIDTH } from './layout';
import { useDashboardStore } from './store/dashboardStore';

function App() {
  const [selectedUseCase, setSelectedUseCase] = useState<string>('');
  const [filters, setFilters] = useState<Record<string, string[]>>({});
  const [weights, setWeights] = useState<Record<string, number>>({});
  const [isDataLoaded, setIsDataLoaded] = useState<boolean>(false); // Track if data is ready

  // When the agent applies a filter (Zustand store), propagate it into the
  // sidebar's filter state so the left panel reflects the change.
  const agentFilters = useDashboardStore((s) => s.dashboardState.activeFilters);
  useEffect(() => {
    if (Object.keys(agentFilters).length === 0) return;
    setFilters((prev) => {
      const merged = { ...prev };
      for (const [key, values] of Object.entries(agentFilters)) {
        merged[key] = values;
      }
      return merged;
    });
  }, [agentFilters]);

  // When the agent updates a weight (Zustand store), merge it into local weights
  // so the sidebar inputs and all chart API calls reflect the change.
  const agentWeightOverrides = useDashboardStore((s) => s.dashboardState.agentWeightOverrides);
  useEffect(() => {
    if (Object.keys(agentWeightOverrides).length === 0) return;
    setWeights((prev) => ({ ...prev, ...agentWeightOverrides }));
  }, [agentWeightOverrides]);

  const { setSidebarFilters, setSidebarWeights } = useDashboardStore();

  const handleWeightsChange = (newWeights: Record<string, number>) => {
    setWeights(newWeights);
    setSidebarWeights(newWeights);
  };

  const handleFiltersChange = (newFilters: Record<string, string[]>) => {
    setFilters(newFilters);
    setSidebarFilters(newFilters);
  };

  const handleLocationSelect = (location: string, locationField?: string) => {
    const field = locationField || 'Location'; // Default to 'Location' for backward compatibility
    setFilters(prevFilters => ({
      ...prevFilters,
      [field]: [location]
    }));
  };

  // Load default use case
  useEffect(() => {
    setSelectedUseCase('MoCoDo_v3'); // Default use case on initial load
  }, []);

  // Determine when filters and weights are fully loaded
  useEffect(() => {
    if (Object.keys(filters).length > 0 && Object.keys(weights).length > 0) {
      setIsDataLoaded(true);
    } else {
      setIsDataLoaded(false);
    }
  }, [filters, weights]);

  return (
    <Box className="app-shell" sx={{ display: 'flex', width: "100%", height: '100dvh', bgcolor: 'background.default'}}>
      {/* Sidebar */}
      <Box
        className="app-shell__sidebar"
        sx={{
          width: SIDEBAR_WIDTH,
          flexShrink: 0,
          borderRight: '1px solid',
          borderColor: 'divider',
          bgcolor: 'background.paper',
        }}
      >
        <SideMenu
          onFiltersChange={handleFiltersChange}
          onSelectUseCase={(useCase) => setSelectedUseCase(useCase)}
          onWeightsChange={handleWeightsChange}
          filters={filters}
          weights={weights}
        />
      </Box>

      {/* Main Content Area */}
      <Box
        className="app-shell__main"
        component="main"
        sx={{
          flexGrow: 1,
          display: 'flex',
          flexDirection: 'column',
          height: '100%',
          minHeight: 0,
          overflow: 'hidden',
        }}
      >
        <Box className="app-shell__header">
          <AppNavbar />
        </Box>

        {selectedUseCase ? (
          <>
            {
            !isDataLoaded ? (
              <Box className="app-shell__loading" sx={{ textAlign: 'center', mt: 12 }}>
                <Typography variant="h6">Loading Use Case Data...</Typography>
                <Typography variant="body2" color="textSecondary">
                  Please wait while we load filters and objective weights.
                </Typography>
                <Box className="app-shell__loading-spinner" sx={{ mt: 12 }}>
                  <CircularProgress size={24} />
                </Box>
              </Box>
            ) : 
            (
              <Box className="app-shell__content" sx={{ ml: 0, mr: 0, pl: 0, pr: 0, pt: 0, maxWidth: '100%', flex: 1, minHeight: 0 }}>
                <MainGrid
                  selectedUseCase={selectedUseCase}
                  filters={filters}
                  weights={weights}
                  onWeightsChange={handleWeightsChange}
                  onLocationSelect={handleLocationSelect}
                />
              </Box>
            )}
          </>
        ) : (
          <Box className="app-shell__empty-state" sx={{ textAlign: 'center', mt: 4 }}>
            <Typography variant="h6">Select a Use Case</Typography>
            <Typography variant="body2" color="textSecondary">
              Please choose a use case from the sidebar.
            </Typography>
          </Box>
        )}
      </Box>
    </Box>
  );
}

export default App;