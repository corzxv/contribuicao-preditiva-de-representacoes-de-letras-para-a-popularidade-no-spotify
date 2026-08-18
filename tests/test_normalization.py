from tcc_music_popularity.normalization import (
    base_title,
    classify_version,
    composition_key,
    conservative_normalize,
    split_artist,
    strict_normalize,
)


def test_diacritics_and_punctuation_variants():
    assert strict_normalize("Beyoncé") != strict_normalize("Beyonce")
    assert conservative_normalize("Beyoncé") == conservative_normalize("Beyonce")
    assert conservative_normalize("AC/DC") == conservative_normalize("ACDC")


def test_earth_wind_and_fire_is_not_split_as_collaborators():
    primary, collaborators = split_artist("Earth, Wind & Fire")
    assert primary == "Earth, Wind & Fire"
    assert collaborators == []


def test_feat_and_ft_are_classified_without_overwriting_artist():
    assert split_artist("Artist feat. Guest") == ("Artist", ["Guest"])
    assert split_artist("Artist ft Guest") == ("Artist", ["Guest"])


def test_title_version_classification_and_base():
    examples = {
        "Song - 2011 Remaster": ("Song", "remaster"),
        "Song (Live)": ("Song", "live"),
        "Song - Radio Edit": ("Song", "radio_edit"),
        "Song [Acoustic Version]": ("Song", "acoustic"),
    }
    for title, (expected_base, flag) in examples.items():
        assert base_title(title) == expected_base
        assert classify_version(title)[flag]


def test_parenthetical_content_without_version_is_preserved():
    assert base_title("Song (For You)") == "Song (For You)"


def test_unicode_apostrophes_hyphens_and_different_artists():
    assert strict_normalize("Don’t—Stop") == strict_normalize("Don't-Stop")
    assert composition_key("Artist A", "Same Title") != composition_key("Artist B", "Same Title")
    assert composition_key("Artist", "Song (Live)") == composition_key("Artist", "Song")
    assert classify_version("Song (Live)")["live"] is True
    assert classify_version("Song (Remix)")["remix"] is True
