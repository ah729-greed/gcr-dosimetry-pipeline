# GCR Dosimetry Pipeline

An open-source Python pipeline for modeling galactic cosmic ray (GCR) radiation exposure on Mars missions, with organ-dose routing and REID risk estimation. It couples modulated spectra, shielding transport, dose calculation, and mission-level risk reporting into one reproducible codebase.

The point of the project is not to claim brand-new physics. The point is to make a serious, transparent, usable tool that turns scattered radiation models into something people can run, inspect, compare, and extend.

## Quick Start

```bash
git clone https://github.com/ah729-greed/gcr-dosimetry-pipeline && cd gcr-dosimetry-pipeline
pip install -e .
python scripts/download_data.py
python scripts/validate_pipeline.py
python scripts/validate_rbe.py
python scripts/run_topas_rbe_benchmark.py
python scripts/compare_topas_rbe.py data/topas/proton_water_v79_reference.csv
gcr-dose mission 2011-11-26 --surface-days 30
jupyter notebook notebooks/03_mars_mission_risk.ipynb
```

## Product Direction

This repository is being shaped as a research product, not just a notebook dump:

- a validated mission-assessment engine
- organ-routed risk reporting
- a clean CLI that produces readable scenario reports
- a dual-use path toward LET / RBE / proton-therapy benchmarking

## Multipurpose Layer

The repository now includes a separate LET/RBE layer for proton-style biological
weighting. This is meant to support crossover work into radiation oncology and
particle therapy without mixing those models into the core space-mission REID
workflow.

Example:

```bash
gcr-dose rbe --dose-gy 2.0 --letd-kev-um 5.0 --alpha-beta-gy 3.0 --model mcnamara
```

The current RBE models are implemented from the same equations used in
OpenTOPAS-RBE for Wedenberg and McNamara. They are best treated as proton
therapy models and exploratory LET-biology tools, not as validated mixed-field
space-radiation surrogates.

The repo now also includes a real TOPAS-facing benchmark workflow:

```bash
python scripts/run_topas_rbe_benchmark.py
python scripts/compare_topas_rbe.py data/topas/proton_water_v79_reference.csv
```

`scripts/run_topas_rbe_benchmark.py` runs a repo-owned proton-water phantom case
through TOPAS/OpenTOPAS-RBE, then merges the scored dose, LETd, Wedenberg-RBE,
and McNamara-RBE outputs into a compare-ready CSV.

Important detail: for the RBE comparison, `dose_Gy` in the merged reference CSV
is the prescribed dose used by the TOPAS RBE scorer. The scored physical dose
profile is preserved separately as `physical_dose_Gy`.

## Pipeline Structure

```
Module 1          Module 2           Module 3          Module 4        Module 5       Module 6
spectrum.py  -->  trajectory.py -->  transport.py -->  dose.py    -->  reid.py   -->  mission.py
                                                       + neutron_table.py

GCR Flux          Hohmann orbit      CSDA energy       Absorbed        Cancer risk    Full Mars
(Boschini 2020    + solar modulation loss + nuclear    dose, dose      (NASA REID     mission:
 per-species LIS   potential along    attenuation      equivalent,     ERR+EAR model  transit +
 + Gleeson-Axford  Mars transfer     (Bradt-Peters)    effective       + Monte Carlo  surface +
 force field)                        + HZETRN neutron  dose (ICRP-60)  uncertainty)   return
                                      table (Slaba14)
```

## Current Focus

The project is being tightened toward publication-grade validation against:

- MSL RAD transit absorbed dose and dose equivalent
- HZETRN-style shielding benchmarks
- organ-routed REID outputs for mission planning

## Validation

```
$ python scripts/validate_pipeline.py

VALIDATION 1: Proton flux at phi=550 MV, E=1000 MeV/n  ... PASS
VALIDATION 2: Proton range in water (CSDA)              ... PASS
VALIDATION 3: Full pipeline vs MSL RAD (1.84 ± 25%)
VALIDATION 4: HZETRN benchmark (Mrigakshi/Slaba)
VALIDATION 5: Dose equivalent & Q_eff vs MSL RAD
```

