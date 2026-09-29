from uuid import NAMESPACE_URL, UUID, uuid5

MOCK_PROVIDER_ID = UUID("00000000-0000-0000-0000-000000000001")
MOCK_MODEL_ID = UUID("00000000-0000-0000-0000-000000000002")
RESEARCH_AGENT_ID = UUID("00000000-0000-0000-0000-000000000003")
RESEARCH_AGENT_VERSION_ID = UUID("00000000-0000-0000-0000-000000000004")


def configured_provider_id(provider_name: str) -> UUID:
    return uuid5(NAMESPACE_URL, f"personal-ai-engineering-workspace:provider:{provider_name}")


def configured_model_id(provider_name: str, model_key: str) -> UUID:
    return uuid5(
        NAMESPACE_URL,
        f"personal-ai-engineering-workspace:model:{provider_name}:{model_key}",
    )
