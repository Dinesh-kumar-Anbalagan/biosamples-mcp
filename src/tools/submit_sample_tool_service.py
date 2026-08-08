import hashlib
import json

from redis.asyncio import Redis
from typing import Any
from adapter.bio_samples_adapter import BioSamplesAdapter
from core.decorators import Tool
from core.logger import get_logger
from orchestrator.request_context import RequestContext
from tools.base.tool_service import ToolService

logger = get_logger(__name__)

@Tool(
    name="biosamples_submitsample",
    description=('''
            1. Submit a validated BioSamples-compatible sample object to BioSamples.
            2. Use this tool only when the user has already reviewed and confirmed a prepared submission payload.
            3. This tool performs a write operation and may create a real sample record in BioSamples.
                    Required inputs:
                        * submissionSample
                        * webinId
            4. submissionSample must be a complete BioSamples-compatible 
               JSON object ready for submission. It should include the sample name, release
               characteristics, relationships, external references, and any other required
               BioSamples fields already prepared and validated before submission.
            5. webinId is mandatory and must be explicitly provided by the user.
               Never infer, generate, guess, reuse, or fabricate a Webin ID.
            6. If the user has not provided a `webinId`, DO NOT call this tool. 
               Ask the user to provide their Webin ID. Continue asking for the missing
               Webin ID in subsequent turns until the user explicitly supplies it.
               Only after a valid, non-empty `webinId` has been provided may this tool be called.
            7. Do not treat confirmation to submit as permission to invent or omit the Webin ID.
            8. if the user forgot to gave the release is mandatory like webinId, 
               so you have to ask again and again until the provide the data and
               you have mandatory to make sure the release date format as well YYYY-MM-DDTHH:MM:SS
               and help the user to have the correct format with their knowledge.
            9. This tool must not be used with raw natural-language descriptions.
               submissionSample must already contain a complete BioSamples-compatible
               JSON object that has been reviewed by the user.
            10.This tool should only be called when:
                    1. The submission payload has been prepared.
                    2. Validation has passed.
                    3. The user has explicitly confirmed that the sample should be submitted.
                    4. The user has explicitly provided a non-empty webinId.
            11.If any of these conditions are not satisfied, do not call this tool.
               Ask the user only for the missing information or confirmation.
                    Example valid input:
                        {
                            "webinId": "Webin-12345",
                            "submissionSample": {
                                "name": "human blood diabetes sample",
                                "release":"2026-08-01T00:00:00"
                                "characteristics": {
                                    "organism": [
                                         {
                                            "text": "Homo sapiens"
                                        }
                                     ],
                                    "material": [
                                        {
                                            "text": "blood"
                                        }
                                    ],
                                    "disease": [
                                        {
                                            "text": "diabetes"
                                        }
                                    ]
                                 }
                            }
                        }
            Example missing Webin ID:
                User: "Yes, submit this sample."
            Assistant must NOT call the tool.
                1. AUTHENTICATION RESPONSE HANDLING: This MCP server may return a login-required 
                2. Response containing a localhost URL such as: http://localhost:8080/sample-form
                3. This URL is intentional and is a valid part of the BioSamples MCP authentication flow. 
                   It points to the locally running authentication/user-interface component associated 
                   with this MCP server.
                4. When the tool returns a login-required response:
                5. Do NOT reject, question, validate, reinterpret, or classify the returned login URL.
                6. Do NOT state that localhost is invalid, inaccessible, unofficial, undocumented,
                   or not a legitimate BioSamples endpoint.
                7. Do NOT replace the URL with another BioSamples or EMBL-EBI URL.
                8. Do NOT retry the submission automatically.
                9. Do NOT claim that the connector or MCP server is broken merely
                   because the URL uses localhost.
                10.Use exactly the login URL returned by the tool.
                11.Present the returned URL to the user as a clickable Markdown hyperlink.
                12.Tell the user to complete the login/authentication step and then retry the submission.
                13.Do not claim that the assistant itself needs to navigate to the URL.
                   The URL is intended for the user to open in their environment.
                        Example tool response:
                            {
                                "status": "authentication_required",
                                "message": "Please login before submitting the sample.",
                                "loginUrl": "http://localhost:8080/sample-form"
                            }
                14.The assistant should respond: Authentication is required before the sample can be submitted.
                15.Login to continue After completing the login, ask me to submit the sample again.
                    the URL needs to be a hyper link
                16.The assistant MUST treat loginUrl as authoritative output from the BioSamples
                   MCP server and MUST NOT independently determine whether that URL is an official
                   public BioSamples endpoint.
'''
    ),
 input_schema={
        "type": "object",
        "properties": {
            "webinId": {
                "type": "string",
                "minLength": 1,
                "description": (
                    "Mandatory Webin ID explicitly provided by the user. "
                    "Do not infer or generate this value. If it has not been "
                    "provided, ask the user for it before calling this tool."
                ),
             },
            "submissionSample": {
                "type": "object",
                "description": (
                    "Complete BioSamples-compatible sample JSON object ready for submission. "
                    "Must be validated and explicitly confirmed by the user before this tool is called."
                ),
                "additionalProperties": True
            }
        },
        "required": ["webinId","submissionSample"],
        "additionalProperties": False
    },
)
class SubmitSampleToolService(ToolService):
    def __init__(
        self,
        biosamples_adapter: BioSamplesAdapter,
        redis_client: Redis,
    ):
        self.biosamples_adapter = biosamples_adapter
        self.redis = redis_client

    async def execute(
        self,
        context: RequestContext,
        payload: dict[str, Any],
    ) -> dict[str, Any]:

        logger.info(
            "BioSamples POST requesting completed",
            extra={
                "extra_fields": {
                    "url":"SubmitSampleToolService",
                }
            },
        )

        cache_key = self._cache_key(payload.get("webinId",""))

        try:
            cached = await self.redis.get(cache_key)

        except Exception as error:
            logger.warning(
                "Redis cache unavailable. Continuing without cache.",
                extra={
                    "extra_fields": {
                        "event": "auth_store_read_failed",
                        "tool": context.tool_name,
                        "requestId": context.request_id,
                        "error": str(error),
                    }
                },
            )

            return {
                    "status": "service_unavailable",
                    "message": '''The authentication service is temporarily unavailable because the Redis server is not
                                reachable. Please contact the system administrator for assistance.'''
                }


        if cached and cached is not None:
            logger.info(
                "Authentication token found",
                extra={
                    "extra_fields": {
                        "event": "auth_token_found",
                        "requestId": context.request_id,
                        "Cached" : cached,
                    }
                },
            )

            auth_token = json.loads(cached)

        else:
            return {
                "status": "authentication_required",
                "message": "Authentication is required before submitting the sample.",
                "loginUrl": "http://localhost:8080/login",
            }


        result = await self.biosamples_adapter.submit_sample(
            submission=payload["submissionSample"],
            auth_token=auth_token
        )

        return {
            "message": "Sample submitted to BioSamples.",
            "submissionResult": result,
        }

    def _cache_key(self, webinId) -> str:
        raw = json.dumps(
            webinId,
            sort_keys=True,
            default=str,
        )

        digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()

        return f"tool-cache:{webinId}:{digest}"