from dataclasses import dataclass, fields

@dataclass
class BioSamples:
    accession: str | None = None
    name: str | None = None
    release: str | None = None
    update: str | None = None
    organism: str | None = None
    sex: str | None = None
    tissue: str | None = None
    disease: str | None = None
    cell_type: str | None = None

    @classmethod
    def from_dict(cls, data: dict):
        allowed_fields = {field.name for field in fields(cls)}

        filtered_data = {
            key: value
            for key, value in data.items()
            if key in allowed_fields
        }

        return cls(**filtered_data)