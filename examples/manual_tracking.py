from aiobserve import configure, record, get_observer
from aiobserve.pricing import ModelPricing, PricingCatalog

pricing = PricingCatalog()
pricing.register(ModelPricing(
    provider="demo",
    model="demo-model",
    input_per_million=0.50,
    output_per_million=1.50,
))

configure(project="example-app", environment="development", pricing=pricing)
record(provider="demo", model="demo-model", input_tokens=1200, output_tokens=350, latency_ms=420)
print(get_observer().summary())
