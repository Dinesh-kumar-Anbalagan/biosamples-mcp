import pytest

from domain.bio_samples_api_error import BioSamplesAPIError
from domain.filter_builder import FilterBuilder


@pytest.mark.parametrize(
    "filter_item,expected",
    [
        (
            {"type": "attr", "field": "organism", "value": "Homo sapiens"},
            "attr:organism:Homo sapiens",
        ),
        (
            {"type": "rel", "field": "derivedFrom", "value": "SAMEG1"},
            "rel:derivedFrom:SAMEG1",
        ),
        (
            {"type": "rrel", "field": "derivedFrom", "value": "SAMEG2"},
            "rrel:derivedFrom:SAMEG2",
        ),
        (
            {"type": "name", "value": "sample one"},
            "name:sample one",
        ),
        (
            {"type": "extd", "field": "ENA", "value": "ERR123"},
            "extd:ENA:ERR123",
        ),
        (
            {"type": "dom", "value": "self.BioSamples"},
            "dom:self.BioSamples",
        ),
        (
            {"type": "acc", "accession": "SAMN*"},
            "acc:SAMN*",
        ),
    ],
)
def test_build_supported_filters(filter_item, expected):
    assert FilterBuilder.build(filter_item) == expected


@pytest.mark.parametrize(
    "filter_item,message",
    [
        (
            {"type": "dom"},
            "Domain filter requires",
        ),
        (
            {"type": "acc"},
            "Accession filter requires",
        ),
        (
            {"type": "unknown"},
            "Unsupported filter type",
        ),
    ],
)
def test_build_invalid_filters_raise_api_error(filter_item, message):
    with pytest.raises(BioSamplesAPIError) as exc:
        FilterBuilder.build(filter_item)

    assert message in str(exc.value)
    assert exc.value.retryable is False
    assert exc.value.details == [{"filter": filter_item}]


def test_build_attribute_filter_without_value():
    result = FilterBuilder.build(
        {
            "type": "attr",
            "field": "organism",
        }
    )

    assert result == "attr:organism"