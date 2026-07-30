"""A base Pydantic model to apply OpenAI schema requirements."""

from typing import Any
from pydantic import BaseModel


class SpecadiaBaseModel(BaseModel):
  """Pydantic base model whose JSON schema marks all fields as required for OpenAI compatibility."""

  @classmethod
  def model_json_schema(cls, **kwargs: Any) -> dict[str, Any]:
    schema = super().model_json_schema(**kwargs)
    if "properties" in schema:
      schema["required"] = list(schema["properties"].keys())
    return schema
