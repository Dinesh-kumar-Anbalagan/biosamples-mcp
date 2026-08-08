from unittest.mock import AsyncMock

import pytest

from orchestrator.request_context import RequestContext
from tools.get_sample_tool_service import GetSampleToolService
from tools.search_samples_tool_service import SearchSamplesToolService
from tools.server_info_tool_service import ServerInfoToolService
from tools.submit_sample_tool_service import SubmitSampleToolService


@pytest.fixture
def context():
    return RequestContext(request_id="rid", tool_name="tool", payload={})


@pytest.mark.asyncio
async def test_get_sample_tool_service_calls_adapter(context):
    adapter = AsyncMock()
    adapter.get_sample.return_value = {"accession": "SAMN1"}
    service = GetSampleToolService(adapter)

    result = await service.execute(context, {"accession": "SAMN1"})

    adapter.get_sample.assert_awaited_once_with("SAMN1")
    assert result == {"sample": {"accession": "SAMN1"}}

@pytest.mark.asyncio
async def test_server_info_tool_service_returns_static_info(context):
    service = ServerInfoToolService()

    result = await service.execute(context, {})

    assert result["serverName"] == "BioSamples MCP Server"
    assert result["version"] == "0.1.0"
    assert "biosamples.search_samples" in result["supportedTools"]


@pytest.mark.asyncio
async def test_search_samples_tool_service_normalizes_embedded_samples(context):
    sample = {
        "accession": "SAMN1",
        "name": "sample one",
        "characteristics": {
            "organism": [
                {
                    "text": "Homo sapiens"
                }
            ]
        },
        "relationships": [
            {
                "source": "SAMN1",
                "type": "derived from",
                "target": "SAMN0",
            }
        ],
        "externalReferences": [
            {
                "url": "https://example.org/sample"
            }
        ],
        "_links": {
            "self": {
                "href": "https://example.org/SAMN1"
            }
        },
    }
    adapter = AsyncMock()
    adapter.search_samples.return_value = {
        "_embedded": {
            "samples": [
                sample,
            ]
        },
        "page": {
            "size": 1,
            "number": 2,
            "totalElements": 5,
            "totalPages": 5,
        },
    }
    service = SearchSamplesToolService(adapter)
    payload = {
        "query": "blood",
        "filters": [{"type": "attr", "field": "organism", "value": "Homo sapiens"}],
        "dateRange": {"field": "release", "from": "2020-01-01"},
        "page": 2,
        "size": 1,
    }

    result = await service.execute(context, payload)

    adapter.search_samples.assert_awaited_once_with(
        query_terms="blood",
        filters=payload["filters"],
        page=2,
        size=1,
        date_range=payload["dateRange"],
    )

    assert result["samples"] == [sample]

    assert result["page"] == {
        "size": 1,
        "number": 2,
        "totalElements": 5,
        "totalPages": 5,
    }

@pytest.mark.asyncio
async def test_search_samples_tool_service_uses_defaults(context):
    adapter = AsyncMock()
    adapter.search_samples.return_value = {}
    service = SearchSamplesToolService(adapter)

    result = await service.execute(context, {})

    adapter.search_samples.assert_awaited_once_with(
        query_terms="",
        filters=[],
        page=0,
        size=10,
        date_range={},
    )
    assert result == {
        "samples": [],
        "page": {
            "size": 10,
            "number": 0,
            "totalElements": 0,
            "totalPages": 0,
        },
    }

@pytest.mark.asyncio
async def test_submit_sample_tool_service_calls_adapter_with_cached_token(context):
    adapter = AsyncMock()
    redis_client = AsyncMock()

    redis_client.get.return_value = "token-123"
    adapter.submit_sample.return_value = {
        "accession": "SAMN1"
    }

    service = SubmitSampleToolService(
        adapter,
        redis_client,
    )

    submission = {
        "name": "sample"
    }

    result = await service.execute(
        context,
        {
            "webinId": "Webin-12345",
            "submissionSample": submission,
        },
    )

    adapter.submit_sample.assert_awaited_once_with(
        submission=submission,
        auth_token="token-123",
    )

    assert result == {
        "message": "Sample submitted to BioSamples.",
        "submissionResult": {
            "accession": "SAMN1"
        },
    }

@pytest.mark.asyncio
async def test_submit_sample_requires_login_when_token_missing(context):
    adapter = AsyncMock()
    redis_client = AsyncMock()

    redis_client.get.return_value = None

    service = SubmitSampleToolService(
        adapter,
        redis_client,
    )

    result = await service.execute(
        context,
        {
            "webinId": "Webin-12345",
            "submissionSample": {
                "name": "sample"
            },
        },
    )

    assert result["status"] == "authentication_required"
    assert "loginUrl" in result

    adapter.submit_sample.assert_not_awaited()