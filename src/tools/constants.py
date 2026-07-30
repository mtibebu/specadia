"""Constants for the tools."""

import enum


class OutputType(enum.Enum):
  """Output type for the tools."""

  SRS = "srs"
  DESIGN = "design"
  ARCHITECTURE_DESIGN = "architecture_design"
  UML_SEQUENCE = "uml_sequence"
  UML_CLASS = "uml_class"
