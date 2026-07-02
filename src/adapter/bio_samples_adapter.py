import httpx

from typing import Any
from core.decorators import Component
from core.config import settings
from core.logger import get_logger
from domain.bio_samples_api_error import BioSamplesAPIError
from domain.filter_builder import FilterBuilder

logger = get_logger(__name__)

@Component("bio_samples_adapter")
class BioSamplesAdapter:
    base_url = settings.biosamples_base_url
    timeout_seconds = settings.biosamples_timeout_seconds

    def _headers(self, auth_token: str | None = None) -> dict[str, str]:
        headers = {
            "Accept": "application/hal+json",
        }

        if auth_token:
            headers["Authorization"] = f"Bearer {auth_token}"

        return headers

    def _raise_for_error(
        self,
        response: httpx.Response,
        message: str,
    ) -> None:
        if response.status_code < 400:
            return

        raise BioSamplesAPIError(
            message,
            status_code=response.status_code,
            details=[
                {
                    "statusCode": response.status_code,
                    "url": str(response.url),
                    "response": response.text[:1000],
                }
            ],
            retryable=response.status_code >= 500,
        )

    async def _get(
        self,
        path: str,
        params: list[tuple[str, Any]] | None = None,
    ) -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
            response = await client.get(
                f"{self.base_url}{path}",
                params=params,
                headers=self._headers(),
            )

        self._raise_for_error(response, "BioSamples GET API failed.")
        return response.json()

    async def _post(
        self,
        path: str,
        body: dict[str, Any],
        auth_token: str | None = None,
    ) -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
            response = await client.post(
                f"{self.base_url}{path}",
                json=body,
                headers={
                    **self._headers(auth_token),
                    "Content-Type": "application/json",
                },
            )

        self._raise_for_error(response, "BioSamples POST API failed.")
        return response.json()

    async def search_samples(
        self,
        query_terms: str,
        filters: list[dict[str, Any]] | None = None,
        page: int = 0,
        size: int = 10,
        date_range: dict[str, Any] | None = None,
    ) -> dict[str, Any]:

        params: list[tuple[str, Any]] = [
            ("text", query_terms),
            ("page", page),
            ("size", size),
        ]

        for filter_item in filters or []:
            params.append(
                ("filter", FilterBuilder.build(filter_item))
            )

        if date_range:
            field = date_range.get("field")
            from_date = date_range.get("from")
            until_date = date_range.get("until")

            if not field:
                raise BioSamplesAPIError(
                    "Date range requires field.",
                    details=[{"dateRange": date_range}],
                    retryable=False,
                )

            date_value = ""

            if from_date:
                date_value += f"from={from_date}"

            if until_date:
                date_value += f"until={until_date}"

            if date_value:
                params.append(
                    ("filter", f"dt:{field}:{date_value}")
                )

        return await self._get(
            "/samples",
            params=params,
        )

    async def get_sample(
        self,
        accession: str,
    ) -> dict[str, Any]:
        return await self._get(f"/samples/{accession}")

    async def submit_sample(
        self,
        submission: dict[str, Any],
        auth_token:Any,
    ) -> dict[str, Any]:

        if not auth_token:
            raise BioSamplesAPIError(
                "Authentication token is required for BioSamples submission.",
                retryable=False,
            )

        return await self._post(
            "/samples",
            body=submission,
            auth_token=auth_token,
        )