from typing import Any

from adapter.bio_samples_adapter import BioSamplesAdapter
from core.decorators import Tool
from orchestrator.request_context import RequestContext
from tools.base.tool_service import ToolService


@Tool(
    name="biosamples_submitsample",
    description=(
            "Submit a validated BioSamples-compatible sample object to BioSamples. "
            "Use this tool only when the user has already reviewed and confirmed a prepared "
            "submission payload. This tool performs a write operation and may create a real "
            "sample record in BioSamples. "

            "Required input: 'submissionSample'. "
            "'submissionSample' must be a complete BioSamples-compatible JSON object ready for submission. "
            "It should include the sample name, release date, characteristics, relationships, "
            "external references, and any other required BioSamples fields already prepared by "
            "the submission preparation flow. "

            "This tool must not be used with raw natural-language descriptions such as "
            "'human blood sample collected in London'. For natural-language sample descriptions, "
            "use biosamples.prepare_submission first. "

            "This tool should only be called after validation has passed and the user has explicitly "
            "confirmed that the sample should be submitted. "

            "Example input: "
            "{'submissionSample': {'name': 'human blood diabetes sample', "
            "'release': '2026-01-01', "
            "'characteristics': {'organism': [{'text': 'Homo sapiens'}], "
            "'material': [{'text': 'blood'}], "
            "'disease': [{'text': 'diabetes'}]}}}. "

            "This tool is not read-only. It submits data to BioSamples through the BioSamplesAdapter."
    ),
 input_schema={
        "type": "object",
        "properties": {
            "submissionSample": {
                "type": "object",
                "description": (
                    "Complete BioSamples-compatible sample JSON object ready for submission. "
                    "Must be validated and explicitly confirmed by the user before this tool is called."
                ),
                "additionalProperties": True
            }
        },
        "required": ["submissionSample"],
        "additionalProperties": False
    },
)
class SubmitSampleToolService(ToolService):
    def __init__(self, biosamples_adapter: BioSamplesAdapter):
        self.biosamples_adapter = biosamples_adapter

    async def execute(
        self,
        context: RequestContext,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        auth_token = payload.get("authToken")

        result = await self.biosamples_adapter.submit_sample(
            submission=payload["submissionSample"],
            auth_token=auth_token
        )

        return {
            "message": "Sample submitted to BioSamples.",
            "submissionResult": result,
        }