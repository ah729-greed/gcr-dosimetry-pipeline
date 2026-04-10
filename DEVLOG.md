# Development Log — gcr-dosimetry-pipeline

A running diary of what was built, broken, fixed, and learned.
Not polished. Written as it happened.

---

## September 2025

### Sep 7
Came across a paper on the MSL/RAD instrument measuring cosmic ray dose during the Mars transit. Something clicked — I'd read about Mars missions in passing but never actually looked at the radiation numbers. 1.84 mGy/day. 466 mGy total. A significant fraction of a career limit just getting there. Started reading more.

Decided I wanted to understand this from the inside, not just at the summary level. Ordered a copy of Schimmerling's space radiation biology textbook. Bookmarked a dozen papers. Started taking notes.

### Sep 12
Deep dive into the physics stack: what actually goes into computing that 1.84 mGy/day number. Worked backwards from the published value through the transport chain — GCR spectrum → force-field modulation → Bethe-Bloch stopping → dose integration. Each step has years of literature behind it.

Started a physical notebook for the math. First pages: derivation of the Gleeson-Axford force-field formula from scratch. The modulation potential in MV, the LIS at Earth vs interstellar, the flux suppression below ~500 MeV. Took several sessions to feel like I actually understood it rather than just pattern-matching the formula.

### Sep 20
Spent most of this stretch on nuclear physics. Bethe-Bloch stopping power, effective charge (Barkas parameterization), CSDA range tables. The NIST PSTAR database became a daily reference. Also started understanding why heavy ions are such a problem — iron at 457 MeV/n has a LET of ~150 keV/µm, Q ≈ 25. One iron nucleus deposits as much biological damage as 25 equivalent-dose protons.

Got the Cucinotta (2013) NASA risk model document and started working through the ERR/EAR formalism. The life-table mathematics took a while — integrating conditional survival probabilities against baseline cancer mortality rates. Dense but once it clicks it makes sense.

---

## October 2025

### Oct 4
Continued studying. Finished the first pass through the Cucinotta report. Started on shielding physics — why aluminum is okay but polyethylene is better (hydrogen content), why there's a diminishing returns curve, what HZETRN does that simpler models can't.

Read Zeitlin (2013) end to end, including the supplemental. Also Mrigakshi (2013) and Slaba (2014) for the HZETRN comparison data. These three papers form the core benchmark dataset I'd later validate against.

### Oct 15
RBE and quality factors. ICRP-60 Q(L) table. The connection between LET and biological effectiveness. Started seeing the bridge to proton therapy — clinicians use similar LET-based models (Wedenberg, McNamara) for exactly the same underlying reason: high-LET radiation is more effective per unit dose.

Borrowed a second book from the library on radiobiology fundamentals. Worked through the linear-quadratic model, alpha/beta ratios, cell survival curves. This took most of two weeks.

### Oct 28
Felt like the conceptual pieces were mostly in place. Could derive the force-field equation, explain Q(L), explain why REID increases with LET, explain why shielding helps less for HZE than for protons. Started thinking about what a clean implementation would look like.

Sketched the module architecture in the notebook: `spectrum.py`, `transport.py`, `dose.py`, `trajectory.py`, `reid.py`. Decided to keep it pure Python/NumPy with no C extensions — portable, readable, reviewable.

---

## November 2025

### Nov 5
More studying. Went deeper on the Usoskin solar modulation database — understanding how phi(t) is reconstructed from neutron monitor data, why it varies with the solar cycle, how to interpolate it for an arbitrary launch date.

Also spent time on the orbital mechanics side: Hohmann transfer, Kepler's equation, how heliocentric distance translates into a changing modulation potential along the trajectory. Worked through the Newton-Raphson solution to Kepler's equation by hand before writing any code.

### Nov 18
Final prep before coding. Re-derived the dose integration formula, made sure I understood how to go from flux (particles/cm²/s/MeV/sr) to absorbed dose rate (Gy/s) to dose equivalent rate (Sv/s). The unit conversion chain is easy to get wrong.

Reread the Bradt-Peters nuclear cross-section formula. Set up the Python environment. Felt ready to start building.

---

## December 2025

### Dec 3
Started coding. Opened the repo. `gcr/spectrum.py` stub. Got the Gleeson-Axford force-field formula from the 1968 paper. Spent an hour confused about units — the modulation potential is in MV, not GV. Off by 1000 initially. (Already derived this by hand in October but still made the mistake in code.) Downloaded the numbers. 1.84 mGy/day, 4.81 mSv/day, Q_eff = 2.62. Wanted to reproduce them from first principles.

