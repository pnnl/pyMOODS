import { useEffect, useState } from 'react';
import * as Plotly from "plotly.js-basic-dist";
import createPlotlyComponent from "react-plotly.js/factory";

const Plot = createPlotlyComponent(Plotly);

const OffshoreWindfarmClusterScatterPlot = () => {
    interface ScatterplotData {
      data: Plotly.Data[];
      layout: Partial<Plotly.Layout>;
      config?: Partial<Plotly.Config>;
    }

    const [scatterplotData, setScatterplotData] = useState<ScatterplotData | null>(null);

    useEffect(() => {
      // Fetch scatterplot data from the API
      fetch('http://localhost:5000/api/scatterplot')
        .then((response) => response.json())
        .then((data) => {
          const plotData = JSON.parse(data.scatterplot); // Parse the JSON string
          setScatterplotData(plotData);
        })
        .catch((error) => console.error('Error fetching scatterplot:', error));
    }, []);
  
    if (!scatterplotData) {
      return <div>Loading...</div>;
    }
  
    return (
      <Plot
        data={scatterplotData.data}
        layout={scatterplotData.layout}
        config={scatterplotData.config}
      />
    );
  };

export default OffshoreWindfarmClusterScatterPlot;