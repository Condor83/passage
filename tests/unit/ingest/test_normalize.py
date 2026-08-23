from passage.ingest.validation import load_default_structure_manifest


def test_default_structure_manifest_is_complete_and_text_free() -> None:
    manifest = load_default_structure_manifest()

    assert len(manifest.expected_references()) == 6604
    assert manifest.expected_references()[0] == "bofm/1-ne/1/1"
    assert manifest.expected_references()[-1] == "bofm/moro/10/34"
    assert "text" not in manifest.model_dump_json().lower()
