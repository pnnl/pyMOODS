import { useState, useEffect } from 'react';
import { Box, Typography } from '@mui/material';
import AppNavbar from './components/AppNavbar';
import SideMenu from './components/SideMenu';
import MainGrid from './components/MainGrid';

const drawerWidth = 240;

function App() {
  const [selectedUseCase, setSelectedUseCase] = useState<string>('');
  const [filters, setFilters] = useState<Record<string, string[]>>({});
  const [weights, setWeights] = useState<Record<string, number>>({});
  const [isDataLoaded, setIsDataLoaded] = useState<boolean>(false); // Track if data is ready

  const handleWeightsChange = (newWeights: Record<string, number>) => {
    setWeights(newWeights);
  };

  const handleFiltersChange = (newFilters: Record<string, string[]>) => {
    setFilters(newFilters);
  };

  const handleLocationSelect = (location: string) => {
    setFilters(prevFilters => ({
      ...prevFilters,
      Location: [location]
    }));
  };

  // Load default use case
  useEffect(() => {
    setSelectedUseCase('MoCoDo_v3');
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
    <Box sx={{ display: 'flex', width: "100%", minHeight: '100vh', bgcolor: 'background.default' }}>
      {/* Sidebar */}
      <Box
        sx={{
          width: drawerWidth,
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
        />
      </Box>

      {/* Main Content Area */}
      <Box
        component="main"
        sx={{
          flexGrow: 1,
          display: 'flex',
          flexDirection: 'column',
          width: 'calc(100% - 240px)',  // Account for sidebar width
          maxWidth: 'none',
        }}
      >
        <Box sx={{ mb: 0, mt: 0, ml: 1, pl: 1 }}>
          <AppNavbar />
        </Box>

        {selectedUseCase ? (
          <>
            {
            // !isDataLoaded ? (
            //   <Box sx={{ textAlign: 'center', mt: 12 }}>
            //     <Typography variant="h6">Loading Use Case Data...</Typography>
            //     <Typography variant="body2" color="textSecondary">
            //       Please wait while we load filters and objective weights.
            //     </Typography>
            //     <Box sx={{ mt: 12 }}>
            //       <CircularProgress size={24} />
            //     </Box>
            //   </Box>
            // ) : 
            (
              <Box sx={{ textAlign: 'center', ml: 0, mr: 0, pl: 0, pr: 0, pt: 0, width: '100%' }}>
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
          <Box sx={{ textAlign: 'center', mt: 4 }}>
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