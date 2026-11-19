"""Burstiness of child-directed speech (CDS), reconstructed from burst_detection_v1.py.

burst_detection_v1.py, as committed, computes bursts over *all* rows of everyday_cds_ods.csv
(sleep and other-directed epochs included) in file-row order, which is not chronological.
The shipped dataframes/burstiness_compiled_results.csv was not made that way. Testing variants
against it, the recipe that matches is: awake CDS epochs only (sleep_pred == 0 & cds_pred == 1),
sorted chronologically by `segment`, threshold > 3*SD as coded in v1. That recipe reproduces the
shipped amplitude, count and duration exactly for every child in corpora D and M (40/40); the R and
L corpora differ because the shipped file was built from an earlier export of their epoch data.

This script applies that recipe. The burst computation itself (interpolation to 0.1-epoch steps,
threshold, run lengths, amplitude) is copied unchanged from v1. It does not draw the plots.

Needs a `segment` column, which the public everyday_cds_ods.csv lacks; `python reclassify_tcds.py
apply` writes everyday_cds_ods_segments.csv (published labels) and everyday_cds_ods_reclassified.csv
(corrected labels) with it.

Usage:
    python burst_detection_v2.py --input dataframes/everyday_cds_ods_segments.csv \
                                 --output tcds_rerun/burstiness_faulty_labels_3sd.csv
    # --threshold mean3sd uses mean + 3 SD (as described in the paper, Sec 3.3) instead of 3 SD
"""
import argparse

import numpy as np
import pandas as pd
import scipy.interpolate as interpolate


def count_contiguous_segments(arr):
    not_nan_segments = np.where(~np.isnan(arr))[0]
    if not_nan_segments.size == 0:
        return 0
    segment_changes = np.where(np.diff(not_nan_segments) > 1)[0]
    return len(segment_changes) + 1


def lengths_of_non_nan_segments(arr):
    if not arr.size:
        return np.array([])
    lengths = []
    current_length = 0
    for value in arr:
        if not np.isnan(value):
            current_length += 1
        else:
            if current_length > 0:
                lengths.append(current_length)
                current_length = 0
    if current_length > 0:
        lengths.append(current_length)
    return np.array(lengths)


def child_bursts(data, threshold="3sd"):
    """data: AWC_COUNT per CDS epoch, in chronological order (v1's per-child loop body)."""
    f = interpolate.interp1d(np.linspace(0, len(data), len(data)), data)
    xnew = np.arange(0, len(data), 0.1)
    ynew = f(xnew)

    std = np.std(ynew)
    cutoff = 3 * std if threshold == "3sd" else np.mean(ynew) + 3 * std

    bursts = np.full([len(ynew), 1], np.nan)
    bursts = np.concatenate(bursts, axis=0)
    for time in range(len(ynew)):
        if ynew[time] > cutoff:
            bursts[time] = ynew[time]

    burst_lengths = lengths_of_non_nan_segments(bursts)
    with np.errstate(all="ignore"):
        return dict(
            bursts_count=count_contiguous_segments(bursts),
            burst_lengths=burst_lengths,
            mean_burst_length=np.mean(burst_lengths) if burst_lengths.size else np.nan,
            std_burst_length=np.std(burst_lengths) if burst_lengths.size else np.nan,
            mean_burst_amplitude=np.mean(bursts[~np.isnan(bursts)]) if burst_lengths.size else np.nan,
            mean_burst_std=np.std(bursts[~np.isnan(bursts)]) if burst_lengths.size else np.nan,
        )


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", default="dataframes/everyday_cds_ods.csv")
    ap.add_argument("--output", default="tcds_rerun/burstiness.csv")
    ap.add_argument("--threshold", choices=["3sd", "mean3sd"], default="3sd")
    args = ap.parse_args()

    real_data = pd.read_csv(args.input, index_col=0, dtype={"child_id": str})
    cds = real_data[(real_data["sleep_pred"] == 0) & (real_data["cds_pred"] == 1)]

    rows = []
    for child in real_data["child_id"].unique():
        data = cds[cds["child_id"] == child].sort_values("segment")["AWC_COUNT"].to_numpy(dtype=float)
        if len(data) < 2:  # interpolation needs at least two epochs
            continue
        rows.append(dict(child_id=child, **child_bursts(data, args.threshold)))

    cols = ["child_id", "bursts_count", "burst_lengths", "mean_burst_length",
            "std_burst_length", "mean_burst_amplitude", "mean_burst_std"]
    pd.DataFrame(rows)[cols].to_csv(args.output, index=False)
    print(f"wrote {args.output} ({len(rows)} children)")


if __name__ == "__main__":
    main()
