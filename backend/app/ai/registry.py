from __future__ import annotations

from dataclasses import dataclass

from app.ai.schemas import ModelCapabilities


@dataclass(frozen=True)
class RegisteredModel:
    id: str
    provider: str
    model_key: str
    display_name: str
    capabilities: ModelCapabilities
    enabled: bool = True


class ModelRegistry:
    def __init__(self) -> None:
        self._models: dict[str, RegisteredModel] = {}

    def register(self, model: RegisteredModel) -> None:
        self._models[model.id] = model

    def get(self, model_id: str) -> RegisteredModel:
        try:
            return self._models[model_id]
        except KeyError as exc:
            raise KeyError(f"Unknown model: {model_id}") from exc

    def list_enabled(self) -> list[RegisteredModel]:
        return [model for model in self._models.values() if model.enabled]
