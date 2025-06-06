import React, { useState, useEffect } from "react";
import * as Plotly from "plotly.js-basic-dist";
import createPlotlyComponent from "react-plotly.js/factory";
import {
  Box,
  Typography,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Slider
} from "@mui/material";

// Import centralized config
import config from "../../config";
const { API_BASE_URL } = config;

const Plot = createPlotlyComponent(Plotly);

interface ScatterplotData {
  data: Plotly.Data[];
  layout: Partial<Plotly.Layout>;
}

interface ClusterScatterPlotProps {
  useCase: string;
  filters: Record<string, string[]>;
  weights: Record<string, number>; 
  onWeightsChange?: (weights: Record<string, number>) => void;
  onColorByChange?: (colorBy: string) => void;
}

const ClusterScatterPlot: React.FC<ClusterScatterPlotProps> = ({
  useCase,
  filters,
  weights,
  onColorByChange
}) => {
  const [scatterplotData, setScatterplotData] =
    useState<ScatterplotData | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [colorBy, setColorBy] = useState<string>("AI-Generated");

  // Fetch scatterplot data
  useEffect(() => {
    if (!useCase || Object.keys(weights).length === 0) return;

    setLoading(true);

    // const availableOptions = Object.keys(filters);
    // const valid = availableOptions.includes(colorBy);
  
    // if (!valid || useCase) {
    //   const newColorBy = "AI-Generated";
    //   setColorBy(newColorBy);
    //   if (onColorByChange) {
    //     onColorByChange(newColorBy);
    //   }
    // }

    const queryParams = new URLSearchParams();

    // Add selected color field
    queryParams.append('color_by', colorBy);

    // Add other filters
    Object.entries(filters).forEach(([key, values]) => {
      if (Array.isArray(values) && values.length > 0) {
        values.forEach((value) => queryParams.append(key, value));
      }
    });

    console.log("Weights:", weights);
    queryParams.append("weights", JSON.stringify(weights)); // send weights

    const url = `${API_BASE_URL}/api/scatterplot?${queryParams.toString()}&use_case=${encodeURIComponent(useCase)}`;
    console.log("URL:", url);

    fetch(url)
      .then((response) => {
        if (!response.ok)
          throw new Error(`HTTP error! status: ${response.status}`);
        return response.json();
      })
      .then((data) => {
        try {
          const plotData = JSON.parse(data.scatterplot);
          setScatterplotData(plotData);
        } catch (parseError) {
          console.error("Failed to parse Plotly JSON:", parseError);
        }
      })
      .catch((error) => {
        console.error("Error fetching or parsing scatterplot:", error);
      })
      .finally(() => {
        setLoading(false);
      });
  }, [useCase, filters, weights, colorBy]);

  if (loading || !scatterplotData) {
    return (
      <Box
        sx={{
          display: "flex",
          justifyContent: "center",
          alignItems: "center",
          height: "50vh",
        }}
      >
        <Typography variant="body1">Loading Scatterplot...</Typography>
      </Box>
    );
  }

  const improvedLayout = {
    ...scatterplotData.layout,
    height: 450,
  };

  return (
    <Box
      sx={{
        width: "100%",
        mt: 1,
        mb: 1,
        display: "flex",
        flexDirection: "column",
        gap: 1,
      }}
    >
      {/* Clustering Dropdown */}
      <FormControl
        fullWidth
        sx={{
          display: "flex",
          justifyContent: "center",
          mb: 2,
          maxWidth: 150,
          margin: "0 auto",
        }}
      >
        <InputLabel 
          id="color-by-select-label" 
          sx={{ fontSize: '0.875rem' }}
        >
          Color By
        </InputLabel>
        <Select
          labelId="color-by-select-label"
          value={colorBy}
          label="Color By"
          onChange={(e) => {
            const newColorBy = e.target.value as string;
            setColorBy(newColorBy);
            if (onColorByChange) {
              onColorByChange(newColorBy);
            }
          }}
          sx={{
            height: 40,
            fontSize: "0.875rem",
            textAlign: "center",
          }}
        >
          <MenuItem 
            key="AI-Generated" 
            value="AI-Generated"
            sx={{ fontSize: '0.875rem' }}
          >
            AI-Generated
          </MenuItem>
          {Object.keys(filters).map((option) => (
            <MenuItem 
              key={option} 
              value={option}
              sx={{ fontSize: '0.875rem' }}
            >
              {option}
            </MenuItem>
          ))}
          
        </Select>
      </FormControl>

      <Box
        sx={{
          display: "flex",
          flexDirection: "row",
          alignItems: "center",
          width: "100%",
        }}
      >
        {/* Plot */}
        <Box sx={{ flexGrow: 1 }}>
          <Plot
            data={scatterplotData.data}
            layout={improvedLayout}
            config={{
              responsive: true,
              scrollZoom: true,
              modeBarButtonsToRemove: ["toggleSpikelines"],
            }}
            style={{ width: "100%" }}
            useResizeHandler
          />
        </Box>
      </Box>
    </Box>
  );
};

export default ClusterScatterPlot;
