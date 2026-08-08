from domain.bio_samples_api_error import BioSamplesAPIError


def test_bio_samples_api_error_stores_values():
    error = BioSamplesAPIError(
        "failed",
        status_code=500,
        details=[{"reason": "server"}],
        retryable=True,
    )

    assert str(error) == "failed"
    assert error.status_code == 500
    assert error.details == [{"reason": "server"}]
    assert error.retryable is True


def test_bio_samples_api_error_defaults():
    error = BioSamplesAPIError("failed")

    assert error.status_code is None
    assert error.details == []
    assert error.retryable is True
