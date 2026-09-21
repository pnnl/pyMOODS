import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  LinearProgress,
} from '@mui/material';

interface Solution {
  [key: string]: any;
}

interface SummaryProps {
  data: Solution[]; // Data passed from MainGrid
  loading: boolean;
  filters?: Record<string, string[]>; // Filters from sidebar
  onRowSelect?: (solution: Solution) => void;
  onLocationSelect?: (location: string, locationField?: string) => void;
  selectedUseCase?: string; // Use case to help determine location field
  decisionKeys?: string[]; // Decision variable keys
  objectiveKeys?: string[]; // Objective function keys
  objectiveUnits?: Record<string, string>; // Units for objective functions
  selectedSolution?: Solution; // Externally controlled selected solution
}

const Summary: React.FC<SummaryProps> = ({ data, loading, filters, onRowSelect, onLocationSelect, selectedUseCase, decisionKeys = [], objectiveKeys = [], objectiveUnits = {}, selectedSolution: externalSelectedSolution }) => {
  const [selectedRowIndex, setSelectedRowIndex] = useState<number | null>(0);
  const [, setSelectedSolution] = useState<Solution | null>(null);

  // Helper function to detect the location field based on available data and use case
  const getLocationField = () => {
    if (!data || data.length === 0) return 'Location';
    
    // Check for different possible location field names
    const possibleLocationFields = [
      'Location Scenario', // For Cameo dataset
      'Location',          // For MoCoDo dataset
      'location',          // lowercase variant
      'LOCATION'           // uppercase variant
    ];
    
    for (const field of possibleLocationFields) {
      if (data[0].hasOwnProperty(field)) {
        return field;
      }
    }
    
    return 'Location'; // fallback
  };

  const locationField = getLocationField();

  // Filter data based on location field selections (dynamic field name detection)
  const filteredData = React.useMemo(() => {
    const filterKey = filters && Object.keys(filters).find(key => 
      key.toLowerCase().includes('location') || key === locationField
    ) || locationField;
    
    if (!filters || !filters[filterKey] || filters[filterKey].length === 0) {
      return data; // Return all data if no location filter is selected
    }
    
    return data.filter((solution) => {
      const solutionLocation = solution[locationField];
      return solutionLocation && filters[filterKey].includes(solutionLocation);
    });
  }, [data, filters, locationField]);

  // State for sorting
  const [sortConfig, setSortConfig] = useState<{
    key: string | null;
    direction: 'asc' | 'desc';
  }>({
    key: null,
    direction: 'asc',
  });


  // Sorted data
  const sortedData = [...filteredData].sort((a, b) => {
    if (!sortConfig.key) return 0;

    const aValue = a[sortConfig.key];
    const bValue = b[sortConfig.key];

    if (typeof aValue === 'number' && typeof bValue === 'number') {
      return sortConfig.direction === 'asc' ? aValue - bValue : bValue - aValue;
    }

    return 0;
  });

  useEffect(() => {
    if (!filteredData || filteredData.length === 0) return;

    const index = selectedRowIndex ?? 0;
    const solution = sortedData[Math.min(index, sortedData.length - 1)];
    
    setSelectedSolution(solution);
    if (onRowSelect) {
      onRowSelect(solution);
    }
  }, [filteredData, sortedData, selectedRowIndex]);

  // Reset selection when filteredData changes (new Location filter applied)
  useEffect(() => {
    if (filteredData.length > 0) {
      setSelectedRowIndex(0);
    }
  }, [filteredData.length]);

  const formatValue = (value: any) => {
    if (typeof value === 'number' && !Number.isNaN(value)) {
      return Number.isInteger(value)
        ? value.toLocaleString('en-US')
        : value.toLocaleString('en-US', {
            minimumFractionDigits: 2,
            maximumFractionDigits: 2,
          });
    }
    return String(value);
  };

  const formatKey = (key: string) => {
    return key === 'weighted_score' ? 'Weighted Sum' : key;
  };

  // Use externally controlled solution if provided, otherwise fall back to first filtered solution
  const solution = externalSelectedSolution ?? filteredData[0];

  if (loading) return <LinearProgress />;
  if (!data || data.length === 0)
    return <Typography variant="body2" color="text.secondary">No solutions found.</Typography>;

  if (filteredData.length === 0) {
    return <Typography variant="body2" color="text.secondary">No solutions found for the selected location(s).</Typography>;
  }

  // Helper function to render a regular row
  const renderRow = (key: string, value: any) => (
    <Box
      key={key}
      sx={{ display: 'flex', alignItems: 'flex-start', columnGap: 1.5, py: 0.75 }}
    >
      <Typography variant="body2" sx={{ color: 'text.secondary', flex: '0 0 55%', wordWrap: 'break-word' }}>
        {formatKey(key)}:
      </Typography>
      <Typography variant="body2" sx={{ color: 'text.primary', flex: '1 1 45%', wordWrap: 'break-word', fontWeight: 500 }}>
        {formatValue(value)}
      </Typography>
    </Box>
  );

  // Helper function to render a section header row
  const renderSectionHeader = (title: string, isFirstSection: boolean = false) => (
    <Box
      key={`header-${title}`}
      sx={{ mb: 0.5, mt: 1, pt: isFirstSection ? 0 : 1, borderTop: isFirstSection ? 'none' : '1px solid', borderColor: isFirstSection ? undefined : 'divider' }}
    >
      <Typography variant="subtitle2" sx={{ fontWeight: 700, color: 'text.primary' }}>
        {title}
      </Typography>
    </Box>
  );

  // Build the organized table rows
  const buildTableRows = () => {
    if (!solution) return [];
    
    const rows = [];
    
    // Solution ID first
    if (solution['Solution ID'] !== undefined) {
      rows.push(renderRow('Solution ID', solution['Solution ID']));
    }
    
    // Decision Variables section
    const decisionVars = decisionKeys.filter(key => solution.hasOwnProperty(key));
    if (decisionVars.length > 0) {
      const isFirstSection = solution['Solution ID'] === undefined;
      rows.push(renderSectionHeader('Decision Variables', isFirstSection));
      decisionVars.forEach((key) => {
        rows.push(renderRow(key, solution[key]));
      });
    }
    
    // Objective Functions section
    const objectiveVars = objectiveKeys.filter(key => solution.hasOwnProperty(key));
    if (objectiveVars.length > 0) {
      rows.push(renderSectionHeader('Objective Functions'));
      objectiveVars.forEach((key) => {
        const unit = objectiveUnits[key];
        const displayValue = unit ? `${formatValue(solution[key])} ${unit}` : formatValue(solution[key]);
        rows.push(renderRow(key, displayValue));
      });
    }
    
    return rows;
  };

  return (
    <Box sx={{ 
      width: '100%',
      height: '100%',
      minHeight: 0,
      overflow: 'auto',
      '&::-webkit-scrollbar': {
        width: '8px',
      },
      '&::-webkit-scrollbar-track': {
        background: '#f1f1f1',
        borderRadius: '4px',
      },
      '&::-webkit-scrollbar-thumb': {
        background: '#c1c1c1',
        borderRadius: '4px',
        '&:hover': {
          background: '#a8a8a8',
        },
      },
      scrollbarWidth: 'thin',
      scrollbarColor: '#c1c1c1 #f1f1f1',
    }}>
      <Box sx={{
        bgcolor: 'background.default',
        border: 1,
        borderColor: 'divider',
        borderRadius: 2,
        p: 1,
        minHeight: '100%',
        boxSizing: 'border-box',
      }}>
        <Box sx={{ pb: 1.5 }}>
          {buildTableRows()}
        </Box>
      </Box>
    </Box>
  );
};

export default Summary;