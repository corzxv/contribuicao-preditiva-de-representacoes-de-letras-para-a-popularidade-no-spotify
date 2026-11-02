"""Complemento leve e idempotente das contagens de cauda, sem identificadores públicos."""

import json

import polars as pl
import pyarrow.parquet as pq

from tcc_music_popularity.closure_diagnostics import (
    MAX_BYTES,
    OUTPUT,
    PREDICTIONS,
    digest,
)
from tcc_music_popularity.manual_lyrics import require


def run():
    require(PREDICTIONS.stat().st_size <= MAX_BYTES, "Fonte excede orçamento leve.")
    require(pq.ParquetFile(PREDICTIONS).metadata.num_rows == 77535, "Contagem inesperada.")
    p = pl.read_parquet(
        PREDICTIONS,
        columns=[
            "spotify_popularity",
            "text_component_id",
            "prediction_combined",
        ],
    )
    t = p.filter(pl.col("spotify_popularity") >= 80)
    sizes = t.group_by("text_component_id").len().sort("len", descending=True)
    result = {
        "source_sha256": digest(PREDICTIONS),
        "n": t.height,
        "observed_min": t["spotify_popularity"].min(),
        "observed_max": t["spotify_popularity"].max(),
        "observed_counts_80_84": t.filter(pl.col("spotify_popularity").is_between(80, 84)).height,
        "observed_counts_85_89": t.filter(pl.col("spotify_popularity").is_between(85, 89)).height,
        "observed_counts_90_100": t.filter(pl.col("spotify_popularity").is_between(90, 100)).height,
        "components": sizes.height,
        "largest_tail_component_tracks": sizes["len"].max(),
        "top5_components_tail_tracks": sizes["len"].head(5).sum(),
        "global_predictions_at_least_80": p.filter(pl.col("prediction_combined") >= 80).height,
        "global_max_prediction": p["prediction_combined"].max(),
    }
    tail = pl.read_csv(OUTPUT / "tail_residuals.csv")
    base = tail.filter(pl.col("model") == "baseline").row(0, named=True)
    comb = tail.filter(pl.col("model") == "combined").row(0, named=True)
    result["tail_contribution_to_baseline_combined_mae_gain"] = (
        base["absolute_error_sum"] - comb["absolute_error_sum"]
    ) / p.height
    result["tail_share_of_total_baseline_combined_gain"] = result[
        "tail_contribution_to_baseline_combined_mae_gain"
    ] / (8.352484301528046 - 8.115121721302737)
    output = OUTPUT / "complemento_cauda.json"
    if output.exists():
        require(
            json.loads(output.read_text(encoding="utf-8")) == result,
            "Complemento existente diverge; preservado.",
        )
    else:
        output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(
        json.dumps({"completed": True, "n": t.height, "existing_output_verified": True}), flush=True
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(run())
