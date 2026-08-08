from model.bio_sample import BioSamples


def test_from_dict_keeps_only_dataclass_fields():
    sample = BioSamples.from_dict(
        {
            "accession": "SAMN1",
            "name": "blood sample",
            "organism": "Homo sapiens",
            "unknownField": "ignored",
        }
    )

    assert sample.accession == "SAMN1"
    assert sample.name == "blood sample"
    assert sample.organism == "Homo sapiens"
    assert not hasattr(sample, "unknownField")


def test_from_dict_missing_values_become_none():
    sample = BioSamples.from_dict({"accession": "SAMN1"})

    assert sample.accession == "SAMN1"
    assert sample.name is None
    assert sample.disease is None