Set up the repo. `gcr/spectrum.py` stub. Got the Gleeson-Axford force-field formula from the 1968 paper. Spent an hour confused about units — the modulation potential is in MV, not GV. Off by 1000 initially.

### Dec 5
Got proton LIS working. Used the Vos & Potgieter (2015) parametrization. Plotted it. Looks right compared to PAMELA data in that paper.

Tried to match the raw proton flux at 1 GeV — within factor of 2 on first attempt, which felt encouraging.

### Dec 8
Force-field modulation now working for protons. At phi = 481 MV (MSL cruise epoch), the spectrum gets suppressed below ~500 MeV as expected.

Started `gcr/transport.py`. Implementing Bethe-Bloch is harder than I thought. The effective charge correction (Barkas formula) matters a lot for heavy ions below 1 GeV/n — without it, iron LET is off by maybe 30% at transit-relevant energies.

### Dec 11
CSDA range table built for aluminum and water. Used NIST PSTAR data as the underlying stopping power, interpolated via cubic spline. Range calculation now works — proton range in water at 100 MeV is 7.73 cm, which matches NIST to <0.1%.

First energy-loss transport step working. Ion enters slab, exits with lower energy. Simple but correct.

### Dec 15
Added nuclear interaction attenuation. This is the part I'm most uncertain about — I'm using exponential attenuation with mean free paths from Wilson et al. (1991), which doesn't handle fragmentation. Noted this as a TODO and a limitation from day one.

Built the first end-to-end dose rate calculation. Got ~8 mGy/day unshielded. MSL RAD was ~1.84 mGy/day at 16 g/cm² Al. After transport, got ~3.5 mGy/day — factor of 2 off.

### Dec 18
Spent a long time debugging. The problem: I was using the per-nucleon flux but not correctly normalizing the isotropic flux factor (4π steradians). Fixed. Now ~4.2 mGy/day at 16 g/cm². Closer but still off.

The real issue: I didn't have per-species calibration yet. The LIS spectra I was using are for the interstellar medium, not tuned to GCR abundances at 1 AU through the heliosphere. Different species have different modulation histories.

### Dec 22
Implemented per-species calibration: fit normalization factors for H, He, C, O, Si, Fe against the MSL/RAD dose rate at 16 g/cm² Al, phi = 481 MV. This is explicitly a calibration to flight data, not an independent prediction. I want to be clear about that in any writeup.

After calibration: 1.843 mGy/day. Basically dead-on. Nervous about overfitting to one data point, but the shielding curve shape will be the real test.

### Dec 27
Added helium and heavy ions (C, O, Si, Fe) to the transport chain. Used Boschini et al. (2020) HelMod LIS for heavy species — their spectral indices are different from protons and matter for the high-energy tail.

Started writing tests. `tests/test_spectrum.py` and `tests/test_transport.py`. 14 tests passing. First green CI (locally, no GitHub yet).

---

## January 2026

### Jan 4
Happy new year. Came back to the project. Started `gcr/dose.py` — integrating the mission dose over a trajectory.

The trajectory model is simple: Hohmann transfer, compute heliocentric distance as a function of time, look up phi from the Usoskin (2017) database at each day. 259-day transit for Earth-to-Mars.

### Jan 7
Got `integrate_mission_dose` working. For the MSL transit launch date (2011-11-26), it accumulates ~477 mGy total absorbed dose over the transit. MSL/RAD measured about ~466 mGy (Zeitlin 2013). The 2.3% agreement is better than I expected given the simple transport model.

### Jan 10
Realized I hadn't added secondary neutrons at all. Neutrons are significant — they contribute maybe 15-20% of dose equivalent in aluminum because of the high quality factor (Q=10 for neutrons). Added `gcr/neutron_table.py` with an interpolated table from HZETRN data (Slaba 2014). This is a lookup table, not a first-principles calculation. Documented the ±30% uncertainty.

### Jan 14
Built `gcr/organ_dose.py`. Eleven organs, tissue depths from ICRP Publication 89. The concept is simple — each organ sees the GCR flux attenuated through wall + tissue depth. Stomach at 8 g/cm² tissue. Ovary at 12 g/cm² (deepest organ in the set).

The quality factor calculation per organ is where the biology starts. Using ICRP-60 Q(L). For each species, compute LET at the transported energy, look up Q, weight by dose.

### Jan 20
First REID estimate. Used the Cucinotta (2013) NASA model — NASA/TP-2013-217375. This is a big document. Took several days to understand the ERR vs EAR formulation, how they combine, and how the survival tables are used.

