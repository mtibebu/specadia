from pydantic import Field

from specadia._agents import SpecadiaBaseModel


class DesignerOutputModel(SpecadiaBaseModel):
  systemArchitecture: str = Field(
      default="",
      description=(
          "The system architecture with textual specification and architecture diagrams using the"
          " mermaid notation."
      ),
  )
  fileStructure: str = Field(default="", description="The file structure for the designed system.")
  componentDesign: str = Field(
      default="",
      description=(
          "Component design consisting of one or more class diagrams and one or more sequence"
          " diagrams drawn using the mermaid notation."
      ),
  )
