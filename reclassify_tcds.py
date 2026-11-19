"""Re-run the tCDS/ODS classifier on everyday_cds_ods.csv with the correct model.

Why: everyday_cds_ods.csv was produced in 2023 by uploading each recording to the web app
(https://kachergis.shinyapps.io/classify_cds_ods/) via 1_pipeline.py. Until Nov 2026 that app
served a stale tCDS model trained with clock time as a 9th (first) feature, while the app passed
it only the 8 LENA features. Every feature landed one slot off and the last slot was empty, so the
published cds_prob / cds_pred values are wrong. (The sleep model was correct and is left as is.)

Two steps:

  labels  Needs the full, pre-trim everyday_cds_ods.csv, which has the LENA feature columns
          (AWC_COUNT, CT_COUNT, CV_COUNT, Duration_Secs, Meaningful, TV_Secs, Noise, Silence,
          Distant, segment). The public dataframes.zip omits them. Recomputes cds_prob / cds_pred for
          awake segments with the correct 8-feature model (models/final_rawLENA_xgb.json, from
          github.com/kachergis/classify_cds_ods) and the app's feature transformation, and writes
          tcds_rerun/tcds_labels.csv.gz (row, segment, cds_prob, cds_pred). With
          --check-faulty-model it also confirms that the faulty model reproduces the published values.

  apply   Uses only the public dataframes/everyday_cds_ods.csv plus tcds_rerun/tcds_labels.csv.gz.
          Writes, both with a `segment` column added (needed to order epochs in time):
            dataframes/everyday_cds_ods_reclassified.csv   corrected cds_prob / cds_pred
            dataframes/everyday_cds_ods_segments.csv       published (faulty) labels, unchanged
          Sleep segments keep the 0_loading.Rmd convention cds_pred = cds_prob = 0.

Usage:
    python reclassify_tcds.py labels --full-input path/to/full/everyday_cds_ods.csv \
                                     --check-faulty-model models/faulty_app_tCDS_9feature.json
    python reclassify_tcds.py apply
"""
import argparse

import numpy as np
import pandas as pd
import xgboost as xgb

FEATURES = ["AWC", "CTC", "CVC", "noise", "silence", "distant", "tv", "meaningful"]
LABELS = "tcds_rerun/tcds_labels.csv.gz"


def app_features(d):
    """Same transformation as the classify_cds_ods app does for LENA SP exports:
    counts per minute, and each audio category as a proportion of the segment."""
    dur_min = d["Duration_Secs"] / 60
    f = pd.DataFrame({
        "AWC": d["AWC_COUNT"] / dur_min,
        "CTC": d["CT_COUNT"] / dur_min,
        "CVC": d["CV_COUNT"] / dur_min,
        "noise": d["Noise"] / 60 / dur_min,
        "silence": d["Silence"] / 60 / dur_min,
        "distant": d["Distant"] / 60 / dur_min,
        "tv": d["TV_Secs"] / 60 / dur_min,
        "meaningful": d["Meaningful"] / 60 / dur_min,
    })
    return f[FEATURES].to_numpy(dtype=float)


def make_labels(args):
    d = pd.read_csv(args.full_input, index_col=0, dtype={"child_id": str})
    needed = ["AWC_COUNT", "CT_COUNT", "CV_COUNT", "Duration_Secs", "Meaningful", "TV_Secs",
              "Noise", "Silence", "Distant", "segment"]
    missing = [c for c in needed if c not in d.columns]
    if missing:
        raise SystemExit(f"{args.full_input} lacks {missing}: the 'labels' step needs the full, "
                         "pre-trim everyday_cds_ods.csv (the public dataframes.zip omits these columns)")
    X = app_features(d)
    awake = (d["sleep_pred"] == 0).to_numpy()

    model = xgb.Booster()
    model.load_model(args.model)
    assert model.feature_names == FEATURES, model.feature_names
    p_new = model.predict(xgb.DMatrix(X, feature_names=FEATURES))

    if args.check_faulty_model:
        old = xgb.Booster()
        old.load_model(args.check_faulty_model)
        assert old.num_features() == 9
        # reproduce the app's bug: the 8 features fill slots 0-7 (so AWC lands in the 'time' slot,
        # etc.) and the last slot is missing
        X_shifted = np.column_stack([X, np.full(len(X), np.nan)])
        p_bug = old.predict(xgb.DMatrix(X_shifted, missing=np.nan, feature_names=old.feature_names))
        max_diff = np.abs(d.loc[awake, "cds_prob"].to_numpy() - p_bug[awake]).max()
        print(f"faulty-model check: max |published cds_prob - faulty app| over awake segments = {max_diff:.2e}")
        assert max_diff < 1e-5, "published values do not match the faulty app"

    labels = pd.DataFrame({
        "row": d.index,
        "segment": d["segment"].astype(int),
        "cds_prob": np.where(awake, p_new, 0.0).round(6),
        "cds_pred": np.where(awake, (p_new > 0.5).astype(int), 0),
    })
    labels.to_csv(LABELS, index=False)

    old_pred = d.loc[awake, "cds_pred"].to_numpy()
    new_pred = labels.loc[awake, "cds_pred"].to_numpy()
    print(f"awake segments: {awake.sum()} | CDS before: {old_pred.sum()} after: {new_pred.sum()} | "
          f"labels changed: {np.mean(old_pred != new_pred):.1%}")
    print(f"wrote {LABELS}")


def apply_labels(args):
    d = pd.read_csv(args.input, index_col=0, dtype={"child_id": str})
    labels = pd.read_csv(LABELS).set_index("row")
    assert labels.index.equals(d.index), "row ids in the labels file do not match the input"

    published = d.copy()
    published["segment"] = labels["segment"]
    published.to_csv("dataframes/everyday_cds_ods_segments.csv")

    out = published.copy()
    out["cds_prob"] = labels["cds_prob"]
    out["cds_pred"] = labels["cds_pred"]
    out.to_csv("dataframes/everyday_cds_ods_reclassified.csv")

    awake = d["sleep_pred"] == 0
    print(f"awake segments: {awake.sum()} | CDS before: {d.loc[awake, 'cds_pred'].sum()} "
          f"after: {out.loc[awake, 'cds_pred'].sum()} | "
          f"labels changed: {(d.loc[awake, 'cds_pred'] != out.loc[awake, 'cds_pred']).mean():.1%}")
    print("wrote dataframes/everyday_cds_ods_reclassified.csv and dataframes/everyday_cds_ods_segments.csv")


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="step", required=True)
    lab = sub.add_parser("labels")
    lab.add_argument("--full-input", required=True)
    lab.add_argument("--model", default="models/final_rawLENA_xgb.json")
    lab.add_argument("--check-faulty-model", default=None)
    app = sub.add_parser("apply")
    app.add_argument("--input", default="dataframes/everyday_cds_ods.csv")
    args = ap.parse_args()
    make_labels(args) if args.step == "labels" else apply_labels(args)


if __name__ == "__main__":
    main()
