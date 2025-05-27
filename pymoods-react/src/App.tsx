import React, { useState, useEffect } from 'react';
import { Box, Typography } from '@mui/material';
import AppNavbar from './components/AppNavbar';
import SideMenu from './components/SideMenu';
import MainGrid from './components/MainGrid';

function App() {
  // State for selected use case and filter values
  const [selectedUseCase, setSelectedUseCase] = useState<string>('');
  const [filters, setFilters] = useState<Record<string, string[]>>({});

  // Callback from SideMenu to update filters in App
  const handleFiltersChange = (newFilters: Record<string, string[]>) => {
    setFilters(newFilters);
  };

  // Optional: Load default use case on mount
  useEffect(() => {
    // Set a default use case if you want one to auto-load
    setSelectedUseCase('MoCoDo_v2'); // Make sure this matches one of your JSON files in demo_data/
  }, []);

  return (
    <Box sx={{ display: 'flex' }}>
      {/* Sidebar Menu */}
      <SideMenu 
        onFiltersChange={handleFiltersChange}
        onSelectUseCase={(useCase) => setSelectedUseCase(useCase)}
      />

      {/* Top Navbar */}
      <AppNavbar />

      {/* Main Content Area */}
      <Box component="main" sx={{ flexGrow: 1, p: 3 }}>
        {/* Main Grid with Plots */}
        {selectedUseCase ? (
          <MainGrid selectedUseCase={selectedUseCase} filters={filters} />
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