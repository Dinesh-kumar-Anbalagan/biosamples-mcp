from domain.bio_samples_api_error import BioSamplesAPIError

class FilterBuilder:

    @staticmethod
    def build(filter_item: dict) -> str:
        filter_type = filter_item.get("type")

        if filter_type in {"attr", "rel", "rrel", "name", "extd"}:
            field = filter_item.get("field")
            value = filter_item.get("value")

            if not field or not value:
                raise BioSamplesAPIError(
                    f"{filter_type} filter requires 'field' and 'value'.",
                    details=[{"filter": filter_item}],
                    retryable=False,
                )

            return f"{filter_type}:{field}:{value}"

        elif filter_type == "dom":
            value = filter_item.get("value")

            if not value:
                raise BioSamplesAPIError(
                    "Domain filter requires 'value'.",
                    details=[{"filter": filter_item}],
                    retryable=False,
                )

            return f"dom:{value}"

        elif filter_type == "acc":
            accession = filter_item.get("accession")

            if not accession:
                raise BioSamplesAPIError(
                    "Accession filter requires 'accession'.",
                    details=[{"filter": filter_item}],
                    retryable=False,
                )

            return f"acc:{accession}"

        raise BioSamplesAPIError(
            f"Unsupported filter type: {filter_type}",
            details=[{"filter": filter_item}],
            retryable=False,
        )