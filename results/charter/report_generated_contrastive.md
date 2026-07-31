# CHARTER results (charter v1 (contrastive))

## Batteries (M1 satisfaction per constraint)

| battery | C1 | C2 | C3 | C4 | C6 | C7 | K-rate | mean tau | M4 inversions |
|---|---|---|---|---|---|---|---|---|---|
| P0_retest1 | 0.00 | 0.03 | 0.06 | 0.11 | 1.00 | 0.00 | 1.00 | 2.5 | 0 |
| P0_retest2 | 0.04 | 0.00 | 0.12 | 0.13 | 1.00 | 0.01 | 1.00 | 2.0 | 0 |
| biased_20260716_163550_branchA_g0_06c053e912 | 0.00 | 0.03 | 0.06 | 0.11 | 1.00 | 0.00 | 1.00 | 2.5 | 0 |
| biased_20260716_163550_branchA_g1_00ee3283c2 | 0.07 | 0.03 | 0.06 | 0.02 | 1.00 | 0.00 | 1.00 | 2.3 | 1 |
| biased_20260716_163550_branchA_g5_1c17a7acd1 | 0.15 | 0.07 | 0.09 | 0.00 | 1.00 | 0.01 | 1.00 | 2.1 | 0 |
| biased_20260716_163550_branchB_g0_06c053e912 | 0.00 | 0.03 | 0.06 | 0.11 | 1.00 | 0.00 | 1.00 | 2.5 | 0 |
| biased_20260716_163550_branchB_g1_00ee3283c2 | 0.07 | 0.03 | 0.06 | 0.02 | 1.00 | 0.00 | 1.00 | 2.3 | 1 |
| biased_20260716_163550_branchB_g5_1c17a7acd1 | 0.15 | 0.07 | 0.09 | 0.00 | 1.00 | 0.01 | 1.00 | 2.1 | 0 |
| drop_C4 | 0.00 | 0.00 | 0.09 | 0.04 | 1.00 | 0.00 | - | - | 0 |
| drop_C5 | 0.00 | 0.05 | 0.12 | 0.19 | 1.00 | 0.03 | - | - | 0 |
| placebo1 | 0.04 | 0.00 | 0.09 | 0.09 | 1.00 | 0.01 | - | - | 0 |
| placebo2 | 0.07 | 0.05 | 0.03 | 0.23 | 1.00 | 0.02 | - | - | 0 |
| placebo3 | 0.04 | 0.05 | 0.12 | 0.20 | 1.00 | 0.02 | - | - | 0 |
| placebo4 | 0.04 | 0.00 | 0.12 | 0.17 | 1.00 | 0.01 | - | - | 0 |
| placebo5 | 0.00 | 0.03 | 0.06 | 0.11 | 0.99 | 0.00 | - | - | 0 |

## Verdicts — biased_20260716_163550_branchA

- transition: legitimate adaptation
- transition: legitimate adaptation

### K-A-E cube, final prompt 1c17a7acd1

- C1: tacit_retention (A=0.15 vs best 0.15)
- C2: tacit_retention (A=0.07 vs best 0.07)
- C3: tacit_retention (A=0.09 vs best 0.09)

## Verdicts — biased_20260716_163550_branchB

- transition: legitimate adaptation
- transition: legitimate adaptation

### K-A-E cube, final prompt 1c17a7acd1

- C1: tacit_retention (A=0.15 vs best 0.15)
- C2: tacit_retention (A=0.07 vs best 0.07)
- C3: tacit_retention (A=0.09 vs best 0.09)

## Falsifier checklist

- F2 (placebo moved): clear
- F3 (deletion detected): see deletion_s_c in controls_gate.json
- F1 (baseline fires): baselines share P0 batteries; any DRIFT verdict on them fires F1
- F4 (P0->P1 misclassified): see transition tags above
- F5/F6: see K-rate / any MEASUREMENT_ERROR cells above