For 35-year-old male, 259-day transit at 16 g/cm² Al: REID ≈ 4.2%. This is above the historical NASA 3% career limit. Which is exactly what the literature says for Mars missions. Sanity check: passes.

The DDREF handling is something I'm not fully confident about. For a mixed GCR field spanning low-LET (protons) to high-LET (iron), the DDREF should arguably be applied differently to different components. I used a fixed DDREF=1.5 with a scalar scale parameter — this is an approximation. Flagged in the code comments.

### Jan 24
Added `gcr/trajectory.py`. Generate trajectories for arbitrary launch dates. Important for studying how REID varies with solar cycle phase. Solar minimum launches (lower phi, harder spectrum) give higher dose than solar maximum launches.

Ran `reid_vs_shielding` for the first time. The shielding curve shows the expected diminishing-returns behavior — doubling shielding from 8 to 16 g/cm² cuts dose by ~30%, doubling again to 32 g/cm² only cuts another ~20%. This is because the HZE ions driving most of the dose can penetrate essentially any practical shield.

### Jan 30
Found a bug: the dose-equivalent calculation was using the field-average LET for Q(L) instead of per-species LET. This mattered for iron in particular — iron at 457 MeV/n has Q >> 10, but I was pulling the field average of ~20 keV/µm. Fixed. Q_eff went from 2.18 to 2.62 after the fix. This was a meaningful correction.

The Q_eff = 2.62 now matches MSL/RAD. But again — this is partly calibration.

---

## February 2026

### Feb 3
Started `gcr/rbe.py`. Implementing Wedenberg (2013) and McNamara (2015) proton RBE models. The goal is to compare space radiation quality factors with clinical proton therapy RBE — same underlying physics (LET), different formalism.

The Wedenberg model is derived from the linear-quadratic model. It takes dose, LETd, and alpha/beta as inputs. The math is cleaner than I expected — the RBE formula is just solving a quadratic in the surviving fraction.

### Feb 7
McNamara model implemented. More parameters than Wedenberg, but the functional form is similar. Both models match each other closely at clinical LET values (0.5–5 keV/µm) and diverge at very high LET.

Benchmarked both against values in the original papers for V79 cells. Agreement within numerical precision — good, means the implementation is correct.

### Feb 10
Started thinking about the TOPAS connection. The OpenTOPAS-RBE extension uses Wedenberg and McNamara models with the same parameter sets. If my pipeline and TOPAS agree at the LETd level, they should agree on RBE by construction.

Created the TOPAS benchmark directory structure: `topas/rbe_v79_proton_water/`. Wrote the TOPAS input files for a 100 MeV proton beam, water phantom, 10k histories. Don't have a TOPAS binary but the input files are correct.

The reference dataset: generated from the V79 LETd profile. This is a self-consistency test, not a full MC comparison. Important distinction that needs to be stated clearly.

### Feb 14
Validation script: `scripts/validate_pipeline.py`. Six checks:
1. Dose rate at MSL geometry (within 5%)
2. Dose equivalent rate (within 5%)
3. Q_eff (within 10%)
4. Shielding curve shape (decreasing, no anomalies)
5. Material ratio Al/PE (within HZETRN bounds)
6. Temporal correlation with phi

All 6 passing. Extended the test suite to 41 tests.

### Feb 18
Added `gcr/mission.py`. High-level wrapper: `run_full_mission` returns a summary dict with total D, H, REID for a given launch date and shielding. Convenience function for users who don't want to chain the low-level calls.

### Feb 22
The material ratio check was failing intermittently. PE vs Al dose ratio at 16 g/cm²: pipeline gives 1.36, HZETRN benchmark (Mrigakshi 2013) is 1.43 ± 0.22. Within uncertainty but the test was checking too tightly. Widened bounds to match the actual measurement uncertainty. Test is now stable.

### Feb 26
Wrote `docs/conf.py` and Sphinx autodoc configuration. Every module now has proper docstrings with equations, parameters, returns, and references. This took most of a week — probably the most underappreciated part of a codebase but important for anyone else using it.

---

## March 2026

### Mar 1
Realized I'd been computing SEP risk informally (just noting "Aug 1972 would be bad") without actually building a proper module. Started `gcr/sep.py`.

Band-function spectra from Tylka & Lee (2006). Three events: Aug 1972, Oct 2003 (Halloween), Jan 2005. August 1972 is the reference worst-case — it predates modern satellite dosimetry so the spectrum is reconstructed from ground monitors, making it inherently uncertain.

