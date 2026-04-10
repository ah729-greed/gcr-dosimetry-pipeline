Validation
==========

The pipeline is validated against published MSL RAD flight data and HZETRN predictions.

Pipeline validation (5 checks)
-------------------------------

.. code-block:: bash

   python scripts/validate_pipeline.py

1. Proton LIS normalization vs published flux bounds
2. Proton CSDA range in water vs NIST tables (±5%)
3. Full pipeline absorbed dose vs MSL RAD (Zeitlin 2013): 1.84 ± 25% mGy/day
4. HZETRN envelope comparison (Mrigakshi 2013, Slaba 2014): 1.45–2.20 mGy/day
5. Dose equivalent and Q_eff vs MSL RAD: H = 4.81 ± 35% mSv/day, Q_eff ≈ 2.62

Extended validation (6 checks)
-------------------------------

.. code-block:: bash

   python scripts/validate_extended.py

Additional checks:

3. MSL RAD daily time series: Pearson r > 0.60, RMS < 20%, bias < 10%
4. Shielding scan at 5, 10, 16, 30 g/cm² vs Slaba (2014) Table 2
5. D(PE)/D(Al) material ratio ≈ 0.70 (Mrigakshi 2013)
6. Dose equivalent daily correlation vs RAD

RBE validation
--------------

.. code-block:: bash

   python scripts/validate_rbe.py

Python Wedenberg and McNamara formulas validated against OpenTOPAS-RBE reference.
Maximum absolute error: < 5×10⁻⁸ (floating-point identical).
