import os
import sys
sys.path.insert(0, os.path.abspath('..'))

project = 'pyMOODS'
copyright = '2025, Pacific Northwest National Laboratory'
author = 'Milan Jain'

release = '0.3.0'

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.viewcode',
    'sphinx.ext.napoleon',
    'sphinx_rtd_theme',
]

templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']

html_theme = 'sphinx_rtd_theme'
html_static_path = ['_static']