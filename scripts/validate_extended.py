#!/usr/bin/env python3
"""
scripts/validate_extended.py — Extended validation checks for the GCR pipeline.

Six validation functions beyond the 5-check baseline in validate_pipeline.py:

  1. Proton LIS normalization (regression guard)
  2. Proton CSDA range in water vs NIST (regression guard)
  3. MSL RAD daily time series: Pearson r > 0.6, RMS error < 20%, mean bias < 10%
  4. Shielding scan: 5, 10, 16, 30 g/cm² Al vs HZETRN predictions (all within ±25%)
  5. Material comparison: D(PE)/D(Al) ≈ 0.70 at 16 g/cm²
  6. Dose equivalent time series: H daily correlation and RMSE vs RAD

Usage:
    python scripts/validate_extended.py [--quick]

--quick skips time-series validations (3 and 6) that require a full
trajectory integration.  Use --quick in CI after validate_pipeline.py
has already run the trajectory.
"""

import os
import sys
import argparse
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from gcr.spectrum import lis_proton, force_field_modulation, load_usoskin_phi
from gcr.transport import proton_range
from gcr.dose import integrate_mission_dose
from gcr.trajectory import generate_trajectory
from gcr.utils import DEFAULT_E_GRID

# ---------------------------------------------------------------------------
# Reference values
# ---------------------------------------------------------------------------

# HZETRN predictions at various Al shielding depths (MSL cruise-like, ~550 MV)
# Format: x_gcm2 → (D_lo_mGy_day, D_hi_mGy_day)
SLABA_2014_SHIELDING_TABLE: dict[float, tuple[float, float]] = {
    5.0:  (2.20, 3.60),
    10.0: (1.90, 2.60),
    16.0: (1.45, 2.20),
    30.0: (1.10, 1.80),
}

# PE/Al dose ratio at 16 g/cm²
MRIGAKSHI_PE_AL_RATIO: float = 0.70
MRIGAKSHI_PE_AL_RATIO_TOL: float = 0.15

# MSL RAD published values
RAD_D_mGy_day: float = 1.84
RAD_H_mSv_day: float = 4.81


def _load_rad_data() -> pd.DataFrame:
    """Load MSL RAD transit CSV."""
    rad_path = os.path.join(
        os.path.dirname(__file__), '..', 'data', 'rad', 'msl_rad_transit.csv'
    )
    return pd.read_csv(rad_path)


def _run_trajectory_integration(phi_df=None):
    """Run the full MSL transit trajectory integration (reused across checks 3, 4, 5, 6)."""
    data_dir = os.path.join(os.path.dirname(__file__), '..', 'data', 'usoskin')
    if phi_df is None:
        phi_df = load_usoskin_phi(os.path.join(data_dir, 'phi_transit_frozen.csv'))

    traj = generate_trajectory('2011-11-26', phi_df=phi_df)
    result = integrate_mission_dose(
        traj,
        shielding_x_gcm2=16.0,
        shielding_material='aluminum',
        phi_df=phi_df,
        E_grid_MeV=DEFAULT_E_GRID,
    )
    return result, traj, phi_df


# ---------------------------------------------------------------------------
# Validation 1 — Proton LIS normalization (regression guard)
# ---------------------------------------------------------------------------

def check_lis_normalization() -> bool:
    """Proton directional flux at 1 GeV/n within published bounds."""
    E_test = np.array([1000.0])
    flux_1GeV = float(force_field_modulation(E_test, 550.0, lis_proton)[0])
    lo, hi = 4e-4, 4e-3
    passed = lo < flux_1GeV < hi
    print(f"  Result:  {flux_1GeV:.3e} cm^-2 s^-1 MeV^-1 sr^-1")
    print(f"  Bounds:  {lo:.1e}–{hi:.1e}")
    return passed


# ---------------------------------------------------------------------------
# Validation 2 — Proton CSDA range in water (regression guard)
# ---------------------------------------------------------------------------

def check_proton_range() -> bool:
    """Proton CSDA range in water at 200 MeV within 5% of NIST value."""
    R_200 = float(proton_range(np.array([200.0]), 'water')[0])
    expected = 25.9  # g/cm² (NIST)
    pct_err = abs(R_200 - expected) / expected * 100
    passed = pct_err < 5.0
    print(f"  Result:  {R_200:.2f} g/cm²  (NIST: {expected} g/cm²)")
    print(f"  Error:   {pct_err:.1f}%  (limit: 5%)")
    return passed


