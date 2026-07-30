"""Tool to save a string to a file."""

from pathlib import Path
from typing import Optional

from loguru import logger

from utils.logger import get_log_path

from .constants import OutputType


def _get_output_file_name(output_type: OutputType) -> Optional[Path]:
  """Get the output file path based on the output type.

  Args:
      output_type: The agent output type, including srs, design, architecture_design, uml_class, and uml_sequence content.

  Returns:
      The full Path to the output file, or None if the log path is not set.
  """
  logger_path = get_log_path()
  if logger_path is None:
    logger.warning("Log path is not set. Cannot save file.")
    return None

  file_path = logger_path / f"{output_type.value}.md"
  return file_path


def save_to_file(file_content: str, output_type: str) -> str:
  """Saves the provided content to a file.

  Args:
      file_content: The string content to save.
      output_type: The agent output type, including srs, design, architecture_design, UML_class, and UML_sequence content.

  Returns:
      A message indicating success or failure.
  """
  # Convert string to enum if possible
  try:
    enum_type = OutputType(output_type.lower())
  except ValueError:
    enum_type = output_type

  file_path = _get_output_file_name(enum_type)
  if file_path is None:
    return "Failed to save file: Log directory not found."

  try:
    with open(file_path, "w", encoding="utf-8") as f:
      f.write(file_content)
    logger.info(f"Saved {output_type} to {file_path}")
    return f"Successfully saved {output_type} to {file_path}"
  except Exception as e:
    error_msg = f"Failed to save {output_type}: {str(e)}"
    logger.error(error_msg)
    return error_msg
