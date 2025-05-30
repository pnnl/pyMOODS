// Summary.tsx
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

interface ClusterSummary {
  cluster: string | number;
  count: number;
  avg_weighted_score: number;
  best_solution: number;
  best_solution_id: number;
}

interface SummaryProps {
  useCase: string;
  filters: Record<string, string[]>;
  weights: Record<string, number>;
  clusterBy: string; // ✅ New required prop
}

const Summary: React.FC<SummaryProps> = ({ useCase, filters, weights, clusterBy }) => {
  const [clusterSummaries, setClusterSummaries] = useState<ClusterSummary[]>([]);
  const [loading, setLoading] = useState<boolean>(true);

  // Define consistent colors for each cluster
  const clusterColors = [
    "#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd",
    "#8c564b", "#e377c2", "#7f7f7f", "#bcbd22", "#17becf"
  ];

  useEffect(() => {
    if (!useCase || !filters || !weights || !clusterBy) return;

    const fetchSummaryData = async () => {
      setLoading(true);
      const queryParams = new URLSearchParams();

      // Add filters
      Object.entries(filters).forEach(([key, values]) => {
        if (Array.isArray(values)) {
          values.forEach(value => queryParams.append(key, value));
        }
      });

      // Add objective weights
      Object.entries(weights).forEach(([key, value]) => {
        queryParams.append(`weight_${key}`, value.toString());
      });

      // Use passed-in clusterBy instead of defaulting
      queryParams.append('use_case', useCase);
      queryParams.append('cluster_by', clusterBy); // ✅ Use dynamic clusterBy

      try {
        const response = await fetch(`${API_BASE_URL}/api/solutions?${queryParams.toString()}`);
        if (!response.ok) throw new Error("Failed to fetch cluster summaries");

        const data = await response.json();
        const sorted = [...data.clusters].sort((a: ClusterSummary, b: ClusterSummary) =>
          b.avg_weighted_score - a.avg_weighted_score
        );
        setClusterSummaries(sorted);
      } catch (error) {
        console.error('Error fetching cluster summaries:', error);
        setClusterSummaries([]);
      } finally {
        setLoading(false);
      }
    };

    fetchSummaryData();
  }, [useCase, filters, weights, clusterBy]); // ✅ Added clusterBy to dependency array

  return (
    <Box sx={{ width: '100%' }}>
      {loading ? (
        <LinearProgress />
      ) : clusterSummaries.length === 0 ? (
        <Typography variant="body2" color="textSecondary">
          No clusters found.
        </Typography>
      ) : (
        <TableContainer component={Paper}>
          <Table size="small">
          <TableHead>
            <TableRow>
                <TableCell align="left" sx={{ fontWeight: 'bold', width: '100px' }}>Cluster</TableCell>
                <TableCell align="center" sx={{ fontWeight: 'bold', width: '90px' }}>#Solutions</TableCell>
                <TableCell align="right" sx={{ fontWeight: 'bold', width: '110px' }}>Cost</TableCell>
                <TableCell align="right" sx={{ fontWeight: 'bold', width: '150px' }}>Best Solution (ID)</TableCell>
            </TableRow>
            </TableHead>
            <TableBody>
              {clusterSummaries.map((row, index) => (
                <TableRow
                  key={`cluster-${index}`}
                  sx={{
                    backgroundColor: clusterColors[index % clusterColors.length],
                    color: 'white',
                    '& .MuiTableCell-root': {
                      color: 'white'
                    }
                  }}
                >
                  <TableCell>{row.cluster}</TableCell>
                  <TableCell align="center">{row.count}</TableCell>
                  <TableCell align="right">{row.avg_weighted_score.toFixed(2)}</TableCell>
                  <TableCell align="right">{row.best_solution.toFixed(2)} ({row.best_solution_id})</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      )}
    </Box>
  );
};

export default Summary;