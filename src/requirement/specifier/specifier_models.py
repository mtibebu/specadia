from typing import List

from pydantic import BaseModel, Field

from specadia._requirement.analyzer import AnalyzerOutputModel
from specadia._requirement.collector import CollectorOutputModel


class SpecifierInputModel(BaseModel):
  """Input model for the specifier agent that combines collector and analyzer outputs."""

  collector_output: CollectorOutputModel = Field(
      description=(
          "The output from the collector agent containing functional and non-functional"
          " requirements"
      )
  )
  analyzer_output: AnalyzerOutputModel = Field(
      description=(
          "The output from the analyzer agent containing use cases, domain classes, and analysis"
          " results"
      )
  )
