# pyMOODS: Multi-Objective Optimization and Decision Support

[![Build Status](https://img.shields.io/gitlab/pipeline/pnnl/e-comp/thrust-2/PyMOODS?branch=master)](https://devops.pnnl.gov/e-comp/thrust-2/PyMOODS.git/-/pipelines)
[![Coverage](https://img.shields.io/codecov/c/github/pymoods/pymoods/master)](https://codecov.io/gh/pymoods/pymoods)
[![Documentation Status](https://img.shields.io/readthedocs/pymoods/latest)](https://pymoods.readthedocs.io/en/latest/)
[![License](https://img.shields.io/badge/license-MIT-blue)](https://opensource.org/licenses/MIT)
[![Python Versions](https://img.shields.io/badge/python-3.7%2B-blue)](https://www.python.org/downloads/)
[![Open Issues](https://img.shields.io/github/issues-raw/pymoods/pymoods)](https://devops.pnnl.gov/e-comp/thrust-2/PyMOODS/-/issues)
[![Contributors](https://img.shields.io/github/contributors/pymoods/pymoods)](https://github.com/pymoods/pymoods/graphs/contributors)
[![Last Commit](https://img.shields.io/github/last-commit/pymoods/pymoods)](https://github.com/pymoods/pymoods/commits/master)
[![Repo Stars](https://img.shields.io/github/stars/pymoods/pymoods)](https://github.com/pymoods/pymoods/stargazers)
[![Open Pull Requests](https://img.shields.io/github/issues-pr-raw/pymoods/pymoods)](https://github.com/pymoods/pymoods/pulls)

pyMOODS is an open-source visual analytics framework designed to support informed decision-making in electricity infrastructure planning. It integrates multi-criteria decision-making (MCDM), visual analytics, and artificial intelligence to provide comprehensive planning solutions.

## Key Features

- Multi-objective optimization for infrastructure planning
- Interactive visual analytics dashboard
- Integration with common electricity grid datasets
- Scenario comparison and sensitivity analysis
- Customizable decision criteria and constraints

## Installation

Install pyMOODS via pip:

```bash
pip install pymoods
```

For development installation:

```bash
git clone https://github.com/pymoods/pymoods.git
cd pymoods
pip install -e .
```

## Documentation

Full documentation is available at [https://pymoods.readthedocs.io](https://pymoods.readthedocs.io), including:

- API reference
- Tutorials and examples
- Contribution guidelines
- Theory and methodology

## Quick Start

```python
import pymoods

# Initialize the analysis framework
analyzer = pymoods.Analyzer()

# Load your infrastructure data
analyzer.load_data("grid_data.csv")

# Run multi-objective optimization
results = analyzer.optimize()

# Visualize the Pareto front
analyzer.visualize(results)
```

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
  title = {pyMOODS: Python Multi-Objective Optimization and Decision Support},
  author = {pyMOODS Contributors},
  year = {2023},
  publisher = {GitHub},
  journal = {GitHub repository},
  howpublished = {\url{https://github.com/pymoods/pymoods}},
}
```

## Contact

For questions or support, please open an issue on GitHub or contact the maintainers at [maintainers@pymoods.org](mailto:maintainers@pymoods.org).