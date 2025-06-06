import React from "react";
import RadialDistributionChart from "./components/RadialDistributionChart";
import * as d3 from "d3";

const sampleData = [
  {
    variable: "Temperature",
    distribution: d3.range(100).map(() => Math.random() * 100),
    selected: 65,
  },
  {
    variable: "Humidity",
    distribution: d3.range(100).map(() => Math.random() * 50),
    selected: 30,
  },
  {
    variable: "Wind",
    distribution: d3.range(100).map(() => Math.random() * 20),
    selected: 10,
  },
  {
    variable: "Pressure",
    distribution: d3.range(100).map(() => Math.random() * 1000),
    selected: 800,
  },
];

function App() {
  return (
    <div style={{ padding: 20 }}>
      <h2>Radial Distribution Chart (Interactive)</h2>
      <RadialDistributionChart data={sampleData} rotation={30} />
    </div>
  );
}

export default App;
