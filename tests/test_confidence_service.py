from app.services.confidence_service import ConfidenceService


def test_confidence_high_landmark():
    """Tests high confidence score for verified landmark with complete city and country metadata."""
    score = ConfidenceService.calculate_confidence(
        raw_name="Fushimi Inari Shrine",
        city="Kyoto",
        country="Japan",
        verified=True,
        place_id="ChIJ31-1ZkQGAWARf0N5e9rW028",
        address="Kyoto, Japan",
    )
    assert score >= 90
    assert score <= 100


def test_confidence_generic_term_penalty():
    """Tests that generic location terms (e.g. 'temple', 'beach') without city metadata are heavily penalized."""
    score = ConfidenceService.calculate_confidence(
        raw_name="temple", city=None, country=None, verified=False, place_id=None, address=None
    )
    assert score <= 45


def test_confidence_caption_alignment_boost():
    """Tests that caption text containing the place name boosts confidence score."""
    score_with_caption = ConfidenceService.calculate_confidence(
        raw_name="Shibuya Crossing",
        city="Tokyo",
        country="Japan",
        verified=False,
        text_context="Visiting Shibuya Crossing in Tokyo!",
    )

    score_without_caption = ConfidenceService.calculate_confidence(
        raw_name="Shibuya Crossing", city="Tokyo", country="Japan", verified=False, text_context=None
    )

    assert score_with_caption > score_without_caption
    assert score_with_caption >= 65
