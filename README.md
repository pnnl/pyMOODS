<div align="center">
  <div style="margin: -40px 0 -50px 0;">
    <img src="./assets/logo.png" alt="PyMOODS Logo" width="200">
  </div>
  <p align="center">
    A Visualization Framework for Multi-Criteria Decision Making
  </p>
  <div style="margin-bottom: 20px;">
    ![Python Versions](https://img.shields.io/badge/python-3.13%2B-blue)
    ![Latest Release](https://devops.pnnl.gov/e-comp/thrust-2/PyMOODS/-/badges/release.svg)
    ![pipeline status](https://devops.pnnl.gov/e-comp/thrust-2/PyMOODS/badges/main/pipeline.svg)
    ![License](https://img.shields.io/badge/license-MIT-blue)
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

## Installation

Install pyMOODS via pip:

```bash
# Coming soon on pip
```

For development installation:

```bash
git clone https://github.com/pymoods/pymoods.git
cd pymoods
pip install -e .
```

## Documentation
Work in progress.
<!-- Full documentation is available at [https://pymoods.readthedocs.io](https://pymoods.readthedocs.io), including:

- API reference
- Tutorials and examples
- Contribution guidelines
- Theory and methodology -->

## Quick Start

```python
npm run dev
```
## Running Locally

### Starting the API Server

1. In the `dashboard` directory, create or activate a virtual environment. If you are using `venv`, run the following command:

```bash
cd dashboard

./venv/Scripts/activate
```

2. Install the dependencies for your venv:

```bash
pip install -r requirements.txt
```

3. Run the following command to start the API server:

```bash
cd api
python react_api.py
```

The API should be running on `http://localhost:8081`

#### Starting the React App (Client)

1. In the `pymoods-react` directory, run the following to install the dependencies:

```bash
yarn install
```

2. Run the following to start the development server:

```bash
npm run dev
```

You can now access the React app on `http://localhost:8081`.

## Contributing

We welcome contributions from the community! Please see our [Contribution Guidelines](CONTRIBUTING.md) for details on how to:

- Report issues
- Submit pull requests
- Suggest new features
- Improve documentation

## License

pyMOODS is released under the MIT License. See [LICENSE](LICENSE) for full details.

## Citation

If you use pyMOODS in your research, please cite:

```bibtex
@software{pymoods,
  title = {pyMOODS: Multi-Objective Optimization and Decision Support},
  author = {pyMOODS Contributors},
  year = {2023},
  publisher = {GitLab},
  journal = {GitLab repository},
}
```

## Contact

For questions or support, please open an issue on GitHub or contact the project PI Dr. Milan Jain at [milan.jain@pnnl.gov](mailto:milan.jain@pnnl.gov).