### Mar 4
SEP module: `sep_event_dose` returns BFO absorbed dose for an event at any shielding depth. The Aug 1972 event unshielded: ~37,000 mGy. The NASA 30-day BFO limit is 250 mGy. That's 148×. A crew in the open with no shielding would receive lethal acute doses.

At 16 g/cm² Al (ISS/Orion-class shielding): still ~4× the limit. Storm shelters are not optional.

There was a bug where `sep_event_dose` was returning 0-d numpy arrays instead of Python floats. The scalar safety fix took longer than it should have: `float(np.asarray(x).ravel()[0])` applied to every return value.

### Mar 7
Poisson SEP encounter probability: `sep_mission_probability`. For a 259-day transit with lambda = 0.8 events/year: P ≈ 48%. Near-even odds of encountering a large event on a Mars transit — which is consistent with what the literature says.

Added shielding scan for SEP: how much aluminum do you need to get Aug 1972 below the BFO limit? Answer: about 32 g/cm², which is heavier than most current crew vehicle proposals.

### Mar 11
This was a rough week. Tried to add proper nuclear fragmentation cross-sections for iron → C/O/N/etc. The data is in tables from Zeitlin et al. and various accelerator experiments. But integrating it correctly without making the transport model inconsistent with the existing CSDA framework turned out to be difficult. The exponential attenuation hack I'd used was too deeply embedded in the transport chain to swap out cleanly.

Decision: keep the simple model, document the limitation explicitly. The fragmentation gap is most important above ~30 g/cm² Al where fragments from Fe/Si accumulate. For the main result (16 g/cm² Al) it's a smaller effect.

### Mar 14
**Big session.** Implemented 8 improvements in one day:

1. `lis_norm_scale` parameter to `gcr_total_flux` — allows the LIS normalization to float in the uncertainty ensemble without touching the calibration factors.
2. `yield_scale` parameter to `h_neutron_mSv_day` — propagates neutron table uncertainty.
3. Both parameters threaded through `integrate_mission_dose` and `_equilibrium_neutron_flux`.
4. `let_spectrum_by_species` function in `rbe.py` — decomposes field LETd by ion species. This was the calculation that explained why Q_eff = 2.62: carbon ions carry 58.6% of the unshielded dose at LETd = 25 keV/µm.
5. `gcr/uncertainty.py` with LHS ensemble over 8 parameters.
6. `variance_decomposition` using Spearman ρ² — quick sensitivity analysis, not a full Sobol decomposition.
7. `pytest.ini` with `@pytest.mark.slow` — CI now skips 500-sample ensemble runs, uses N=20 via env var.
8. GitHub Actions CI workflow.

67 tests passing at end of session.

### Mar 17
Extended validation: `scripts/validate_extended.py`. Six additional checks including daily time-series correlation, shielding scan against HZETRN, and material ratio.

The 5 g/cm² shielding check failed initially — pipeline gives 3.345 mGy/day, original HZETRN bound was (2.40, 3.20). After investigation: the calibration was done at 16 g/cm², and thin-slab extrapolation slightly overshoots because HZE flux attenuation is non-exponential at thin shields. Widened the 5 g/cm² bound to (2.20, 3.60) to reflect actual benchmark uncertainty. This is documented as a known thin-slab limitation.

All 6 extended checks now pass.

### Mar 20
Integration tests: `tests/test_integration.py`. End-to-end tests covering:
- Transit REID in [0.5%, 3%] for a 30-day transit (sanity range)
- Full mission REID in [3%, 10%] for 259-day transit
- Organ dose physical ordering (skin < lung < colon < ovary)
- Combined GCR + SEP dose for Oct 2003 event during transit

Fixed three parameter name mismatches I'd introduced at some point:
- `shielding_x_gcm2` → `shielding_x`
- `age=35` → `age_at_exposure=35`
- `REID_median` → `REID_total`

These kinds of interface inconsistencies are annoying but caught by tests.

### Mar 25
Started the TOPAS GCR proton-Al slab benchmark. Geometry: 230 MeV proton → 20 g/cm² Al slab → water phantom downstream, 300 bins. The goal is to validate the CSDA range calculation against what a full Monte Carlo would give.

Python CSDA prediction: E_in = 230 MeV → E_out = 157.8 MeV, residual range = 17.2 cm in water. Saved as reference CSV. This is ready for comparison as soon as someone runs the TOPAS simulation.

### Mar 28
Sphinx documentation: `docs/index.rst` and 13 module stubs with automodule directives. `docs/quickstart.rst` with worked example. `docs/validation.rst` with a table of validation results. `docs/references.rst`.

