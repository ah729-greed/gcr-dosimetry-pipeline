# GCR Dosimetry Pipeline

An open-source Python package for estimating galactic cosmic ray (GCR) radiation exposure and cancer risk on crewed deep-space missions. It integrates GCR spectrum generation, CSDA slab transport, organ-specific REID estimation, Solar Energetic Particle acute dosimetry, and Latin Hypercube uncertainty quantification into one reproducible workflow.

This repository accompanies the manuscript:

> Shah, A. H. (2025). *An open-source GCR dosimetry pipeline for Mars mission risk assessment: organ-specific REID, SEP acute hazard, and dual-use proton therapy RBE benchmarking.* Submitted to *Life Sciences in Space Research*.

The point of this tool is not to claim new physics — HZETRN and Geant4 do the transport better. The point is that those tools are closed, hard to install, and don't come with uncertainty quantification built in. This one does, and anyone with Python can run it.

---

## Quick Start

```bash
git clone https://github.com/aryanhshah8/gcr-dosimetry-pipeline
cd gcr-dosimetry-pipeline
pip install -e .
python scripts/download_data.py
python scripts/validate_pipeline.py
```

To reproduce the paper figures:

```bash
python scripts/plot_shielding_uncertainty.py   # Figure 2
python scripts/plot_let_spectrum.py            # Figure 3
python scripts/plot_sep_shielding.py           # Figure 4
python scripts/plot_reid_shielding.py          # Figure 5
python scripts/plot_topas_benchmark.py         # Figure 6
```

Full N=500 uncertainty ensemble (~90 min on a single core):

```bash
python scripts/validate_extended.py
```

A reduced N=20 version runs in under 2 minutes and is what CI uses:

```bash
UNCERTAINTY_SAMPLES=20 python scripts/validate_extended.py
```

---

## What it does

```
spectrum.py  →  trajectory.py  →  transport.py  →  dose.py  →  reid.py  →  mission.py

GCR flux         Hohmann orbit      CSDA energy     Absorbed    Cancer risk
(Boschini 2020   + Usoskin phi      loss + nuclear  dose, dose  (Cucinotta 2013
 per-species LIS   along transfer    attenuation     equivalent  ERR+EAR model +
 + Gleeson-Axford  ellipse           + HZETRN        (ICRP-60)   CDC 2020 life
 force field)                        neutron table)              tables)
```

The RBE module (`rbe.py`) runs the Wedenberg (2013) and McNamara (2015) proton RBE models using the same LET infrastructure as the GCR quality factor calculation — so you can directly compare quality factors across space and clinical radiation contexts from one codebase.

---

## Validation

Calibrated to MSL/RAD cruise-phase dosimetry, independently validated against shielding curve shape, Al/PE material ratio, and temporal modulation:

| Quantity | Pipeline | Reference | Source | Notes |
|---|---|---|---|---|
| Shielding slope (5–30 g/cm²) | within envelope | HZETRN benchmark | Slaba (2014) | Independent |
| Al/PE dose ratio at 16 g/cm² | 1.36 | 1.43 ± 0.22 | Mrigakshi (2013) | Independent |
| Daily r(dose, φ) | >0.80 | — | Zeitlin (2013) | Independent |
| Dose rate at 16 g/cm² Al | 1.843 mGy/day | 1.84 ± 0.33 | Zeitlin (2013) | **Calibration** |
| Q_eff at 16 g/cm² Al | 2.60 | 2.62 ± 0.14 | Zeitlin (2013) | **Calibration** |
| V79 RBE (Wedenberg, plateau) | 1.053 | 1.053 | TOPAS-nBio | Self-consistency |

The 0.05% dose rate match is a result of the calibration — not an independent prediction. The independent checks are the shielding slope, the material ratio, and the temporal correlation.

**Per-species dose fractions at the calibration geometry** (16 g/cm² Al, φ = 481 MV):

| Charge group | Pipeline | NSRL GCR reference† |
|---|---|---|
| Z=1 (protons) | 46.7% | 73.3% |
| Z=2 (helium) | 16.8% | 19.2% |
| Z>2 (HZE) | 30.9% | 7.6% |

