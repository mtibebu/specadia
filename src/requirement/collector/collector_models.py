from typing import List

from pydantic import Field

from agents import SpecadiaBaseModel


class CollectorOutputModel(SpecadiaBaseModel):
  FRs: List[str] = Field(default_factory=list, description="The list of functional requirements")

  NFRs: List[str] = Field(default_factory=list, description="List of non-functional requirements")