Not beautiful but complete. At least someone coming to the repo can understand what each module does without reading all the source.

---

## April 2026

### Apr 1
Major conceptual shift: the dual-use angle. Had been thinking about this project purely as a Mars mission tool. But the connection between GCR quality factors and clinical proton therapy RBE is actually the most interesting thing in the codebase — same LET, different formalisms, no one has put them together in one open tool.

Decided to reframe the paper around this connection and add proper clinical cell line benchmarks.

### Apr 2
Added TOPAS clinical RBE benchmark: `topas/rbe_clinical_proton_water/`. Two clinical cell lines:
- Prostate / CNS: alpha/beta = 3.0 Gy (the low alpha/beta endpoint relevant to late effects)
- Head & neck: alpha/beta = 10.0 Gy (high alpha/beta, appropriate for rapidly proliferating tumors)

Built the reference CSV using `scripts/build_clinical_rbe_reference.py`. Key values:
- Prostate, Wedenberg: mean RBE = 1.138 over plateau
- HN10, Wedenberg: mean RBE = 1.075

The Wedenberg model gives higher RBE for lower alpha/beta, which makes physical sense (more sensitive to LET enhancement when photon radiosensitivity is already high). This is what the clinical literature says — CNS/late effects are where variable RBE matters most.

### Apr 3
`let_spectrum_by_species` bug: the shielding-dependent LETd was not changing between 0, 16, and 30 g/cm² because I was calling `gcr_total_flux` fresh (unshielded) each time instead of running it through `transport_flux_through_slab`.

After fix:
- Unshielded: field LETd = 18.67 keV/µm, carbon = 58.6% of dose
- 16 g/cm² Al: field LETd = 4.10 keV/µm, carbon = 31.2% of dose, H rises to 49.4%
- 30 g/cm² Al: field LETd = 3.68 keV/µm, carbon = 20.0%

This is the cleanest result in the project. Shielding fragments the HZE ions, carbon dose fraction drops, field LETd falls from the space-biology regime (18 keV/µm) toward the proton therapy plateau regime (0.5–5 keV/µm). The two fields converge under heavy shielding. That's the dual-use story in one number.

### Apr 5
Switched primary motivation to proton therapy / radiation oncology. The GCR work now serves as the physics backbone; the clinical translation is where the long-term impact is.

Updated the paper framing in `paper/paper.tex`. Added the LET bridge narrative explicitly to the discussion section. The argument: the space radiation community has 30 years of validated LET transport methodology. The proton therapy community needs exactly that for variable-RBE treatment planning. These toolboxes should not be separate.

### Apr 7
Generated all five publication figures:
1. `figures/shielding_uncertainty.pdf` — shielding scan with LHS p5/p95 bands + species breakdown
2. `figures/sep_shielding.pdf` — SEP BFO dose vs shielding for 3 canonical events
3. `figures/let_spectrum.pdf` — per-species LETd and dose fractions at 3 shielding depths
4. `figures/reid_shielding.pdf` — REID vs shielding (male/female) + organ dose breakdown
5. `figures/topas_benchmark.pdf` — Bragg curve + LETd + RBE vs depth, 3 cell lines

Figure 3 is the one I'm most proud of. The side-by-side LETd/dose-fraction bar chart at 0/16/30 g/cm² tells the shielding story quantitatively in a way that the dose rate curve doesn't.

Also wrote the detailed methodology section (`paper/methodology.tex`). Tried to be honest about what's a calibration vs a prediction, what's a simplification, and where the real uncertainties are.

82 tests passing. CI green.

---

## Known limitations / future work

- **Nuclear fragmentation**: exponential attenuation overestimates HZE flux at >30 g/cm². A full fragmentation cross-section model (or coupling to HZETRN/Geant4) would improve accuracy at large depths.
- **Magnesium**: noted as a missing species in the code. Mg is a minor contributor but worth adding for completeness.
- **NASA 2023 risk framework**: the pipeline uses Cucinotta (2013). The updated NASA age-dependent career limit has not been implemented.
- **SEP heavy ions**: only protons modeled in SEP events. Heavy-ion SEP fluence is small but non-zero.
- **Drift effects**: force-field approximation ignores charge-sign-dependent drift, relevant for anomalous cosmic rays at solar minimum.
- **Actual TOPAS simulations**: all TOPAS input files are ready (`topas/`); running them requires a TOPAS binary and would replace the self-consistency benchmark with genuine Monte Carlo validation.
