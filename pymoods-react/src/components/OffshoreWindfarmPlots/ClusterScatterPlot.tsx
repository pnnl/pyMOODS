import React, { useState, useEffect } from "react";
import * as Plotly from "plotly.js-basic-dist";
import createPlotlyComponent from "react-plotly.js/factory";
import {
  Box,
  Typography,
  Select,
  MenuItem,
  FormControl,
  InputLabel
} from "@mui/material";

// Import centralized config
import config from "../../config";
const { API_BASE_URL } = config;

const Plot = createPlotlyComponent(Plotly);

interface ScatterplotData {
  data: Plotly.Data[];
  layout: Partial<Plotly.Layout>;
}

interface Solution {
  [key: string]: any;
}

interface ClusterScatterPlotProps {
  useCase: string;
  solutionsData: Solution[];
  onColorByChange?: (colorBy: string) => void;
}

const ClusterScatterPlot: React.FC<ClusterScatterPlotProps> = ({
  useCase,
  solutionsData,
  onColorByChange
}) => {
  const [scatterplotData, setScatterplotData] =
    useState<ScatterplotData | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [colorBy, setColorBy] = useState<string>("AI-Generated");

  console.log(solutionsData)

  // Fetch scatterplot data
  useEffect(() => {
    if (!useCase || !solutionsData) return;

    setLoading(true);

    const payload = {
      use_case: useCase,
      solution_ids: solutionsData,//.map(sol => sol.id),
      color_by: colorBy
    };

    fetch(`${API_BASE_URL}/api/project`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify(payload)
    })
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
  }, [solutionsData, colorBy]);

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
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          mb: 1,
        }}
      >
        <Box sx={{ flex: 1, textAlign: "center" }}>
          <Typography sx={{ fontSize: "1.2rem" }}>Solution Space</Typography>
        </Box>
        {/* Clustering Dropdown */}
        <FormControl
          fullWidth
          size="small"
          variant="outlined"
          sx={{
            maxWidth: 150,
          }}
        >
        <InputLabel 
          id="color-by-select-label" 
          sx={{ fontSize: "1.1rem",
          fontFamily:
            "Inter, system-ui, Avenir, Helvetica, Arial, sans-serif",
          color: "#213547" }}
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
          {/* {Object.keys(filters).map((option) => (
            <MenuItem 
              key={option} 
              value={option}
              sx={{ fontSize: '0.875rem' }}
            >
              {option}
            </MenuItem>
          ))} */}
          
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