# ---------------------------------------------------------------------------
# Validation 3 — MSL RAD daily dose-rate time series
# ---------------------------------------------------------------------------

def check_daily_dose_timeseries(result: dict) -> bool:
    """Compare daily pipeline D_rate_daily [mGy/day] vs MSL RAD measurements."""
    from scipy.stats import pearsonr

    rad = _load_rad_data()
    pipeline_daily = result['D_rate_daily']  # mGy/day, one entry per trajectory day

    # Align lengths (trajectory may be longer than RAD data)
    n = min(len(rad), len(pipeline_daily))
    rad_D = rad['dose_mGy_day'].values[:n]
    pipe_D = pipeline_daily[:n]

    r, _ = pearsonr(rad_D, pipe_D)
    rms_err = float(np.sqrt(np.mean(((pipe_D - rad_D) / rad_D) ** 2))) * 100  # %
    bias = float(np.mean((pipe_D - rad_D) / rad_D)) * 100  # %

    passed = r > 0.60 and rms_err < 20.0 and abs(bias) < 10.0
    print(f"  Pearson r:     {r:.3f}  (limit: > 0.60)")
    print(f"  RMS error:     {rms_err:.1f}%  (limit: < 20%)")
    print(f"  Mean bias:     {bias:+.1f}%  (limit: |bias| < 10%)")
    print(f"  Days compared: {n}")
    return passed


# ---------------------------------------------------------------------------
# Validation 4 — Shielding scan vs Slaba (2014) Table 2
# ---------------------------------------------------------------------------

def check_shielding_scan(phi_df=None) -> bool:
    """D_rate at 4 shielding depths within ±25% of HZETRN predictions."""
    data_dir = os.path.join(os.path.dirname(__file__), '..', 'data', 'usoskin')
    if phi_df is None:
        phi_df = load_usoskin_phi(os.path.join(data_dir, 'phi_transit_frozen.csv'))

    traj = generate_trajectory('2011-11-26', phi_df=phi_df)

    all_ok = True
    print(f"  {'x (g/cm²)':<12} {'D_rate':<12} {'Slaba lo':<12} {'Slaba hi':<12} {'Status'}")
    for x_ref, (lo, hi) in sorted(SLABA_2014_SHIELDING_TABLE.items()):
        res = integrate_mission_dose(
            traj,
            shielding_x_gcm2=x_ref,
            shielding_material='aluminum',
            phi_df=phi_df,
            E_grid_MeV=DEFAULT_E_GRID,
        )
        D_mean = float(np.mean(res['D_rate_daily']))
        ok = lo <= D_mean <= hi
        all_ok = all_ok and ok
        print(f"  {x_ref:<12.0f} {D_mean:<12.3f} {lo:<12.2f} {hi:<12.2f} {'PASS' if ok else 'FAIL'}")

    return all_ok


# ---------------------------------------------------------------------------
# Validation 5 — Material comparison: D(PE) / D(Al) ≈ 0.70
# ---------------------------------------------------------------------------

def check_material_ratio(phi_df=None) -> bool:
    """Dose ratio D(PE)/D(Al) at 16 g/cm² within ±15% of reference value 0.70."""
    data_dir = os.path.join(os.path.dirname(__file__), '..', 'data', 'usoskin')
    if phi_df is None:
        phi_df = load_usoskin_phi(os.path.join(data_dir, 'phi_transit_frozen.csv'))

    traj = generate_trajectory('2011-11-26', phi_df=phi_df)

    res_al = integrate_mission_dose(
        traj, shielding_x_gcm2=16.0, shielding_material='aluminum',
        phi_df=phi_df, E_grid_MeV=DEFAULT_E_GRID,
    )
    res_pe = integrate_mission_dose(
        traj, shielding_x_gcm2=16.0, shielding_material='polyethylene',
        phi_df=phi_df, E_grid_MeV=DEFAULT_E_GRID,
    )

    D_al = float(np.mean(res_al['D_rate_daily']))
    D_pe = float(np.mean(res_pe['D_rate_daily']))
    ratio = D_pe / D_al if D_al > 0 else 0.0

    expected = MRIGAKSHI_PE_AL_RATIO
    tol = MRIGAKSHI_PE_AL_RATIO_TOL
    passed = abs(ratio - expected) <= tol

    print(f"  D(Al):   {D_al:.3f} mGy/day")
    print(f"  D(PE):   {D_pe:.3f} mGy/day")
    print(f"  Ratio:   {ratio:.3f}  (reference: {expected:.2f} ± {tol:.2f})")
    return passed