†Slaba et al. (2016), 20 g/cm² Al, solar minimum.

The HZE fraction is about 4× higher than the reference. This is a known consequence of fitting six normalization factors to one total dose measurement — the optimizer has too many degrees of freedom and the result is not physically constrained at the species level. A proper species-resolved calibration against MSL/RAD per-species data is the obvious next step.

---

## Uncertainty quantification

The LHS ensemble varies eight physics and radiobiological parameters simultaneously. Key results for a 35-year-old male, 259-day Earth–Mars transit at 16 g/cm² aluminum:

- Median REID: **5.0%** (p5–p95: 1.3%–16.9%)
- Q-factor scale accounts for **76%** of REID variance
- DDREF accounts for **7%**
- All GCR physics parameters combined: **<9%** of REID variance
- Solar modulation (phi_scale): **3.5%** of REID variance but **72%** of absorbed dose variance

The main takeaway: improving GCR transport physics will narrow dose uncertainty but won't move the needle on cancer risk estimates until the high-LET radiobiology is better understood.

---

## Known limitations

- **No nuclear fragmentation transport.** Heavy ions are exponentially attenuated — the pipeline doesn't track secondary lighter ions from fragmentation reactions. Comparisons with full transport codes suggest the HZE quality factor at 16 g/cm² is overestimated by roughly 15–25% as a result.
- **Six GCR species only.** Magnesium and other minor species are absent; their combined contribution is estimated at <5% of total dose.
- **Slab geometry.** The spacecraft is a uniform aluminum slab. Real geometries need ray-tracing.
- **Cucinotta (2013) REID model.** The NASA 2023 age- and sex-dependent career limit framework is not implemented.
- **TOPAS comparisons.** V79 agreement is an independent check against TOPAS-nBio reference data. Prostate and H&N comparisons are self-consistency only — no external experimental data were used.

---

## Running the tests

```bash
pytest                                 # 82 unit tests
python scripts/validate_pipeline.py   # dose rate, Q_eff, Al/PE ratio
python scripts/validate_extended.py   # LHS ensemble + variance decomposition
python scripts/validate_rbe.py        # Wedenberg and McNamara vs TOPAS-nBio
```

No proprietary datasets are required. Everything needed is in `data/`.

---

## Citation

If you use this code, please cite:

```
Shah, A. H. (2025). An open-source GCR dosimetry pipeline for Mars mission
risk assessment: organ-specific REID, SEP acute hazard, and dual-use proton
therapy RBE benchmarking. Life Sciences in Space Research (submitted).
```

---

## References

- Zeitlin et al. (2013). Measurements of energetic particle radiation in transit to Mars. *Science* 340, 1080–1084.
- Cucinotta et al. (2013). Space radiation cancer risk projections and uncertainties. NASA/TP-2013-217375.
- Slaba et al. (2014). Optimal shielding thickness for galactic cosmic ray environments. *Space Weather* 12, 217–227.
- Slaba et al. (2016). Reference field specification and preliminary beam selection strategy for accelerator-based GCR simulation. *Life Sci. Space Res.* 8, 52–67.
- Boschini et al. (2020). Deciphering the local interstellar spectra of primary cosmic-ray species with HelMod. *ApJS* 250, 27.
- Mrigakshi et al. (2013). Estimation of galactic cosmic ray exposure inside spacecraft. *J. Geophys. Res.* 118, 6633–6643.
- Wedenberg et al. (2013). A model for the relative biological effectiveness of protons. *Acta Oncol.* 52, 580–588.
- McNamara et al. (2015). A phenomenological relative biological effectiveness model for proton therapy. *Phys. Med. Biol.* 60, 8399.
- Gleeson & Axford (1968). Solar modulation of galactic cosmic rays. *ApJ* 154, 1011.
- Vos & Potgieter (2015). New modeling of galactic proton modulation during solar minimum. *ApJ* 815, 119.

---

## License

MIT
