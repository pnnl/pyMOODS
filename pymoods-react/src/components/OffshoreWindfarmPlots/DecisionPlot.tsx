import { useState, useEffect } from 'react';
import Plotly from "plotly.js-basic-dist";
import createPlotlyComponent from "react-plotly.js/factory";
import { CircularProgress, Box, Typography, Paper } from '@mui/material';

const Plot = createPlotlyComponent(Plotly);

interface DecisionPlotProps {
  selectedLocations?: string[];
  selectedTechnologies?: string[];
  selectedDurations?: string[];
  selectedPowers?: string[];
}

const DecisionPlot: React.FC<DecisionPlotProps> = ({ 
  selectedLocations = [], 
  selectedTechnologies = [], 
  selectedDurations = [], 
  selectedPowers = [] 
}) => {
  const [decisionSpaceData, setDecisionSpaceData] = useState<any>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchDecisionSpace = async () => {
      try {
        setLoading(true);
        setError(null);
        
        // Create the request payload from the selected parameters
        const payload = {
          location: selectedLocations,
          hyperparameters: {
            technology: selectedTechnologies,
            duration: selectedDurations,
            power: selectedPowers
          }
        };
        
        console.log("Fetching decision space with params:", payload);
        
        const response = await fetch('http://localhost:5000/api/decision-space', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload),
        });

        const data = await response.json();
        
        if (!response.ok) {
          throw new Error(`Error: ${data.error || response.statusText}`);
        }
        
        if (data.error) {
          throw new Error(data.error);
        }
        
        // Check if we have valid data
        const parsedData = JSON.parse(data.decisionSpace);
        if (!parsedData || !parsedData.data) {
          throw new Error("Invalid or empty chart data received");
        }
        
        setDecisionSpaceData(parsedData);
      } catch (err: any) {
        console.error("Error fetching decision space:", err);
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    // Only fetch if we have at least one filter selected
    if (selectedLocations.length > 0 || 
        selectedTechnologies.length > 0 || 
        selectedDurations.length > 0 || 
        selectedPowers.length > 0) {
      fetchDecisionSpace();
    } else {
      // No filters selected, show instruction message
      setLoading(false);
      setDecisionSpaceData(null);
    }
  }, [selectedLocations, selectedTechnologies, selectedDurations, selectedPowers]);

  return (
    <Box sx={{ height: '100%', p: 1 }}>
      <Typography variant="h6" align="center" gutterBottom>
        Decision Space Distribution
      </Typography>
      {loading ? (
        <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '400px' }}>
          <CircularProgress />
        </Box>
      ) : error ? (
        <Paper elevation={3} sx={{ p: 2, bgcolor: '#ffebee', color: '#d32f2f' }}>
          <Typography variant="body1">Error loading decision space: {error}</Typography>
        </Paper>
      ) : !decisionSpaceData ? (
        <Paper elevation={3} sx={{ p: 2 }}>
          <Typography variant="body1">
            {selectedLocations.length === 0 && 
             selectedTechnologies.length === 0 && 
             selectedDurations.length === 0 &&
             selectedPowers.length === 0 
              ? "Please select filters from the side menu to view decision space data."
              : "No decision space data available for your current selection."}
          </Typography>
        </Paper>
      ) : (
        <Plot
          data={decisionSpaceData.data}
          layout={{
            ...decisionSpaceData.layout,
            autosize: true,
            height: 400,
            margin: { ...decisionSpaceData.layout.margin, t: 30 }
          }}
          config={{ 
            responsive: true,
            displayModeBar: true,
            displaylogo: false,
            modeBarButtonsToRemove: ['lasso2d', 'select2d']
          }}
          style={{ width: '100%', height: '100%' }}
        />
      )}
    </Box>
  );
};

export default DecisionPlot;