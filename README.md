<div align="center">
  <div style="margin: -40px 0 -50px 0;">
    <img src="./assets/logo.png" alt="PyMOODS Logo" width="200">
  </div>
  <p align="center">
    A Visualization Framework for Multi-Criteria Decision Making
  </p>
  <div style="margin-bottom: 20px;">
    <img src="https://img.shields.io/badge/license-BSD--3--Clause-blue?style=flat-square" alt="License">
  </div>
</div>

## Overview
An AI-enabled visualization capability for power systems planning that integrates co-design principles. The goal is to create a platform that combines cutting-edge artificial intelligence with interactive visualizations and theory of multi-criteria decision-making (MCDM) to address key challenges in large-scale infrastructure planning and operations. This tool will help stakeholders collaborate more effectively, enabling better decision-making by exploring complex scenarios in real time.

## Key Features
✅ Interactive Visualization of High-Dimensional Pareto Fronts\
✅ Plug-and-Play Data-Driven Framework\
✅ Scenario Comparison & Tradeoff Analysis\
✅ Customizable Decision Criteria & Constraints\
✅ Pre-Integrated Real-World Use Cases\
🚀 Coming Soon: Generative AI-Powered Interaction

## Quick Start

### Prerequisites
- python
- venv
- yarn
- node

### Starting the API Server

1. Create and activate a virtual environment (first-time setup):

Windows (PowerShell)
```bash
cd dashboard
python -m venv venv
.\venv\Scripts\Activate.ps1
```

macOS/Linux
```bash
cd dashboard
python3 -m venv venv
source venv/bin/activate
```

2. Install backend dependencies:

Windows
```bash
python -m pip install -r requirements.txt
```

macOS/Linux
```bash
python3 -m pip install -r requirements.txt
```

3. Start the API server:

Windows
```bash
cd backend/api
python react_api.py
```

macOS/Linux
```bash
cd backend/api
python3 react_api.py
```

The API should be running on `http://localhost:8080`

#### Starting the React App (Client)

1. Open a new terminal and navigate to the frontend directory

```bash
cd dashboard/frontend
```

2. Run the following to install the dependencies:

```bash
yarn install
```

3. Run the following to start the development server:

```bash
yarn start
```

You can now access the React app on `http://localhost:8081`.

## License

pyMOODS is released under the [BSD-3-Clause License](LICENSE.txt)

## Citation

If you use pyMOODS in your research, please cite:

```bibtex
@software{pymoods,
  title = {pyMOODS: Multi-Objective Optimization and Decision Support},
  author = {pyMOODS Contributors},
  year = {2023},
  publisher = {GitHub},
  journal = {GitHub repository},
}
```
