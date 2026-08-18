import polars as pl

from tcc_music_popularity.quality import add_spotify_quality_flags


def test_ranges_are_flagged_without_dropping_rows():
    frame = pl.DataFrame(
        {
            "track_id": ["A" * 22, "bad"],
            "spotify_popularity": [50, 101],
            "year": [2020, 1700],
            "duration_ms": [1000, 0],
            "tempo": [100.0, -1.0],
            "danceability": [0.5, 1.2],
            "key": [1, 99],
            "mode": [1, 3],
            "time_signature": [4, 12],
        }
    )
    result = add_spotify_quality_flags(frame)
    assert result.height == 2
    assert result["qf_any"].to_list() == [False, True]
    assert result["qf_spotify_popularity_out_of_range"][1]
