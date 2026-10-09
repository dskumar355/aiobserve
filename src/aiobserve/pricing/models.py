from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ModelPricing:
    """Prices expressed per one million tokens in a single currency."""

    provider: str
    model: str
    input_per_million: float = 0.0
    output_per_million: float = 0.0
    cached_input_per_million: float | None = None
    currency: str = "USD"

    def __post_init__(self) -> None:
        if not self.provider.strip() or not self.model.strip():
            raise ValueError("provider and model must be non-empty")
        rates = [self.input_per_million, self.output_per_million]
        if self.cached_input_per_million is not None:
            rates.append(self.cached_input_per_million)
        if any(rate < 0 for rate in rates):
            raise ValueError("Pricing rates cannot be negative")
        if not self.currency.strip():
            raise ValueError("currency must be non-empty")

    def calculate(
        self, input_tokens: int, output_tokens: int, cached_tokens: int = 0
    ) -> tuple[float, float, float]:
        if min(input_tokens, output_tokens, cached_tokens) < 0:
            raise ValueError("Token counts cannot be negative")
        if cached_tokens > input_tokens:
            raise ValueError("cached_tokens cannot exceed input_tokens")
        normal_input = input_tokens - cached_tokens
        cached_price = (
            self.input_per_million
            if self.cached_input_per_million is None
            else self.cached_input_per_million
        )
        input_cost = (
            normal_input / 1_000_000 * self.input_per_million
            + cached_tokens / 1_000_000 * cached_price
        )
        output_cost = output_tokens / 1_000_000 * self.output_per_million
        return input_cost, output_cost, input_cost + output_cost
