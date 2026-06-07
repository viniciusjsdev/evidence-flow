"""JSON Schema validation for harness contracts."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

try:
    from jsonschema import Draft202012Validator as JsonSchemaValidator
except ImportError:  # pragma: no cover - compatibility with older system jsonschema
    from jsonschema import Draft7Validator as JsonSchemaValidator

from evidence_flow.harness.io import read_structured


class ContractValidationError(ValueError):
    """Raised when a payload does not satisfy a harness contract."""


@dataclass(frozen=True)
class ContractValidator:
    """Load and validate JSON Schema contracts from the repository."""

    contracts_dir: Path

    def schema_path(self, contract_name: str) -> Path:
        path = self.contracts_dir / f"{contract_name}.schema.json"
        if not path.exists():
            raise FileNotFoundError(f"Unknown contract: {contract_name}")
        return path

    def load_schema(self, contract_name: str) -> dict[str, Any]:
        schema = read_structured(self.schema_path(contract_name))
        if not isinstance(schema, dict):
            raise ContractValidationError(f"Schema is not an object: {contract_name}")
        return schema

    def validate_payload(self, payload: Any, contract_name: str) -> None:
        schema = self.load_schema(contract_name)
        validator = JsonSchemaValidator(schema)
        errors = sorted(validator.iter_errors(payload), key=lambda error: list(error.path))
        if errors:
            first = errors[0]
            location = ".".join(str(part) for part in first.path) or "<root>"
            raise ContractValidationError(
                f"{contract_name} validation failed at {location}: {first.message}"
            )

    def validate_file(self, path: Path, contract_name: str) -> Any:
        payload = read_structured(path)
        self.validate_payload(payload, contract_name)
        return payload
