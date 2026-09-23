---
title: "pyMOODS: Multi-Criteria Decision Support for Large-Scale Infrastructure Planning"
date: 21 September 2026
bibliography: paper.bib
authors:
    - name: Jennifer Pham
      affiliation: "1"
    - name: Milan Jain
      affiliation: "1"
    - name: Palak Mattoo
      affiliation: "1"
affiliations:
    - index: 1
      name: Pacific Northwest National Laboratory
---

# Summary

In energy infrastructure planning, there are hundreds of feasible designs that could be considered. A less expensive design may be less resilient, while a more reliable design may require greater capital investment or create environmental costs. Optimization models can help rank designs given a priority, but they do not determine which trade-off is appropriate for a particular stakeholder.

`pyMOODS` is an open-source decision-support framework for exploring these choices. It loads optimization and simulation results through a metadata-driven data model, applies several multi-criteria decision-making (MCDM) methods, and renders interactive views of objectives, decision variables, candidate solutions, and scenarios. Version 0.0.4 introduces the capability of an AI chatbot that can intake natural language to help determine an optimal solution for a given use case through the user interface. The aim is to make the evidence, assumptions, and consequences behind candidate decisions easier to inspect.

# Statement of need

Large-scale infrastructure planning and operations require operators to optimize multiple parameters and evaluate the system over multiple criteria and under multiple scenarios. Co-design and multi-objective optimization therefore produce sets of non-dominated alternatives rather than a single answer. The difficult post-optimization task is to compare these alternatives, elicit preferences, understand sensitivity to those preferences, and communicate trade-offs among domain experts and stakeholders [@branke2008multiobjective].

`pyMOODS` addresses this interpretation gap for researchers, infrastructure planners, systems engineers, and analysts. It supports heterogeneous formulations and the input of case-study descriptors that identify hyperparameters, decision variables, objective functions, and optional control inputs, including each objective's optimization direction.

# State of the field

Research software for multi-objective optimization spans algorithm-oriented frameworks, such as `pymoo` [@blank2020pymoo] and jMetalPy [@benitezhidalgo2019jmetalpy]. `pyMOODS` complements these tools by starting from external optimization and simulation results and support the subsequent human decision process through linked scenario views, post-optimization ranking methods, and domain-specific metadata.

`pyMOODS` was built as a separate framework because its research requirements span capabilities that are normally separated. It combines a case-study JSON schema, linked solution and scenario views, multiple MCDM methods, generalizer/specializer analysis, and optional AI assistance grounded in the current dashboard state. Adding these capabilities to an optimization library would require substantial data-loading, application-state, and scenario-analysis infrastructure outside the library's primary purpose. General visualization packages, in turn, do not provide the multi-objective decision methods or infrastructure-planning semantics required by this workflow.

# Software design

## Architecture and data flow

`pyMOODS` separates interactive rendering from analytical computation. A React and Material UI frontend maintains coordinated application state with Zustand. A Flask backend loads solutions from CSV files and case-study metadata from JSON schemas. The backend validates and caches the data, filters alternatives, and returns structured results. Version 0.0.4 refactors the backend into Flask Blueprints for case studies, solutions, visualizations, parameters, trade-offs, and chat. Pure helper modules isolate filtering, normalization, labeling, ranking, graph construction, and model access. This separation makes domain calculations testable without a browser and allows new visual panels or case studies to reuse stable data contracts.

The frontend centers on three linked views: a scatter plot for exploring and selecting solutions, a summary table for comparing alternatives, and a parallel-coordinates plot for examining trade-offs among objectives. Hyperparameter filters can be applied to analyze solutions under certain conditions.

## Decision-support workflow

The software supports the weighted-sum method [@marler2010weighted], TOPSIS [@hwang1981multiple], VIKOR [@opricovic2004compromise], and generalizer/specializer analyses. Providing multiple methods helps users identify rankings that depend on a particular scoring assumption and distinguish balanced solutions from those that perform especially well on individual objectives. The trade-off lattice groups solutions by user-selected scenario dimensions and allows users to inspect each group's members and objective profiles.

Version 0.0.4 extends the visual workflow with `mooCHAT`, an optional large language model interface. The backend exposes explicit tools for querying solutions, summarizing trade-offs, and comparing alternatives. If prompted, `mooCHAT` can perform actions on the user interface, such as changing a chart, updating filters, highlighting variables, changing a weight, setting scenario aggregation, or resetting the dashboard. This AI feature should be considered as an aid rather than an autonomous decision-maker.

# Research impact statement

Infrastructure planning often requires choosing among alternatives with competing cost, reliability, and performance objectives, yet optimization results are commonly examined through problem-specific scripts or static figures. `pyMOODS` addresses this gap by providing a reusable, interactive workflow for exploring, ranking, and comparing multi-objective solutions.

The software's applicability is demonstrated by using example case studies of offshore-wind farms, battery-storage planning, and data-center design optimization. These studies use the same metadata-driven interface despite having different objectives, decision variables, hyperparameters, and network data. They therefore provide concrete examples of reusing the software across various infrastructure-planning problems rather than developing a new dashboard for each formulation.

Since 2023, multiple contributors have developed and applied `pyMOODS`. Version 0.0.4 includes reproducible example data, a developer guide, modular extension points, and end-to-end tests for principal dashboard interactions. The project also provides a versioned Zenodo archive [@pham2026pymoods_v004], a permissive BSD 3-Clause license, contribution guidelines, and a public issue and development history. These materials allow researchers to reproduce the bundled analyses, introduce new optimization studies through the metadata contract, and compare how alternative decision-support methods affect the selection of infrastructure designs.

# AI usage disclosure

Generative AI tools, including ChatGPT Enterprise, an internal Pacific Northwest National Laboratory AI tool, and OpenAI Codex, were used to assist with software development, documentation, and preparation of this
manuscript. The authors reviewed and edited the generated text, checked technical statements against the source code and documentation, and checked any bibliographic claims against their cited sources. AI outputs were not treated as evidence. `pyMOODS` itself optionally uses a configured large language model to implement `mooCHAT`; its responses and requested interface actions remain subject to the grounding and validation mechanisms described above. The authors retain responsibility for the manuscript and software.

# Acknowledgements

This research was supported by the E-COMP initiative at the Pacific Northwest National Laboratory (PNNL). The computational work for this research was performed using Research Computing at PNNL.  PNNL is a multi-program national laboratory operated for the U.S. Department of Energy (DOE) by Battelle Memorial Institute under Contract No. DE AC05 76RL01830.

# References
