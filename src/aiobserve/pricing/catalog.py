from __future__ import annotations

from .models import ModelPricing


class PricingCatalog:
    """Explicit pricing rates keyed by provider and model."""

    def __init__(self) -> None:
        self._prices: dict[tuple[str, str], ModelPricing] = {}

    def register(self, pricing: ModelPricing) -> None:
        self._prices[(pricing.provider.lower(), pricing.model)] = pricing

    def get(self, provider: str, model: str) -> ModelPricing | None:
        return self._prices.get((provider.lower(), model))

    def calculate(
        self,
        provider: str,
        model: str,
        input_tokens: int,
        output_tokens: int,
        cached_tokens: int = 0,
    ) -> tuple[float, float, float] | None:
        pricing = self.get(provider, model)
        return None if pricing is None else pricing.calculate(input_tokens, output_tokens, cached_tokens)


DEFAULT_CATALOG = PricingCatalog()