Current benchmark snapshot for the MSL-like transit case:

- absorbed dose rate: `1.84 mGy/day` vs RAD `1.84`
- dose equivalent rate: `4.80 mSv/day` vs RAD `4.81`
- `Q_eff = 2.60` vs RAD `2.62`
- post-shielding absorbed-dose mix: `H 46.7%`, `He 16.8%`, `HZE 30.9%`

There is also a small proton-therapy-side regression check:

```bash
python scripts/validate_rbe.py
```

`67` unit tests currently pass across the transport, dose, mission, organ-dose, REID, CLI, RBE, and TOPAS benchmark layers.

See also:

- [TOPAS benchmark plan](docs/topas_benchmark_plan.md)
- [validation and uncertainty notes](docs/validation_and_uncertainty.md)

The checked-in TOPAS benchmark reference is:

- [data/topas/proton_water_v79_reference.csv](/Users/aryan/Documents/Code/Astrobiology/gcr-dosimetry-pipeline/data/topas/proton_water_v79_reference.csv)

## Features

- **Organ-dose bridge**: organ-specific self-shielding depths route transport physics into organ-level REID inputs
- **CLI mission reports**: `gcr-dose mission ...` runs an end-to-end mission scenario from the terminal
- **Per-species HZE LIS**: Boschini et al. (2020) HelMod-inspired parameterizations with distinct spectral indices per ion
- **Full NASA REID model**: ERR + organ-specific EAR (Cucinotta 2013), survival-weighted integration, DDREF, case fatality fractions, Monte Carlo uncertainty propagation
- **3-phase mission model**: Earth→Mars transit + Mars surface stay (Hassler 2014 RAD data) + Mars→Earth return
- **HZETRN-tabulated neutron dose**: 2D interpolation table calibrated to Slaba (2014) and Mrigakshi (2013) published predictions
- **Charged-fragment surrogate**: reinjects a benchmarked light-ion fragment field so post-shielding species composition is closer to HZETRN-like results
- **Hemisphere-averaged transport**: 8-angle Lambertian quadrature for isotropic GCR through slab geometry
- **Real solar modulation data**: Downloads Usoskin et al. phi from cosmicrays.oulu.fi with synthetic fallback
- **~100× transport speedup**: Precomputed CSDA factors reused across trajectory days

## Known Simplifications

- Force-field modulation ignores charge-sign-dependent drift (acceptable below 1 GV)
- Transport: CSDA with Jacobian-corrected energy re-binning; benchmarked charged-fragment surrogate instead of full fragmentation transport
- Geometry: hemisphere-averaged 1D slab; no full-body anthropomorphic model
- Neutron cascade: tabulated from HZETRN, not computed from Boltzmann equation
- Mars surface: parameterized from RAD measurements, not computed from atmospheric transport
- Solar modulation distance scaling: blended r^(-0.5) Parker approximation

## References

- Zeitlin, C. et al. (2013). Measurements of energetic particle radiation in transit to Mars on the Mars Science Laboratory. *Science*, 340(6136), 1080-1084.
- Cucinotta, F. A. et al. (2013). Space radiation cancer risk projections and uncertainties. NASA TP-2013-217375.
- Boschini, M. J. et al. (2020). Deciphering the local interstellar spectra of primary cosmic-ray species with HelMod. *ApJS*, 250(2), 27.
- Hassler, D. M. et al. (2014). Mars' surface radiation environment measured with the Curiosity rover. *Science*, 343(6169), 1244797.
- Slaba, T. C. et al. (2014). Optimal shielding thickness for galactic cosmic ray environments. *Space Weather*, 12, 217-227.
- Mrigakshi, A. I. et al. (2013). Estimation of galactic cosmic ray exposure inside spacecraft. *J. Geophys. Res. Space Phys.*, 118, 6633-6643.
- Gleeson, L. J. & Axford, W. I. (1968). Solar modulation of galactic cosmic rays. *ApJ*, 154, 1011.
- Vos, E. E. & Potgieter, M. S. (2015). New modeling of galactic cosmic ray modulation during the minimum of solar cycle 23/24. *ApJ*, 815(2), 119.

## License

MIT
