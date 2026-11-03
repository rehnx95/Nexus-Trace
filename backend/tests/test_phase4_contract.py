from app.extraction.pretrained.gazetteer import find_gazetteer_entities
from app.extraction.pretrained.ner import NerExtractor


def test_gazetteer_extracts_person_location_and_organization():
    text = "Rohan Patel was seen at Central Market near Nova Traders Limited."
    spans = find_gazetteer_entities(text)
    found = {(span["type"], span["text"]) for span in spans}

    assert ("Person", "Rohan Patel") in found
    assert ("Location", "Central Market") in found
    assert ("Organization", "Nova Traders Limited") in found


def test_gazetteer_negative_does_not_extract_common_words():
    spans = find_gazetteer_entities("The officer filed a report in the morning.")
    assert spans == []


def test_ner_extractor_reports_safe_fallback():
    extractor = NerExtractor(
        model=None,
        model_status={
            "model_status": "fallback",
            "model_warning": "spaCy unavailable",
            "model_path": None,
        },
    )
    entities, status = extractor.extract(
        "Nisha Rao works at Meera Holdings Limited.",
        "doc-phase4",
    )

    assert status["model_status"] == "fallback"
    assert status["model_warning"] == "spaCy unavailable"
    assert "Nisha Rao" in {entity.id for entity in entities if entity.type == "Person"}
