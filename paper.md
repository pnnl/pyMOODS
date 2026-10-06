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

Large-scale infrastructure planning and operations require operators to optimize multiple parameters and evaluate the system over multiple criteria and under multiple scenarios [@krishnan2016cooptimization; @dvorkin2018coplanning; @cho2022recent]. Co-design and multi-objective optimization therefore produce sets of non-dominated alternatives rather than a single answer. The difficult post-optimization task is to compare these alternatives, elicit preferences, understand sensitivity to those preferences, and communicate trade-offs among domain experts and stakeholders [@miettinen1999nonlinear; @osika2023what].

The resulting workflow is summarized in \autoref{fig:motivation}.

![Conceptual multi-objective optimization and decision-support workflow. Optimization produces a set of non-dominated alternatives, after which a decision-maker uses visual analytics to evaluate trade-offs and select a preferred solution. This figure was originally prepared for and is also included in a related SoftwareX manuscript currently under review.\label{fig:motivation}](figures/fig_motivation.png){width="100%"}

`pyMOODS` addresses this interpretation gap for researchers, infrastructure planners, systems engineers, and analysts. It supports heterogeneous formulations and the input of case-study descriptors that identify hyperparameters, decision variables, objective functions, and optional control inputs, including each objective's optimization direction.

# State of the field

Research software for multi-objective optimization includes algorithm-oriented frameworks such as `pymoo` [@blank2020pymoo], PlatEMO [@tian2017platemo], and Borg [@hadka2013borg]. Multi-criteria decision-analysis libraries such as `pymcdm` [@kizielewicz2023pymcdm] and `pyDecision` [@pereira2026pydecision] rank alternatives after objectives have been defined. Visualization systems such as PAVED [@cibulski2020paved] and Parasol [@raseman2019parasol] support interactive exploration of Pareto fronts.

These tools cover complementary parts of the workflow, whereas `pyMOODS` starts from external optimization and simulation results and supports the subsequent human decision process. It combines a case-study JSON schema, linked solution and scenario views, multiple MCDM methods, generalizer/specializer analysis, and optional AI assistance grounded in the current dashboard state. Extending an algorithm, MCDM, or visualization package with this combination would require substantial data-loading, application-state, and scenario-analysis infrastructure outside its primary purpose. `pyMOODS` therefore provides a separate, domain-oriented workflow for post-optimization ranking and coordinated exploration of infrastructure-planning alternatives.

# Software design

## Architecture and data flow

`pyMOODS` separates interactive rendering from analytical computation. A React and Material UI frontend maintains coordinated application state with Zustand. A Flask backend loads solutions from CSV files and case-study metadata from JSON schemas. The backend validates and caches the data, filters alternatives, and returns structured results. Version 0.0.4 refactors the backend into Flask Blueprints for case studies, solutions, visualizations, parameters, trade-offs, and chat. Pure helper modules isolate filtering, normalization, labeling, ranking, graph construction, and model access. This separation makes domain calculations testable without a browser and allows new visual panels or case studies to reuse stable data contracts. The resulting data flow is shown in \autoref{fig:architecture}.

![Architecture and data flow of `pyMOODS` version 0.0.4. The React frontend communicates with Flask services that load and validate case-study data, perform analytical computations, and support the AI-assisted interaction layer. This figure is adapted from the related SoftwareX manuscript currently under review and updated here to include AI chat assistance.\label{fig:architecture}](figures/fig_architecture.jpg){width="95%"}

The frontend centers on three linked views: a scatter plot for exploring and selecting solutions, a summary table for comparing alternatives, and a parallel-coordinates plot for examining trade-offs among objectives. Hyperparameter filters can be applied to analyze solutions under certain conditions. \autoref{fig:dashboard} shows the current dashboard with a selected generalizer.

![The `pyMOODS` version 0.0.4 dashboard showing the solution-space scatter plot, objective weights and filters, and a generalizer selected in the analysis view.\label{fig:dashboard}](figures/fig_dashboard.png){width="95%"}

## Decision-support workflow

The software supports the weighted-sum method [@marler2010weighted], TOPSIS [@hwang1981multiple], VIKOR [@opricovic2004compromise], and generalizer/specializer analyses. Providing multiple methods helps users identify rankings that depend on a particular scoring assumption and distinguish balanced solutions from those that perform especially well on individual objectives. The trade-off lattice groups solutions by user-selected scenario dimensions and allows users to inspect each group's members and objective profiles.

Version 0.0.4 extends the visual workflow with `mooCHAT`, an optional large language model interface. The backend exposes explicit tools for querying solutions, summarizing trade-offs, and comparing alternatives. If prompted, `mooCHAT` can perform actions on the user interface, such as changing a chart, updating filters, highlighting variables, changing a weight, setting scenario aggregation, or resetting the dashboard. This AI feature should be considered as an aid rather than an autonomous decision-maker. An example interaction is shown in \autoref{fig:ai-chat}.

![Example `mooCHAT` interaction. In response to a natural-language request, the assistant applies the COTTONWOOD location filter, selects a candidate that minimizes cable material cost within that filtered set, and reports its decision variables and objective values.\label{fig:ai-chat}](figures/fig_ai_chat.png){width="95%"}

# Research impact statement

Infrastructure planning often requires choosing among alternatives with competing cost, reliability, and performance objectives, yet optimization results are commonly examined through problem-specific scripts or static figures. `pyMOODS` addresses this gap by providing a reusable, interactive workflow for exploring, ranking, and comparing multi-objective solutions.

The software's applicability is demonstrated by using example case studies of offshore-wind farms, battery-storage planning, and data-center design optimization, including the CAMEO co-design workflow [@meyur2024cameo]. These studies use the same metadata-driven interface despite having different objectives, decision variables, hyperparameters, and network data. They therefore provide concrete examples of reusing the software across various infrastructure-planning problems rather than developing a new dashboard for each formulation.

Since 2023, multiple contributors have developed and applied `pyMOODS`. Version 0.0.4 includes reproducible example data, a developer guide, modular extension points, and end-to-end tests for principal dashboard interactions. The project also provides a versioned Zenodo archive [@pham2026pymoods_v004], a permissive BSD 3-Clause license, contribution guidelines, and a public issue and development history. These materials allow researchers to reproduce the bundled analyses, introduce new optimization studies through the metadata contract, and compare how alternative decision-support methods affect the selection of infrastructure designs.

# AI usage disclosure

Generative AI tools, including ChatGPT Enterprise, an internal Pacific Northwest National Laboratory AI tool, and OpenAI Codex, were used to assist with software development, documentation, and preparation of this
manuscript. The authors reviewed and edited the generated text, checked technical statements against the source code and documentation, and checked any bibliographic claims against their cited sources. AI outputs were not treated as evidence. `pyMOODS` itself optionally uses a configured large language model to implement `mooCHAT`; its responses and requested interface actions remain subject to the grounding and validation mechanisms described above. The authors retain responsibility for the manuscript and software.

# Acknowledgements

This research was supported by the E-COMP initiative at the Pacific Northwest National Laboratory (PNNL). The computational work for this research was performed using Research Computing at PNNL.  PNNL is a multi-program national laboratory operated for the U.S. Department of Energy (DOE) by Battelle Memorial Institute under Contract No. DE AC05 76RL01830.

# References