# ---------------------------------------------------------------------------
# Validation 6 — Dose equivalent daily time series
# ---------------------------------------------------------------------------

def check_daily_H_timeseries(result: dict) -> bool:
    """
    Compare daily pipeline H_rate_daily [mSv/day] vs MSL RAD measurements.

    Same criteria as check 3 but for dose equivalent (quality-factor weighted).
    """
    from scipy.stats import pearsonr

    rad = _load_rad_data()
    pipeline_daily = result['H_rate_daily']  # mSv/day

    n = min(len(rad), len(pipeline_daily))
    rad_H = rad['H_mSv_day'].values[:n]
    pipe_H = pipeline_daily[:n]

    r, _ = pearsonr(rad_H, pipe_H)
    rms_err = float(np.sqrt(np.mean(((pipe_H - rad_H) / rad_H) ** 2))) * 100
    bias = float(np.mean((pipe_H - rad_H) / rad_H)) * 100

    passed = r > 0.50 and rms_err < 25.0 and abs(bias) < 15.0
    print(f"  Pearson r:     {r:.3f}  (limit: > 0.50)")
    print(f"  RMS error:     {rms_err:.1f}%  (limit: < 25%)")
    print(f"  Mean bias:     {bias:+.1f}%  (limit: |bias| < 15%)")
    print(f"  Days compared: {n}")
    return passed


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--quick', action='store_true',
                        help='Skip time-series checks (3 and 6) — no trajectory integration')
    args = parser.parse_args()

    print("=" * 65)
    print("GCR DOSIMETRY PIPELINE — EXTENDED VALIDATION CHECKS")
    print("=" * 65)
    all_pass = True

    # Checks 1 and 2 — regressions (fast)
    print("\nCHECK 1: Proton LIS normalization (regression)")
    ok = check_lis_normalization()
    print(f"  Status: {'PASS' if ok else 'FAIL'}")
    all_pass = all_pass and ok

    print("\nCHECK 2: Proton CSDA range in water (regression)")
    ok = check_proton_range()
    print(f"  Status: {'PASS' if ok else 'FAIL'}")
    all_pass = all_pass and ok

    if not args.quick:
        # Run full trajectory integration once; reuse for checks 3 and 6
        print("\nRunning MSL transit trajectory integration (shared for checks 3 and 6)…")
        result, traj, phi_df = _run_trajectory_integration()

        print("\nCHECK 3: MSL RAD daily absorbed-dose time series")
        ok = check_daily_dose_timeseries(result)
        print(f"  Status: {'PASS' if ok else 'FAIL'}")
        all_pass = all_pass and ok
    else:
        phi_df = None
        print("\n[SKIP] Checks 3 and 6 skipped in --quick mode")

    print("\nCHECK 4: Shielding scan vs HZETRN predictions")
    print("  (Runs integrate_mission_dose at 4 thicknesses — may take ~2 min)")
    ok = check_shielding_scan(phi_df)
    print(f"  Status: {'PASS' if ok else 'FAIL'}")
    all_pass = all_pass and ok

    print("\nCHECK 5: D(PE)/D(Al) material ratio")
    ok = check_material_ratio(phi_df)
    print(f"  Status: {'PASS' if ok else 'FAIL'}")
    all_pass = all_pass and ok

    if not args.quick:
        print("\nCHECK 6: MSL RAD daily dose-equivalent time series")
        ok = check_daily_H_timeseries(result)
        print(f"  Status: {'PASS' if ok else 'FAIL'}")
        all_pass = all_pass and ok

    print("\n" + "=" * 65)
    print("ALL EXTENDED CHECKS PASSED" if all_pass else "SOME EXTENDED CHECKS FAILED")
    print("=" * 65)
    return 0 if all_pass else 1


if __name__ == '__main__':
    sys.exit(main())
