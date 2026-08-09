import httpx
import pytest

from unittest.mock import AsyncMock, Mock, patch
from adapter.bio_samples_adapter import BioSamplesAdapter
from domain.bio_samples_api_error import BioSamplesAPIError

class AsyncClientMock:
    def __init__(self, response):
        self.response = response
        self.get = AsyncMock(return_value=response)
        self.post = AsyncMock(return_value=response)

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False


def response(status_code=200, json_body=None, text="body", url="https://example.com/samples"):
    mock = Mock(spec=httpx.Response)
    mock.status_code = status_code
    mock.text = text
    mock.url = url
    mock.json.return_value = json_body or {"ok": True}
    return mock

def test_headers_without_auth_token():
    assert BioSamplesAdapter()._headers() == {"Accept": "application/hal+json"}

def test_headers_with_auth_token():
    assert BioSamplesAdapter()._headers("token") == {
        "Accept": "application/hal+json",
        "Authorization": "Bearer token",
    }

def test_raise_for_error_does_nothing_for_success_response():
    BioSamplesAdapter()._raise_for_error(response(200), "failed")

def test_raise_for_error_raises_api_error_for_failure_response():
    adapter = BioSamplesAdapter()
    bad_response = response(
        status_code=503,
        text="x" * 1200,
        url="https://example.com/error",
    )

    with pytest.raises(BioSamplesAPIError) as exc:
        adapter._raise_for_error(bad_response, "BioSamples failed")

    assert str(exc.value) == "BioSamples failed"
    assert exc.value.status_code == 503
    assert exc.value.retryable is True
    assert exc.value.details[0]["statusCode"] == 503
    assert exc.value.details[0]["url"] == "https://example.com/error"
    assert len(exc.value.details[0]["response"]) == 1000


@pytest.mark.asyncio
async def test_get_calls_httpx_and_returns_json():
    adapter = BioSamplesAdapter()
    client = AsyncClientMock(response(json_body={"samples": []}))

    with patch("adapter.bio_samples_adapter.httpx.AsyncClient", return_value=client):
        result = await adapter._get("/samples", params=[("text", "blood")])

    assert result == {"samples": []}
    client.get.assert_awaited_once_with(
        f"{adapter.base_url}/samples",
        params=[("text", "blood")],
        headers={"Accept": "application/hal+json"},
    )

@pytest.mark.asyncio
async def test_post_calls_httpx_and_returns_json():
    adapter = BioSamplesAdapter()
    client = AsyncClientMock(response(json_body={"accession": "SAMN1"}))
    body = {"name": "sample"}

    with patch("adapter.bio_samples_adapter.httpx.AsyncClient", return_value=client):
        result = await adapter._post("/samples", body=body, auth_token="token")

    assert result == {"accession": "SAMN1"}
    client.post.assert_awaited_once_with(
        f"{adapter.base_url}/samples",
        json=body,
        headers={
            "Accept": "application/hal+json",
            "Authorization": "Bearer token",
            "Content-Type": "application/json",
        },
    )

@pytest.mark.asyncio
async def test_search_samples_builds_params_with_filters_and_date_range():
    adapter = BioSamplesAdapter()

    with patch.object(adapter, "_get", new_callable=AsyncMock) as get:
        get.return_value = {"ok": True}
        result = await adapter.search_samples(
            query_terms="blood",
            filters=[{"type": "attr", "field": "organism", "value": "Homo sapiens"}],
            page=2,
            size=20,
            date_range={"field": "release", "from": "2020-01-01", "until": "2024-01-01"},
        )

    assert result == {"ok": True}
    get.assert_awaited_once_with(
        "/samples",
        params=[
            ("text", "blood"),
            ("page", 2),
            ("size", 20),
            ("filter", "attr:organism:Homo sapiens"),
            ("filter", "dt:release:from=2020-01-01until=2024-01-01"),
        ],
    )

@pytest.mark.asyncio
async def test_search_samples_date_range_requires_field():
    adapter = BioSamplesAdapter()

    with pytest.raises(BioSamplesAPIError) as exc:
        await adapter.search_samples(
            query_terms="blood",
            date_range={"from": "2020-01-01"},
        )

    assert "Date range requires field" in str(exc.value)
    assert exc.value.retryable is False

@pytest.mark.asyncio
async def test_get_sample_calls_get_with_accession_path():
    adapter = BioSamplesAdapter()

    with patch.object(adapter, "_get", new_callable=AsyncMock) as get:
        get.return_value = {"accession": "SAMN1"}
        result = await adapter.get_sample("SAMN1")

    assert result == {"accession": "SAMN1"}
    get.assert_awaited_once_with("/samples/SAMN1")

@pytest.mark.asyncio
async def test_submit_sample_requires_auth_token():
    adapter = BioSamplesAdapter()

    with pytest.raises(BioSamplesAPIError) as exc:
        await adapter.submit_sample({"name": "sample"}, auth_token=None)

    assert "Authentication token is required" in str(exc.value)
    assert exc.value.retryable is False

@pytest.mark.asyncio
async def test_submit_sample_posts_submission_with_token():
    adapter = BioSamplesAdapter()
    submission = {"name": "sample"}

    with patch.object(adapter, "_post", new_callable=AsyncMock) as post:
        post.return_value = {"accession": "SAMN1"}
        result = await adapter.submit_sample(submission, auth_token="token")

    assert result == {"accession": "SAMN1"}
    post.assert_awaited_once_with(
        "/samples",
        body=submission,
        auth_token="token",
    )