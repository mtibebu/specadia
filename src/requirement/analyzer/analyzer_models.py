from typing import List

from pydantic import Field

from agents import SpecadiaBaseModel


class AnalyzerOutputModel(SpecadiaBaseModel):
  useCases: List[str] = Field(
      default_factory=list,
      description=(
          "The list of business use cases as simple string descriptions (e.g., 'Customer registers"
          " for an account')."
      ),
  )
  domainClasses: str = Field(
      default="",
      description="The analysis business classes in the mermaid notation",
  )
  businessRules: List[str] = Field(default_factory=list, description="The list of business rules")
  dataModel: str = Field(
      default="",
      description="The data model as an ER and DFD in mermaid notation",
  )
  traceability: List[str] = Field(
      default_factory=list, description="The requirements traceability matrix"
  )
  validation: List[str] = Field(
      default_factory=list, description="The requirements validation output"
  )
