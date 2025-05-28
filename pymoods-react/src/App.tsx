import React, { useState, useEffect } from 'react';
import { Box, Typography } from '@mui/material';
import AppNavbar from './components/AppNavbar';
import SideMenu from './components/SideMenu';
import MainGrid from './components/MainGrid';

const drawerWidth = 240;

function App() {
  const [selectedUseCase, setSelectedUseCase] = useState<string>('');
  const [filters, setFilters] = useState<Record<string, string[]>>({});
  const [weights, setWeights] = useState<Record<string, number>>({});

  const handleWeightsChange = (newWeights: Record<string, number>) => {
    console.log("Weights received in App:", newWeights);
    setWeights(newWeights);
  };

  useEffect(() => {
    setSelectedUseCase('MoCoDo_v3');
  }, []);

  const handleFiltersChange = (newFilters: Record<string, string[]>) => {
    setFilters(newFilters);
  };

  return (
    <Box sx={{ display: 'flex', minHeight: '100vh', bgcolor: 'background.default' }}>
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
        />
      </Box>

      {/* Main Content Area */}
      <Box
        component="main"
        sx={{
          flexGrow: 1,
          display: 'flex',
          flexDirection: 'column',
        }}
      >
        <Box sx={{ mb: 0, mt: 0, ml: 1, pl: 1 }}>
          <AppNavbar />
        </Box>

        {selectedUseCase ? (
          <Box sx={{ 
            textAlign: 'center', pl: 3, pt: 0 }}>
            <MainGrid 
              selectedUseCase={selectedUseCase} 
              filters={filters} 
              weights={weights}
              onWeightsChange={handleWeightsChange}
            />
          </Box>
        ) : (
          <Box sx={{ 
            textAlign: 'center', mt: 4 }}>
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