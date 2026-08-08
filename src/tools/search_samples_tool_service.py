from typing import Any
from adapter.bio_samples_adapter import BioSamplesAdapter
from core.decorators import Tool
from orchestrator.request_context import RequestContext
from tools.base.tool_service import ToolService

@Tool(
    name="biosamples_searchsamples",
    description=( '''
            1. Search existing BioSamples records using natural-language or structured search criteria.
            2. This tool is read-only. It only searches existing BioSamples records.
            3. It does not create, validate, prepare, update, or submit samples.
            4. IMPORTANT INPUT FORMAT: The tool must receive a JSON object with these keys:
                {'query': string, 'filters': array, 'page': integer, 'size': integer}.
                Required input: 'query'.
            5.'query' must be a string containing the main searchable keyword or phrase extracted
               from the user's natural-language request. Use this for sample material, disease, tissue,
               organism, or other biomedical search terms.
                Examples for query: 'blood', 'liver cancer', 'human blood diabetes','liver biopsy cirrhosis'.
            6. Optional input: 'filters'.
                'filters' must be an array of filter objects. Each filter object must contain a 'type' field.
            7. Supported filter types are: attr, acc, rel, rrel, dom, name, and extd.
            8. Date filtering is supported separately through the dateRange property
                1. Attribute filter format:{'type': 'attr', 'field': '<attribute name>', 'value': '<attribute value>'}.
                2. BioSamples filter format: attr:<field>:<value>.
                3. Use attr filters for organism, disease, tissue, material, sex, and geographic location.
                    Example: {'type': 'attr', 'field': 'organism', 'value': 'Homo sapiens'}.
            9. Accession filter format: 
                {'type': 'acc', 'accession': '<sample accession>'}.
                BioSamples format: acc:<accession>. Supports wildcards.
                Example: {'type': 'acc' ,'value': 'SAMN*'}.
            10.Relationship filter format:
                {'type': 'rel', 'field': '<relation type>', 'value': '<target accession>'}.
                BioSamples format: rel:<relation_type>:<accession>.
            11.Reverse relationship filter format:
                {'type': 'rrel', 'field': '<relation type>', 'value': '<source accession>'}.
                BioSamples format: rrel:<relation_type>:<accession>.
            12.Domain filter format:
                {'type': 'dom', 'value': '<domain>'}.
                BioSamples format: dom:<domain>.
                Example: {'type': 'dom', 'value': 'self.BioSamples'}.
            14.Name filter format: "
                {'type': 'name', 'value': '<sample name>'}.
                BioSamples format: name:<sample name>. Use this for exact sample name filtering.
            15.External reference data filter format: "
                {'type': 'extd', 'field': '<archive>', 'value': '<external ID>'}.
                BioSamples format: extd:<archive>:<external ID>.
            16.Date range format: do not add date in the filter field
                {'type': 'dt', 'field': 'release' or 'update', 'from': 'YYYY-MM-DD', 'until': 'YYYY-MM-DD'}.
                BioSamples filter format: dt:<release|update>:from=<date>until=<date>.
            17.Use ISO 8601 date format.
                Example: {'type': 'dt', 'field': 'release', 'from': '2020-01-01', 'until': '2024-12-31'}.
                If only a start date is known, send only 'from'.
                If only an end date is known, send only 'until'.
            18.Optional input: 'page'.
                'page' must be an integer zero-based page number. Default is 0.
            19.Optional input: 'size'.
                'size' must be an integer result count per page. Default is 10.
            20.OUTPUT REQUIREMENT (mandatory): The calling assistant MUST display this tool's JSON response to
               the user in full and verbatim, exactly as returned, with no summarization, paraphrasing,
               reformatting into prose, or omission of any field, A raw JSON code block is the expected presentation."
            '''
    ),
    input_schema={
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description":
                    ("Main searchable keyword or phrase extracted from the user's natural-language request."
                      "for examples: 'blood', 'liver cancer', 'human blood diabetes','liver biopsy cirrhosis'."
                    )
            },
            "filters": {
                "type": "array",
                "description": "Structured BioSamples filters.",
                "items": {
                    "type": "object",
                    "properties": {
                        "type": {
                            "type": "string",
                            "enum": [
                                "attr",
                                "acc",
                                "rel",
                                "rrel",
                                "dom",
                                "name",
                                "extd",
                            ],
                        },
                        "field": {
                            "type": "string",
                            "description": (
                                    "Field/relation/archive name when required "
                                    "by the selected filter type."
                            ),
                        },
                        "value": {
                            "type": "string",
                            "description": "Filter value when applicable.",
                        },
                        "accession": {
                            "type": "string",
                            "description": "Sample accession for accession filters.",
                        },
                    },
                    "required": ["type"],
                    "additionalProperties": False,
                },
            },
            "dateRange": {
                "type": "object",
                "description": "Optional date range filter.",
                "properties": {
                    "field": {
                        "type": "string",
                        "description": "Date field to filter on, for example release."
                    },
                    "from": {
                        "type": "string",
                        "format": "date",
                        "description": "Start date in YYYY-MM-DD format."
                    },
                    "until": {
                        "type": "string",
                        "format": "date",
                        "description": "to date in YYYY-MM-DD format."
                    }
                },
            },
            "page": {
                "type": "integer",
                "default": 0
            },
            "size": {
                "type": "integer",
                "default": 10
            }
        },
        "required": ["query"]
    },
)
class SearchSamplesToolService(ToolService):
    def __init__(
            self,
            biosamples_adapter: BioSamplesAdapter,
    ):
        self.biosamples_adapter = biosamples_adapter

    async def execute(
            self,
            context: RequestContext,
            payload: dict[str, Any],
    ) -> dict[str, Any]:
        query = payload.get("query", "")
        page = payload.get("page", 0)
        size = payload.get("size", 10)
        filters = payload.get("filters", [])
        date_range = payload.get("dateRange", {})

        result = await self.biosamples_adapter.search_samples(
            query_terms=query,
            filters=filters,
            page=page,
            size=size,
            date_range=date_range
        )

        samples = result.get("_embedded", {}).get("samples", [])
        page_info = result.get("page", {})

        return {
            "samples": samples,
            "page": {
                "size": page_info.get("size", size),
                "number": page_info.get("number", page),
                "totalElements": page_info.get("totalElements", 0),
                "totalPages": page_info.get("totalPages", 0),
            },
        }

