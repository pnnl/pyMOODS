#!/usr/bin/env python
from setuptools import setup, find_packages
import pathlib

# The directory containing this file
HERE = pathlib.Path(__file__).parent

# The text of the README file
README = (HERE / "README.md").read_text()

def get_requirements():
    with open(HERE / 'requirements.txt') as f:
        return [line.strip() for line in f if not line.startswith('#')]

setup(
    name='pymoods',
    version='0.1.0',
    description='Multi-Objective Optimization and Decision Support for electricity infrastructure planning',
    long_description=README,
    long_description_content_type='text/markdown',
    url='https://github.com/pymoods/pymoods',
    project_urls={
        'Documentation': 'https://pymoods.readthedocs.io',
        'Source': 'https://github.com/pymoods/pymoods',
        'Tracker': 'https://github.com/pymoods/pymoods/issues',
    },
    author='Milan Jain',
    author_email='milan.jain@pnnl.gov',
    maintainer='pyMOODS Team',
    maintainer_email='maintainers@pymoods.org',
    license='MIT',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Science/Research',
        'Intended Audience :: Developers',
        'Topic :: Scientific/Engineering',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Operating System :: OS Independent',
    ],
    packages=find_packages(include=['pymoods*']),
    python_requires='>=3.7',
    install_requires=[
        'pandas>=1.0.0',
        'numpy>=1.18.0',
        'plotly>=5.0.0',
        'pymoo>=0.6.0',
        'scipy>=1.5.0',
        'matplotlib>=3.0.0',
    ],
    extras_require={
        'dev': [
            'pytest>=6.0',
            'pytest-cov>=2.0',
            'flake8>=3.8',
            'black>=21.0',
            'isort>=5.0',
            'sphinx>=4.0',
            'sphinx-rtd-theme>=0.5',
        ],
        'docs': [
            'sphinx>=4.0',
            'sphinx-rtd-theme>=0.5',
            'sphinx-autodoc-typehints>=1.0',
        ],
    },
    include_package_data=True,
    package_data={
        'pymoods': ['data/*.csv', 'templates/*.html'],
    },
    entry_points={
        'console_scripts': [
            'pymoods=pymoods.cli:main',
        ],
    },
    zip_safe=False,
    keywords=[
        'multi-objective optimization',
        'decision support',
        'energy systems',
        'visual analytics',
        'MCDM',
    ],
)