import { useState, useEffect } from 'react';
import Plotly from "plotly.js-basic-dist";
import createPlotlyComponent from "react-plotly.js/factory";
import * as d3 from "d3";

const Plot = createPlotlyComponent(Plotly);

const LMPPlot: React.FC = () => {
  const [data, setData] = useState<{ x: number[]; y: number[] }>({ x: [], y: [] });

  useEffect(() => {
    d3.csv("/data/LMP.csv").then((csvData) => {
      const x: number[] = [];
      const y: number[] = [];

      csvData.forEach((row, index) => {
        if (row.INTERVALSTARTTIME_GMT && row.LMP) {
          x.push(index); // Convert timestamps to sequential numbers for plotting
          y.push(parseFloat(row.LMP));
        }
      });

      setData({ x, y });
    });
  }, []);

  return (
    <Plot
      data={[{
        x: data.x,
        y: data.y,
        type: 'scatter',
        mode: 'lines+markers',
        marker: { color: 'blue' }
      }]}
      layout={{
        title: 'LMP Plot',
        xaxis: {
          title: 'Hour',
          tickmode: 'array',
          tickvals: [0, 5, 10, 15, 20],
          ticktext: ['0', '5', '10', '15', '20']
        },
        yaxis: {
          title: 'LMP',
          tickmode: 'array',
          tickvals: [0, 10, 20, 30, 40, 50, 60, 70],
          ticktext: ['0', '10', '20', '30', '40', '50', '60', '70']
        }
      }}
    />
  );
};

export default LMPPlot;