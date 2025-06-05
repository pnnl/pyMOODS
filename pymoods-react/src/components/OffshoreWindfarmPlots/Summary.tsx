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
  Paper,
  LinearProgress
} from '@mui/material';

import config from '../../config';
const { API_BASE_URL } = config;

interface Solution {
  [key: string]: any;
}

interface SummaryProps {
  useCase: string;
  filters: Record<string, string[]>;
  weights: Record<string, number>;
  clusterBy: string;
}

const Summary: React.FC<SummaryProps> = ({ useCase, filters, weights, clusterBy }) => {
  const [solutions, setSolutions] = useState<Solution[]>([]);
  const [loading, setLoading] = useState<boolean>(true);

  useEffect(() => {
    if (!useCase || !filters || !weights || !clusterBy) return;

    const fetchTopSolutions = async () => {
      setLoading(true);
      const queryParams = new URLSearchParams();

      Object.entries(filters).forEach(([key, values]) => {
        values.forEach(value => queryParams.append(key, value));
      });

      Object.entries(weights).forEach(([key, value]) => {
        queryParams.append(`weight_${key}`, value.toString());
      });

      queryParams.append('use_case', useCase);
      queryParams.append('cluster_by', clusterBy);

      try {
        const response = await fetch(`${API_BASE_URL}/api/solutions?${queryParams.toString()}`);
        if (!response.ok) throw new Error("Failed to fetch solutions");

        const data = await response.json();
        setSolutions(data.solutions || []);
      } catch (error) {
        console.error('Error fetching solutions:', error);
        setSolutions([]);
      } finally {
        setLoading(false);
      }
    };

    fetchTopSolutions();
  }, [useCase, filters, weights, clusterBy]);

  if (loading) return <LinearProgress />;
  if (solutions.length === 0) return <Typography>No solutions found.</Typography>;

  const allKeys = Array.from(new Set(solutions.flatMap(Object.keys)));

  // Gradient: dark green (best) to light red (worst)
  const getRowColor = (index: number, total: number) => {
    const ratio = index / Math.max(1, total - 1);
    // Color interpolation from dark green (0,100,0) to light red (255,200,200)
    const r = Math.round(0 + ratio * (255 - 0));
    const g = Math.round(100 + ratio * (200 - 100));
    const b = Math.round(0 + ratio * (200 - 0));
    return `rgba(${r}, ${g}, ${b}, 0.3)`; // Increased alpha for visibility
  };

  return (
    <Box sx={{ width: '100%' }}>
      <TableContainer component={Paper} sx={{ overflowX: 'auto' }}>
        <Table
          size="small"
          sx={{
            tableLayout: 'fixed',
            minWidth: 300,
            maxWidth: '95%',
            margin: '0 auto', // This centers the table
            width: 'max-content',
          }}
        >
          <TableHead>
            <TableRow>
              {allKeys.map((key) => (
                <TableCell
                  key={`col-${key}`}
                  align={key === 'Weighted Sum' ? 'right' : 'left'}
                  sx={{
                    fontWeight: 'bold',
                    whiteSpace: 'normal',
                    wordWrap: 'break-word',
                    overflow: 'hidden',
                    textOverflow: 'ellipsis',
                    maxWidth: 150,
                    px: 1,
                    fontSize: '0.8rem',
                    verticalAlign: 'top'
                  }}
                >
                  {key === 'weighted_score' ? 'Weighted Sum' : key}
                </TableCell>
              ))}
            </TableRow>
          </TableHead>

          <TableBody>
            {solutions.map((solution, index) => (
              <TableRow
                key={`solution-${index}`}
                sx={{
                  backgroundColor: getRowColor(index, solutions.length),
                  transition: 'transform 0.4s ease-in-out, box-shadow 0.3s ease',
                  ...(index === 0 && {
                    transform: 'scale3d(1.05, 1.05, 1)',
                    zIndex: 2,
                    boxShadow: 4,
                    '&:hover': {
                      transform: 'scale3d(1.08, 1.08, 1)',
                      boxShadow: 6,
                    },
                    // Optional bounce on mount using keyframes
                    animation: 'bounceIn 0.6s ease',
                    '@keyframes bounceIn': {
                      '0%': {
                        transform: 'scale3d(0.9, 0.9, 1)',
                        opacity: 0,
                      },
                      '60%': {
                        transform: 'scale3d(1.08, 1.08, 1)',
                        opacity: 1,
                      },
                      '100%': {
                        transform: 'scale3d(1.05, 1.05, 1)',
                      },
                    },
                  }),
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
                      fontSize: '0.75rem'
                    }}
                  >
                    {typeof solution[key] === 'number' ? solution[key].toFixed(2) : solution[key]}
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
