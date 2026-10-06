from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.registry import RegisteredModel
from app.db.models import Model, Provider
from app.domain.constants import configured_provider_id


async def ensure_registered_model(
    session: AsyncSession,
    model_id: UUID,
    registered: RegisteredModel,
) -> None:
    # Same provider may be registered concurrently with different model keys.
    await session.execute(
        text("SELECT pg_advisory_xact_lock(:key)"),
        {"key": configured_provider_id(registered.provider).int % (2**63)},
    )
    existing = await session.get(Model, model_id)
    if existing is not None:
        return

    provider_id = configured_provider_id(registered.provider)
    provider = await session.get(Provider, provider_id)
    if provider is None:
        provider = Provider(
            id=provider_id,
            name=registered.provider.title(),
            provider_type=registered.provider,
            status="ACTIVE",
        )
        session.add(provider)
        await session.flush()

    capabilities = registered.capabilities
    session.add(
        Model(
            id=model_id,
            provider_id=provider_id,
            model_key=registered.model_key,
            display_name=registered.display_name,
            status="ACTIVE",
            supports_streaming=capabilities.streaming,
            supports_tools=capabilities.tools,
            supports_parallel_tools=capabilities.parallel_tools,
            supports_structured_output=capabilities.structured_output,
            supports_vision=capabilities.vision,
            supports_reasoning=capabilities.reasoning,
            supports_system_prompt=capabilities.system_prompt,
            context_window=capabilities.context_window,
            max_output_tokens=capabilities.max_output_tokens,
        )
    )
    await session.flush()
