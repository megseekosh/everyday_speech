# Re-running the CDS analyses with the corrected tCDS classifier

## What went wrong

The CDS/ODS labels in `dataframes/everyday_cds_ods.csv` came from the online classifier
(https://kachergis.shinyapps.io/classify_cds_ods/), driven by `1_pipeline.py` in 2023. From August 2022
until November 2026 that app served a stale tCDS model. That model had been trained with clock time as
an extra first feature (9 features). The app passed it only the 8 LENA features, so every feature landed
one slot off and the last slot was empty. The model the classifier paper describes (Kachergis et al.)
was retrained without time two days later, but it never reached the app. See
[classify_cds_ods@fb18716](https://github.com/kachergis/classify_cds_ods/commit/fb18716).

**Confirmed for this dataset:**
- Recomputing with the faulty model and the app's misaligned input reproduces every published
  `cds_prob` for the 76,013 awake segments (max difference 1.2e-7). The correct model does not.
- The sleep classifier was correct: every published `sleep_prob` matches it.
- `sleep_cds_min.csv` (1-minute epochs) was made with the same app, so its `cds_pred` is also faulty.
  The analyses only use its `sleep_pred` column, so nothing downstream is affected.

With the correct model, **41.7% of awake-segment labels change**. CDS segments go from 49,498 to 46,141.

## What depends on the tCDS labels

| Result | Depends on tCDS? |
|---|---|
| Mean CDS probability, % CDS epochs (Sec 3.2) | yes |
| Burst amplitude and duration (Table 2, Sec 4.1, 4.2, Tables 3–4, figures) | yes, computed on CDS epochs |
| Hourly words (`avg_hrly_words`, "quantity", a covariate in the vocabulary models) | depends on the code version, see below |
| Sleep removal, Supp. II (turns), Supp. IV (naps) | no, these use only sleep labels |

### Hourly words: published vs current code

The published results compute hourly words over **all awake epochs**, CDS and ODS alike, although the
paper calls them "CDS words". Only that version reproduces the paper: 1094 words/hr in Table 2, and
quantity χ² = 0.35, vocabulary ~ amplitude χ² = 4.42 (β = 4.54) and vocabulary ~ duration χ² = 4.12
(β = 3.17) in Sec 4.

The current `1_modeling.Rmd` restores `filter(cds_pred=='1')` at the top of the CDS chunk (793f13c).
With it:
- Hourly words count **CDS epochs only**: 810 words/hr with the published labels.
- The vocabulary-model statistics no longer match the paper (amplitude χ² = 5.26, duration χ² = 4.29).
- The Sec 3.2 descriptives degenerate: there are no sleep epochs left, and "% CDS epochs" is 100%.
- Hourly words now depend on the classifier too.

Both versions are run below (`quantity` in `results.csv`).

## The burstiness file had to be reconstructed

The shipped `burstiness_compiled_results.csv` cannot be regenerated from `burst_detection_v1.py`, which
uses all rows in file order. I tested recipes against it.
- **What matches:** awake CDS epochs only, in chronological order, threshold > 3*SD as coded. This
  reproduces amplitude, duration and burst count exactly for every child in corpora D and M (40/40).
  It also confirms that the paper's burst metrics were computed on the (faulty) CDS labels.
- **What doesn't:** corpora R (0/211) and L (88/306). As the main README notes, the shipped file was
  built from an earlier export of their epoch data that is no longer available.

So the paper's exact numbers cannot be recomputed with corrected labels. Instead,
`burst_detection_v2.py` applies the reconstructed recipe to both the faulty and the corrected labels, so
the two can be compared with the pipeline held fixed. It also runs the paper's stated threshold
(mean + 3 SD, Sec 3.3) as a sensitivity check.

## Results

All models are the paper's own code from `1_modeling.Rmd`, run by `rerun_tcds_analysis.R`. Values in
**bold** are p < .05. "Paper" uses the shipped burst file. With hourly words over all awake epochs, it
reproduces the manuscript exactly.

### Not affected by the hourly-words definition

| | Paper | Faulty, 3 SD | **Corrected, 3 SD** | Faulty, mean + 3 SD | **Corrected, mean + 3 SD** |
|---|---|---|---|---|---|
| Recordings / children | 555 / 292 | 555 / 292 | 555 / 292 | 483 / 274 | 488 / 280 |
| Mean CDS prob (SD) | .67 (.10) | .67 (.10) | .71 (.12) | .67 (.10) | .71 (.12) |
| % CDS epochs | 67.19 | 67.19 | 64.18 | 67.19 | 64.18 |
| Mean burst amplitude (words) | 400 | 430 | 389 | 530 | 482 |
| Mean burst duration (0.1-epoch units) | 10.4 | 15.0 | 14.6 | 9.5 | 9.8 |
| **Age → amplitude**: χ², p | 4.25, **.039** | 1.15, .28 | 7.09, **.008** | 2.17, .14 | 6.20, **.013** |
| **Age → duration**: χ², p | 16.63, **<.001** | 0.26, .61 | 0.62, .43 | 0.12, .73 | 4.41, **.036** |

### Hourly words over all awake epochs (as published)

| | Paper | Faulty, 3 SD | **Corrected, 3 SD** | Faulty, mean + 3 SD | **Corrected, mean + 3 SD** |
|---|---|---|---|---|---|
| Hourly words | 1094 | 1094 | 1094 | 1073 | 1093 |
| Age → quantity: χ², p | 0.35, .56 | 0.35, .56 | 0.35, .56 | 0.14, .71 | 0.68, .41 |
| **Vocab ~ amplitude**: χ², p | 4.42, **.036** | 4.30, **.038** | 8.12, **.004** | 3.64, .057 | 8.31, **.004** |
| **Vocab ~ duration**: χ², p | 4.12, **.042** | 0.87, .35 | 3.30, .069 | 4.65, **.031** | 0.25, .62 |

### Hourly words over CDS epochs only (current `1_modeling.Rmd`)

| | Paper | Faulty, 3 SD | **Corrected, 3 SD** | Faulty, mean + 3 SD | **Corrected, mean + 3 SD** |
|---|---|---|---|---|---|
| Hourly words | 810 | 810 | 670 | 793 | 676 |
| Age → quantity: χ², p | 1.53, .22 | 1.53, .22 | 2.74, .098 | 1.43, .23 | 2.99, .084 |
| **Vocab ~ amplitude**: χ², p | 5.26, **.022** | 5.13, **.024** | 3.50, .061 | 4.01, **.045** | 2.16, .14 |
| **Vocab ~ duration**: χ², p | 4.29, **.038** | 0.93, .34 | 1.95, .16 | 4.22, **.040** | 0.01, .93 |

Vocabulary model N: 472 for the 3 SD conditions; 410 (faulty) and 421 (corrected) for mean + 3 SD.
The mean + 3 SD conditions drop children with no bursts above the threshold (74 faulty, 68 corrected),
because the paper's model comparison cannot run with missing burst values. Betas are in `results.csv`.

## Takeaways

1. **Age → burst amplitude holds, and gets stronger, with the correct classifier** (p = .008 and .013
   under the two thresholds). This model does not use hourly words.
2. **Vocabulary ~ burst amplitude depends on how quantity is controlled.** With hourly words over all
   awake epochs, as published, it is stronger with corrected labels (p = .004 under both thresholds).
   With hourly CDS words, as the paper describes the covariate and as the current code computes it, it
   is not significant with corrected labels (p = .061 and .14).
3. **Burst duration results are not robust.** With corrected labels, vocabulary ~ duration is not
   significant in any variant. Age → duration is significant only under mean + 3 SD (p = .036). The
   paper's strong age → duration effect (p < .001) is not reproduced by any reconstructed variant, with
   either set of labels.
4. **The Sec 3.2 descriptives change:** mean CDS probability .71 (.12) instead of .67 (.10), and 64.18%
   CDS epochs instead of 67.19%. Table 2's burst means change too.
5. **Unaffected:** sleep removal and Supp. II and IV. The age → quantity result is non-significant in
   every variant.
6. **Caveat:** the comparison uses the reconstructed burst pipeline, not the exact one behind the paper.
   For corpora R and L it differs from the shipped file even with the faulty labels ("Faulty, 3 SD" vs
   "Paper"). Exact updated numbers would need the original R and L epoch data.

## Files

| File | What it does |
|---|---|
| `models/final_rawLENA_xgb.json` | Correct 8-feature tCDS model (from `classify_cds_ods`) |
| `models/faulty_app_tCDS_9feature.json` | The faulty model the app served, kept so the check can be repeated |
| `tcds_rerun/tcds_labels.csv.gz` | Corrected `cds_prob` / `cds_pred` per row of `everyday_cds_ods.csv`, plus `segment` (the epoch's position in the recording, needed to order epochs in time) |
| `reclassify_tcds.py` | `labels`: makes `tcds_labels.csv.gz` (needs the full pre-trim `everyday_cds_ods.csv` with the LENA feature columns). `apply`: writes `dataframes/everyday_cds_ods_reclassified.csv` and `dataframes/everyday_cds_ods_segments.csv` from the public file |
| `burst_detection_v2.py` | Reconstructed burst recipe: CDS-only, chronological, `--threshold 3sd` or `mean3sd` |
| `rerun_tcds_analysis.R` | Runs the paper's own model chunks for each condition and both hourly-words definitions; writes `tcds_rerun/results.csv` |
| `tcds_rerun/burstiness_*.csv` | Burst metrics per condition |

To reproduce from the public data (from the repo root, with `dataframes.zip` unzipped):

```bash
python reclassify_tcds.py apply
for t in 3sd mean3sd; do
  python burst_detection_v2.py --input dataframes/everyday_cds_ods_segments.csv --output tcds_rerun/burstiness_faulty_labels_$t.csv --threshold $t
  python burst_detection_v2.py --input dataframes/everyday_cds_ods_reclassified.csv --output tcds_rerun/burstiness_corrected_labels_$t.csv --threshold $t
done
Rscript rerun_tcds_analysis.R
```

To regenerate the labels and repeat the faulty-model check, you need the full `everyday_cds_ods.csv`
(with the LENA feature columns):

```bash
python reclassify_tcds.py labels --full-input path/to/full/everyday_cds_ods.csv --check-faulty-model models/faulty_app_tCDS_9feature.json
```

Tested with Python 3.11 (xgboost 3.2, pandas 3.0, scipy 1.15) and R 4.6 (lme4 2.0.1, lmerTest 3.2.1, dplyr 1.2.1).
