import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  LinearProgress,
} from '@mui/material';
import ArrowUpwardIcon from '@mui/icons-material/ArrowUpward';
import ArrowDownwardIcon from '@mui/icons-material/ArrowDownward';

interface Solution {
  [key: string]: any;
}

interface SummaryProps {
  data: Solution[]; // Data passed from MainGrid
  loading: boolean;
  filters?: Record<string, string[]>; // Filters from sidebar
  onRowSelect?: (solution: Solution) => void;
}

const Summary: React.FC<SummaryProps> = ({ data, loading, filters, onRowSelect }) => {
  const [selectedRowIndex, setSelectedRowIndex] = useState<number | null>(0);
  const [selectedSolution, setSelectedSolution] = useState<Solution | null>(null);

  if (loading) return <LinearProgress />;
  if (!data || data.length === 0)
    return <Typography>No solutions found.</Typography>;

  // Filter data based on Location selections
  const filteredData = React.useMemo(() => {
    if (!filters || !filters.Location || filters.Location.length === 0) {
      return data; // Return all data if no Location filter is selected
    }
    
    return data.filter((solution) => {
      // Check for Location field with different case variations
      const solutionLocation = solution.Location || solution.location || solution.LOCATION;
      return solutionLocation && filters.Location.includes(solutionLocation);
    });
  }, [data, filters]);

  if (filteredData.length === 0) {
    return <Typography>No solutions found for the selected location(s).</Typography>;
  }

  const allKeys = Array.from(new Set(filteredData.flatMap(Object.keys)));

  // State for sorting
  const [sortConfig, setSortConfig] = useState<{
    key: string | null;
    direction: 'asc' | 'desc';
  }>({
    key: null,
    direction: 'asc',
  });

  // Determine if a column is numeric
  const isNumericColumn = (key: string) =>
    filteredData.every((item) => typeof item[key] === 'number');

  // Handle sort toggle
  const handleSort = (key: string) => {
    setSortConfig((prev) => {
      if (prev.key === key) {
        return {
          key,
          direction: prev.direction === 'asc' ? 'desc' : 'asc',
        };
      } else {
        return { key, direction: 'asc' };
      }
    });
  };

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

  // Gradient: dark green (best) to light red (worst)
  const getRowColor = (index: number, total: number) => {
    const ratio = index / Math.max(1, total - 1);
    const r = Math.round(0 + ratio * (255 - 0));
    const g = Math.round(100 + ratio * (200 - 100));
    const b = Math.round(0 + ratio * (200 - 0));
    return `rgba(${r}, ${g}, ${b}, 0.3)`;
  };

  return (
    <Box sx={{ width: '100%' }}>
      <TableContainer sx={{ 
        overflowX: 'auto',
        overflowY: 'auto',
        maxHeight: '250px',
        '&::-webkit-scrollbar': {
          display: 'none',
        },
        '&': {
          '-ms-overflow-style': 'none',
          'scrollbar-width': 'none',
        },
      }}>
        <Table
          size="small"
          sx={{
            tableLayout: 'fixed',
            minWidth: 280,
            maxWidth: '95%',
            margin: '0 auto',
            width: 'max-content',
          }}
        >
          <TableHead
            sx={{
              position: 'sticky',
              top: 0,
              zIndex: 1,
            }}
          >
            <TableRow>
              {allKeys.map((key) => (
                <TableCell
                  key={`col-${key}`}
                  align={key === 'Weighted Sum' ? 'right' : 'left'}
                  sx={{
                    fontWeight: 500,
        fontFamily: 'Inter,system-ui, Avenir, Helvetica,Arial, sans-serif',
                    whiteSpace: 'normal',
                    wordWrap: 'break-word',
                    overflow: 'hidden',
                    textOverflow: 'ellipsis',
                    maxWidth: 150,
                    px: 1,
                    fontSize: '0.8rem',
                    verticalAlign: 'top',
                    cursor: isNumericColumn(key) ? 'pointer' : 'default',
                    '&:hover': isNumericColumn(key)
                      ? { backgroundColor: '#006400' }
                      : {},
                    backgroundColor: '#2e7d32', 
                    color: 'white'
                  }}
                  onClick={() => isNumericColumn(key) && handleSort(key)}
                >
                  <Box
                    sx={{
                      display: 'flex',
                      justifyContent:
                        key === 'Weighted Sum' ? 'flex-end' : 'flex-start',
                      alignItems: 'center',
                      gap: 0.5,
                    }}
                  >
                    {key === 'weighted_score' ? 'Weighted Sum' : key}
                    {isNumericColumn(key) && sortConfig.key === key && (
                      <>
                        {sortConfig.direction === 'asc' ? (
                          <ArrowUpwardIcon fontSize="small" />
                        ) : (
                          <ArrowDownwardIcon fontSize="small" />
                        )}
                      </>
                    )}
                  </Box>
                </TableCell>
              ))}
            </TableRow>
          </TableHead>

          <TableBody>
            {/* Add .slice(0, 5) if you want to limit to top 5 rows */}
            {sortedData.map((solution, index) => (
              <TableRow
                key={`solution-${index}`}
                sx={{
                  backgroundColor: getRowColor(index, sortedData.length),
                }}
              >
                {allKeys.map((key) => (
                  <TableCell
                    key={`sol-${index}-cell-${key}`}
                    align={key === 'Weighted Sum' ? 'right' : 'left'}
                    sx={{
                      whiteSpace: 'nowrap',
                      overflow: 'hidden',
                      textOverflow: 'ellipsis',
                      px: 1,
                      fontSize: '0.75rem',
                    }}
                  >
                    {typeof solution[key] === 'number' && !Number.isNaN(solution[key])
                      ? Number.isInteger(solution[key])
                        ? solution[key]
                        : solution[key].toFixed(2)
                      : solution[key]}
                  </TableCell>
                ))}
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
    </Box>
  );
};

export default Summary;