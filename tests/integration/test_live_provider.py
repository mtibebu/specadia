"""Opt-in live provider smoke test.

Run with SPECADIA_LIVE_MODEL set to a configured provider-qualified model.
"""

import os

import pytest

from specadia._contracts.specadia_pipeline import SpecadiaPipeline


@pytest.mark.asyncio
@pytest.mark.live
async def test_live_collector_returns_structured_requirements():
  model = os.getenv("SPECADIA_LIVE_MODEL")
  if not model:
    pytest.skip("Set SPECADIA_LIVE_MODEL to run provider smoke tests")

  draft = await SpecadiaPipeline(model, rag=False).collect(
      "A minimal service that returns a health status."
  )

  assert isinstance(draft, dict)
  assert draft
