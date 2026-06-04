GCR Dosimetry Pipeline
======================

.. image:: https://img.shields.io/badge/python-3.10%2B-blue
   :alt: Python 3.10+

.. image:: https://img.shields.io/badge/license-MIT-green
   :alt: MIT License

An open-source, reproducible pipeline for modeling galactic cosmic ray (GCR)
radiation exposure on Mars missions and benchmarking proton therapy
relative biological effectiveness (RBE) against real
`OpenTOPAS-RBE <https://github.com/OpenTOPAS/OpenTOPAS-RBE>`_ Monte Carlo output.

The same physics that describes a particle's path through shielding also
governs the cellular damage that becomes the clinical problem a physician
must solve — this pipeline treats that chain as one integrated system.

.. toctree::
   :maxdepth: 2
   :caption: Contents

   installation
   quickstart
   api/index
   validation
   references

Installation
------------

.. code-block:: bash

   git clone https://github.com/aryanhshah8/gcr-dosimetry-pipeline.git
   cd gcr-dosimetry-pipeline
   pip install -e ".[dev]"
   python scripts/download_data.py

Quickstart
----------

**Mars mission dose and cancer risk:**

.. code-block:: bash

   gcr-dose mission 2025-06-01 --surface-days 500 --age 35 --sex female

**Proton therapy LET/RBE evaluation:**

.. code-block:: bash

   gcr-dose rbe --dose-gy 2.0 --letd-kev-um 5.0 --alpha-beta-gy 3.0 --model mcnamara

**TOPAS benchmark (requires OpenTOPAS-RBE on PATH):**

.. code-block:: bash

   python scripts/run_topas_rbe_benchmark.py
   python scripts/compare_topas_rbe.py data/topas/proton_water_v79_reference.csv

**Run tests:**

.. code-block:: bash

   pytest                   # fast tests (excludes slow ensemble)
   pytest -m slow           # run full uncertainty ensemble locally

API Reference
=============

.. toctree::
   :maxdepth: 1

   api/spectrum
   api/trajectory
   api/transport
   api/dose
   api/neutron_table
   api/organ_dose
   api/sep
   api/rbe
   api/topas_benchmark
   api/uncertainty
   api/reid
   api/mission
   api/utils

.. rubric:: Module descriptions

- :mod:`gcr.spectrum` — GCR local interstellar spectra (LIS) + Gleeson-Axford force-field modulation
- :mod:`gcr.trajectory` — Hohmann transfer orbit + real Usoskin solar modulation data
- :mod:`gcr.transport` — CSDA stopping power, range tables, Bradt-Peters nuclear cross-sections
- :mod:`gcr.dose` — Absorbed dose, dose equivalent, ICRP-60 Q(L), precomputed 4π transport
- :mod:`gcr.neutron_table` — HZETRN-tabulated secondary neutron dose surrogate
- :mod:`gcr.organ_dose` — Organ self-shielding depths + ICRP-60 tissue routing
- :mod:`gcr.sep` — Solar Energetic Particle event module (Band-function spectra, acute risk)
- :mod:`gcr.rbe` — Proton therapy RBE models (Wedenberg, McNamara 2015)
- :mod:`gcr.topas_benchmark` — TOPAS/OpenTOPAS-RBE CSV parser and comparator
- :mod:`gcr.uncertainty` — Latin Hypercube uncertainty ensemble (8 physics + biology parameters)
- :mod:`gcr.reid` — NASA REID cancer risk model (Cucinotta 2013, ERR + EAR combined)
- :mod:`gcr.mission` — 3-phase Mars mission model (transit + surface + return)
- :mod:`gcr.utils` — Physical constants, ion species registry, material properties

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
