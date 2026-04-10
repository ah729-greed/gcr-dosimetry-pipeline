# Validation And Uncertainty

This document is the honest status page for the model.

## Maturity By Subsystem

| Subsystem | Current status | What anchors it | Main limitation |
| --- | --- | --- | --- |
| Transit GCR dose totals | `validated surrogate` | MSL RAD transit dose and HZETRN-like envelope | not full Boltzmann or Monte Carlo transport |
| Post-shielding species mix | `benchmarked surrogate` | H/He/HZE comparison against published HZETRN-like fractions | charged fragments are approximate |
| Neutron contribution | `calibrated table model` | Slaba/Mrigakshi/Zeitlin anchor points | not explicit neutron cascade transport |
| Organ dose routing | `physics-informed bridge` | self-shielding depth model + ICRP-60 weighting check | not voxel phantom transport |
| REID | `literature-based risk model` | NASA/Cucinotta formulation | epidemiologic and biology uncertainty remain large |
| Mars surface | `parameterized environment model` | Hassler RAD surface measurements | not atmospheric transport |
| LET / RBE | `equation-validated therapy helper` | OpenTOPAS-RBE equation-level reference cases | not full TOPAS transport benchmarking |

## What Is Validated Right Now

Main script:

```bash
python scripts/validate_pipeline.py
```

Current benchmark snapshot:

- absorbed dose rate: `1.84 mGy/day` vs RAD `1.84`
- dose equivalent rate: `4.80 mSv/day` vs RAD `4.81`
- `Q_eff = 2.60` vs RAD `2.62`
- post-shielding absorbed-dose mix: `H 46.7%`, `He 16.8%`, `HZE 30.9%`

RBE equation check:

```bash
python scripts/validate_rbe.py
```

This confirms that the implemented Wedenberg and McNamara models reproduce the
same equation outputs used in the OpenTOPAS-RBE workflow for fixed reference
cases.

## What Uncertainty Is Already Represented

The current REID Monte Carlo in `gcr.reid` perturbs:

- quality-factor scaling
- ERR scaling
- DDREF
- EAR scaling

This means the project already captures a real part of the biology/risk
uncertainty.

## What Uncertainty Is Not Yet Fully Represented

The following are still mostly handled through calibration, benchmarking, or
qualitative caveats rather than a full ensemble:

- LIS normalization and species composition uncertainty
- solar modulation uncertainty along the trajectory
- charged-fragment production uncertainty
- neutron yield / spectral uncertainty
- Mars surface transport uncertainty

That is why the current project should be described as:

`validated end-to-end surrogate with explicit known approximations`

and not as a fully first-principles radiation transport code.

## Best Next Uncertainty Upgrade

The most useful next step is a proper `physics + biology` ensemble:

1. vary species/LIS normalization
2. vary neutron yield scaling
3. vary REID biological parameters
4. report dose and REID percentile bands together

That would make the risk output much more publication-ready without pretending
the underlying transport is fully exact.
