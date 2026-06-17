from typing import Any

from adapter.bio_samples_adapter import BioSamplesAdapter
from core.decorators import Tool
from tools.base.tool_service import ToolService
from orchestrator.request_context import RequestContext

@Tool(
    name="biosamples.get_sample",
    description = (
        "Retrieve one existing BioSamples record using a known BioSamples accession ID. "
        "Use this tool only when the user provides a specific sample accession and wants "
        "to view, inspect, verify, or explore that sample's metadata. "
        "Required input parameter: 'accession' as a string. The accession is the unique "
        "BioSamples sample identifier, commonly starting with SAMEA, SAMN, SAMD, or SAMEG. "
        "Example input payload: {'accession': 'SAMN12345678'}. "
        "Return the sample accession, name, release/update dates, characteristics, "
        "relationships, external references, and available links when present. "
        "This tool is read-only and must not be used to search, create, validate, "
        "prepare, update, or submit BioSamples records. If the user asks for samples "
        "without giving an accession, call biosamples.search_samples instead."
    ),
    input_schema={
            "type": "object",
            "properties": {
                "accession": {
                    "type": "string",
                    "description": (
                        "Required BioSamples accession ID of the sample to retrieve. "
                        "Examples: SAMEA1234567, SAMN12345678, SAMD00000001."
                    )
                }
            },
            "required": ["accession"],
            "additionalProperties": False
        }
)
class GetSampleToolService(ToolService):
    def __init__(self, biosamples_adapter: BioSamplesAdapter):
        self.biosamples_adapter = biosamples_adapter

    async def execute(
        self,
        context: RequestContext,
        payload: dict[str, Any],
    ) -> dict[str, Any]:

        accession = payload["accession"]

        sample = await self.biosamples_adapter.get_sample(accession)

        return {
            "sample": sample
        }