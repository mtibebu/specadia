"""Adapter from the contract workflow to the existing Specadia agents."""

import asyncio
import json
from pathlib import Path
from typing import Any

from specadia._agents.prompt_safety import require_bounded_strings
from specadia._agents.prompt_safety import untrusted_json
from specadia._agents.prompt_safety import untrusted_text

from .workflow import CollectorDraft
from .workflow import GeneratedDocuments
from .workflow import PartialDocumentsError


class SpecadiaPipeline:
  """Run Collector separately, then the approved downstream agent chain."""

  def __init__(
      self,
      llm_model_name: str,
      *,
      rag: bool = False,
      rag_collection: str = "default",
      rag_index_dir: Path = Path(".specadia/rag"),
      stage_timeout: float | None = 300,
  ):
    self._llm_model_name = llm_model_name
    self._rag = rag
    self._rag_collection = rag_collection
    self._rag_index_dir = rag_index_dir
    self._stage_timeout = stage_timeout

  async def collect(
      self,
      intent: str,
      previous_draft: CollectorDraft | None = None,
      feedback: str | None = None,
  ) -> CollectorDraft:
    """Run only Collector, optionally refining its previous draft."""
    from specadia._orchestrator.orchestrator import run_agent
    from specadia._requirement import CollectorAgent
    from specadia._utils.constants import AgentRunMode

    query = (
        "Extract requirements from the following user-provided intent.\n\n"
        f"{untrusted_text('user intent', intent)}"
    )
    if previous_draft is not None:
      query = (
          "Refine the requirements draft using the human feedback below. Preserve useful "
          "approved details, resolve the feedback, and return a complete replacement draft.\n\n"
          f"{untrusted_text('original user intent', intent)}\n\n"
          f"{untrusted_json('previous Collector draft', previous_draft)}\n\n"
          f"{untrusted_text('human feedback', feedback or '')}"
      )

    state: dict[str, Any] = {}
    response = await run_agent(
        query,
        CollectorAgent(
            self._llm_model_name,
            run_mode=AgentRunMode.MAIN,
            rag=self._rag,
            rag_source=self._rag_collection,
            rag_index_dir=self._rag_index_dir,
        ).get_agent(),
        run_mode=AgentRunMode.MAIN,
        state_collector=state,
    )
    draft = state.get("collector_output")
    if isinstance(draft, dict):
      require_bounded_strings(draft, label="Collector output")
      return draft
    if hasattr(draft, "model_dump"):
      result = draft.model_dump()
      require_bounded_strings(result, label="Collector output")
      return result
    try:
      parsed = json.loads(response)
    except (TypeError, json.JSONDecodeError) as error:
      raise ValueError("Collector did not return structured requirements") from error
    if not isinstance(parsed, dict):
      raise ValueError("Collector response must be a JSON object")
    require_bounded_strings(parsed, label="Collector output")
    return parsed

  async def generate_documents(
      self,
      intent: str,
      approved_draft: CollectorDraft,
  ) -> GeneratedDocuments:
    """Run Analyzer onward with the human-approved Collector state."""
    from specadia._design import DesignerAgent
    from specadia._design import DocumenterAgent
    from specadia._orchestrator.orchestrator import run_agent
    from specadia._requirement import AnalyzerAgent
    from specadia._requirement import SpecifierAgent
    from specadia._utils.constants import AgentRunMode

    require_bounded_strings(approved_draft, label="approved Collector output")

    state: dict[str, Any] = {"collector_output": approved_draft}
    await self._run_stage(
        "analyzer",
        run_agent(
            json.dumps(approved_draft),
            AnalyzerAgent(
                self._llm_model_name,
                run_mode=AgentRunMode.MAIN,
                rag=self._rag,
            ).get_agent(),
            run_mode=AgentRunMode.MAIN,
            state_collector=state,
            initial_state=state,
        ),
    )
    analyzer_result = state.get("analyzer_output")
    require_bounded_strings(analyzer_result, label="Analyzer output")
    if hasattr(analyzer_result, "model_dump"):
      raw_for_schema = analyzer_result.model_dump()
    elif isinstance(analyzer_result, str):
      raw_for_schema = json.loads(analyzer_result)
    elif isinstance(analyzer_result, dict):
      raw_for_schema = analyzer_result
    else:
      raw_for_schema = json.loads(str(analyzer_result))

    await self._run_stage(
        "specifier",
        run_agent(
            json.dumps(
                {
                    "collector_output": approved_draft,
                    "analyzer_output": raw_for_schema,
                },
                default=_json_default,
            ),
            SpecifierAgent(
                self._llm_model_name,
                run_mode=AgentRunMode.MAIN,
                rag=self._rag,
            ).get_agent(),
            run_mode=AgentRunMode.MAIN,
            state_collector=state,
            initial_state=state,
        ),
    )
    srs = _state_text(state, "specifier_output")
    require_bounded_strings(srs, label="Specifier output")

    try:
      designer_input = (
          "Create the implementation-ready system and component design from the exact SRS "
          "below.\n\n"
          "Grounding rules:\n"
          "- Treat this SRS as the only authoritative source.\n"
          "- Preserve every FR-* and NFR-* ID exactly and map each one into the design.\n"
          "- Do not create REQ-* replacements.\n"
          "- Do not introduce named technologies, protocols, products, regulations, APIs, "
          "roles, or features unless the SRS explicitly names them.\n"
          "- Mark an implementation choice as unspecified when the SRS does not select it.\n"
          "- Return only the structured designer output requested by your system prompt.\n\n"
          f"{untrusted_text('approved user intent', intent)}\n\n"
          f"{untrusted_text('authoritative SRS', srs)}"
      )
      await self._run_stage(
          "designer",
          run_agent(
              designer_input,
              DesignerAgent(
                  self._llm_model_name,
                  run_mode=AgentRunMode.MAIN,
                  rag=self._rag,
              ).get_agent(),
              run_mode=AgentRunMode.MAIN,
              state_collector=state,
              initial_state=state,
          ),
      )
      designer_output = _state_text(state, "designer_output")
      require_bounded_strings(designer_output, label="Designer output")

      documenter_input = (
          "Write the final software design document using only the authoritative SRS and "
          "designer output below.\n\n"
          "Grounding rules:\n"
          "- Preserve every FR-* and NFR-* ID exactly and include all of them.\n"
          "- Do not create REQ-* replacements.\n"
          "- Do not add or infer named technologies, protocols, products, regulations, APIs, "
          "roles, features, or compliance claims absent from the SRS.\n"
          "- If designer output conflicts with or exceeds the SRS, discard that content.\n"
          "- Return only the final design document.\n\n"
          f"{untrusted_text('authoritative SRS', srs)}\n\n"
          f"{untrusted_text('grounded Designer output', designer_output)}"
      )
      await self._run_stage(
          "documenter",
          run_agent(
              documenter_input,
              DocumenterAgent(
                  self._llm_model_name,
                  run_mode=AgentRunMode.MAIN,
                  rag=self._rag,
              ).get_agent(),
              run_mode=AgentRunMode.MAIN,
              state_collector=state,
              initial_state=state,
          ),
      )
      design = _state_text(state, "documenter_output")
    except Exception as error:
      raise PartialDocumentsError(f"Design generation failed: {error}", srs=srs) from error
    return GeneratedDocuments(srs=srs, design=design)

  async def _run_stage(self, stage: str, operation):
    try:
      if self._stage_timeout:
        return await asyncio.wait_for(operation, self._stage_timeout)
      return await operation
    except asyncio.TimeoutError as error:
      raise TimeoutError(f"{stage} timed out after {self._stage_timeout:g} seconds") from error


def _state_text(state: dict[str, Any], key: str) -> str:
  value = state.get(key)
  if isinstance(value, str):
    return value
  if hasattr(value, "model_dump_json"):
    return value.model_dump_json(indent=2)
  if value is not None:
    return json.dumps(value, indent=2, default=str)
  raise ValueError(f"Specadia downstream pipeline did not produce {key}")


def _json_default(value: Any) -> Any:
  if hasattr(value, "model_dump"):
    return value.model_dump()
  raise TypeError(f"Object of type {type(value).__name__} is not JSON serializable")
