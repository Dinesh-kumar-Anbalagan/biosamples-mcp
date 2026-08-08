from domain.bio_samples_api_error import BioSamplesAPIError

class FilterBuilder:

    @staticmethod
    def build(filter_item: dict) -> str:
        filter_type = filter_item.get("type")

        if filter_type == "attr":
            field = filter_item.get("field")
            value = filter_item.get("value")

            if not field:
                raise BioSamplesAPIError(
                    "Attribute filter requires 'field'.",
                    details=[{"filter": filter_item}],
                    retryable=False,
                )

            if value:
                return f"attr:{field}:{value}"

            return f"attr:{field}"

        if filter_type == "rel":
            field = filter_item.get("field")
            value = filter_item.get("value")

            if not field:
                raise BioSamplesAPIError(
                    "Relationship filter requires 'field'.",
                    details=[{"filter": filter_item}],
                    retryable=False,
                )

            if value:
                return f"rel:{field}:{value}"

            return f"rel:{field}"

        if filter_type == "rrel":
            field = filter_item.get("field")
            value = filter_item.get("value")

            if not field:
                raise BioSamplesAPIError(
                    "Reverse relationship filter requires 'field'.",
                    details=[{"filter": filter_item}],
                    retryable=False,
                )

            if value:
                return f"rrel:{field}:{value}"

            return f"rrel:{field}"

        if filter_type == "name":
            value = filter_item.get("value")

            if not value:
                raise BioSamplesAPIError(
                    "Name filter requires 'value'.",
                    details=[{"filter": filter_item}],
                    retryable=False,
                )

            return f"name:{value}"

        if filter_type == "extd":
            field = filter_item.get("field")
            value = filter_item.get("value")

            if not field or not value:
                raise BioSamplesAPIError(
                    "External data filter requires 'field' and 'value'.",
                    details=[{"filter": filter_item}],
                    retryable=False,
                )

            return f"extd:{field}:{value}"

        if filter_type == "dom":
            value = filter_item.get("value")

            if not value:
                raise BioSamplesAPIError(
                    "Domain filter requires 'value'.",
                    details=[{"filter": filter_item}],
                    retryable=False,
                )

            return f"dom:{value}"

        if filter_type == "acc":
            accession = filter_item.get("accession") or filter_item.get("value")

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