"""Human-approved Specadia pipeline for contract generation."""

import asyncio
import inspect
import uuid
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Awaitable
from typing import Callable
from typing import Protocol

from .generator import ContractGenerator
from .models import ContractBundle
from .models import Harness
from .session_store import RunCheckpoint
from .session_store import SessionStore
from .traceability import build_traceability
from .traceability import write_traceability
from .validation import validate_documents
from .validation import QualityReport
from .writer import write_bundles

CollectorDraft = dict[str, object]
CollectDraft = Callable[
    [str, CollectorDraft | None, str | None],
    Awaitable[CollectorDraft],
]
GenerateDocuments = Callable[
    [str, CollectorDraft],
    Awaitable["GeneratedDocuments"],
]


class ApprovalAction(StrEnum):
  """Available human decisions for a Collector draft."""

  APPROVE = "approve"
  REFINE = "refine"
  CANCEL = "cancel"


@dataclass(frozen=True)
class ApprovalDecision:
  """A human decision about a Collector draft."""

  action: ApprovalAction
  feedback: str | None = None


@dataclass(frozen=True)
class GeneratedDocuments:
  """Documents produced after the Collector draft is approved."""

  srs: str
  design: str


@dataclass(frozen=True)
class WorkflowResult:
  """Outputs from a completed intent-to-contract workflow."""

  approved_draft: CollectorDraft
  documents: GeneratedDocuments
  written_paths: list[Path]
  refinement_count: int


class ApprovalGate(Protocol):
  """Review a Collector draft without coupling the workflow to a UI."""

  def review(
      self, draft: CollectorDraft, attempt: int
  ) -> ApprovalDecision | Awaitable[ApprovalDecision]:
    """Return approve, refine, or cancel."""


class WorkflowCancelled(RuntimeError):
  """Raised when a human cancels before downstream generation."""


class PartialDocumentsError(RuntimeError):
  """A later document stage failed after producing a valid SRS."""

  def __init__(self, message: str, *, srs: str):
    super().__init__(message)
    self.srs = srs


class ContractWorkflow:
  """Run Collector refinement before any downstream Specadia agents."""

  def __init__(
      self,
      collect_draft: CollectDraft,
      generate_documents: GenerateDocuments,
      approval_gate: ApprovalGate,
      contract_generator: ContractGenerator | None = None,
      session_store: SessionStore | None = None,
      progress: Callable[[str, str], None] | None = None,
      collector_fallbacks: list[CollectDraft] | None = None,
      document_fallbacks: list[GenerateDocuments] | None = None,
      quality_gate: (
          Callable[[QualityReport], ApprovalDecision | Awaitable[ApprovalDecision]] | None
      ) = None,
  ):
    self._collect_draft = collect_draft
    self._generate_documents = generate_documents
    self._approval_gate = approval_gate
    self._contract_generator = contract_generator or ContractGenerator()
    self._session_store = session_store
    self._progress = progress
    self._collector_fallbacks = collector_fallbacks or []
    self._document_fallbacks = document_fallbacks or []
    self._quality_gate = quality_gate

  async def run(
      self,
      intent: str,
      harnesses: list[Harness],
      output_dir: Path,
      *,
      project_name: str | None = None,
      max_refinements: int = 5,
      force: bool = False,
      run_id: str | None = None,
      resume: bool = False,
      stage_timeout: float | None = 300,
      cancel_event: asyncio.Event | None = None,
      metadata: dict[str, object] | None = None,
  ) -> WorkflowResult:
    """Generate approved SRS/design documents and coding contracts."""
    if not intent.strip():
      raise ValueError("User intent cannot be empty")
    if max_refinements < 0:
      raise ValueError("max_refinements cannot be negative")
    if not harnesses:
      raise ValueError("At least one harness is required")

    run_id = run_id or uuid.uuid4().hex
    checkpoint = self._checkpoint(
        run_id,
        intent,
        harnesses,
        output_dir,
        project_name,
        resume=resume,
        metadata=metadata or {},
    )
    draft: CollectorDraft | None = checkpoint.approved_draft
    if draft is None and checkpoint.collector_drafts:
      draft = checkpoint.collector_drafts[-1]
    feedback: str | None = None
    refinements = len(checkpoint.feedback)

    try:
      while checkpoint.approved_draft is None:
        self._cancel_if_requested(cancel_event)
        if draft is None or feedback is not None:
          self._emit("collector", "running")
          draft = await self._run_stage(
              "collector",
              [
                  lambda: self._collect_draft(intent, draft, feedback),
                  *(
                      lambda fallback=fallback: fallback(intent, draft, feedback)
                      for fallback in self._collector_fallbacks
                  ),
              ],
              stage_timeout,
          )
          if not draft:
            raise ValueError("Collector returned an empty draft")
          checkpoint.collector_drafts.append(draft)
          checkpoint.touch(stage="collector", status="waiting_for_approval")
          self._save(checkpoint)

        self._emit("approval", "waiting")
        decision = self._approval_gate.review(draft, refinements + 1)
        if inspect.isawaitable(decision):
          decision = await decision

        if decision.action == ApprovalAction.CANCEL:
          checkpoint.touch(stage="approval", status="cancelled")
          self._save(checkpoint)
          raise WorkflowCancelled("Contract generation cancelled before approval")
        if decision.action == ApprovalAction.APPROVE:
          checkpoint.approved_draft = draft
          checkpoint.touch(stage="approval", status="approved")
          self._save(checkpoint)
          break
        if decision.action != ApprovalAction.REFINE:
          raise ValueError(f"Unsupported approval action: {decision.action}")
        if not decision.feedback or not decision.feedback.strip():
          raise ValueError("Refinement feedback cannot be empty")
        if refinements >= max_refinements:
          raise ValueError(f"Maximum Collector refinements reached: {max_refinements}")
        feedback = decision.feedback.strip()
        checkpoint.feedback.append(feedback)
        checkpoint.touch(stage="collector", status="refining")
        self._save(checkpoint)
        refinements += 1

      while True:
        self._cancel_if_requested(cancel_event)
        if checkpoint.srs is not None and checkpoint.design is not None:
          documents = GeneratedDocuments(checkpoint.srs, checkpoint.design)
        else:
          self._emit("documents", "running")
          documents = await self._run_stage(
              "documents",
              [
                  lambda: self._generate_documents(intent, checkpoint.approved_draft or draft),
                  *(
                      lambda fallback=fallback: fallback(intent, checkpoint.approved_draft or draft)
                      for fallback in self._document_fallbacks
                  ),
              ],
              stage_timeout * 4 if stage_timeout else None,
          )
          checkpoint.srs = documents.srs
          checkpoint.design = documents.design
          checkpoint.touch(stage="documents", status="generated")
          self._save(checkpoint)

        quality = validate_documents(documents.srs, documents.design)
        if quality.ok:
          break
        if not self._quality_gate:
          quality.require_valid()
        quality_decision = self._quality_gate(quality)
        if inspect.isawaitable(quality_decision):
          quality_decision = await quality_decision
        if quality_decision.action == ApprovalAction.CANCEL:
          raise WorkflowCancelled("Contract generation cancelled at quality review")
        if (
            quality_decision.action != ApprovalAction.REFINE
            or not quality_decision.feedback
            or not quality_decision.feedback.strip()
        ):
          quality.require_valid()
        if refinements >= max_refinements:
          raise ValueError(f"Maximum Collector refinements reached: {max_refinements}")
        feedback = quality_decision.feedback.strip()
        refinements += 1
        draft = await self._collect_with_fallback(
            intent,
            checkpoint.approved_draft or draft,
            feedback,
            stage_timeout,
        )
        checkpoint.collector_drafts.append(draft)
        checkpoint.feedback.append(feedback)
        checkpoint.approved_draft = draft
        checkpoint.srs = None
        checkpoint.design = None
        checkpoint.touch(stage="quality", status="refined")
        self._save(checkpoint)
      source_dir = output_dir / "sources"
      spec_path = source_dir / "srs.md"
      design_path = source_dir / "design.md"
      targets = list(dict.fromkeys(harnesses))
      planned_paths = [
          spec_path,
          design_path,
          *(output_dir / harness.filename for harness in targets),
          output_dir / "contract-manifest.json",
          output_dir / "traceability.json",
          output_dir / "traceability.md",
      ]
      existing = [path for path in planned_paths if path.exists()]
      if existing and not force:
        names = ", ".join(str(path) for path in existing)
        raise FileExistsError(f"Refusing to overwrite generated files: {names}")

      source_dir.mkdir(parents=True, exist_ok=True)
      spec_path.write_text(documents.srs, encoding="utf-8")
      design_path.write_text(documents.design, encoding="utf-8")

      bundles: list[ContractBundle] = [
          self._contract_generator.generate(
              spec_path=spec_path,
              design_path=design_path,
              harness=harness,
              output_dir=output_dir,
              project_name=project_name,
          )
          for harness in targets
      ]
      written = write_bundles(bundles, force=force)
      traceability = build_traceability(
          checkpoint.approved_draft or draft,
          documents.srs,
          documents.design,
          [bundle.content for bundle in bundles],
      )
      traceability.require_valid()
      trace_paths = write_traceability(traceability, output_dir)
      all_paths = [spec_path, design_path, *written, *trace_paths]
      checkpoint.written_paths = [str(path) for path in all_paths]
      checkpoint.error = None
      checkpoint.touch(stage="complete", status="complete")
      self._save(checkpoint)
      self._emit("complete", "complete")
      return WorkflowResult(
          approved_draft=checkpoint.approved_draft or draft,
          documents=documents,
          written_paths=all_paths,
          refinement_count=refinements,
      )
    except BaseException as error:
      if isinstance(error, PartialDocumentsError):
        checkpoint.srs = error.srs
      checkpoint.error = f"{type(error).__name__}: {error}"
      if checkpoint.status != "cancelled":
        checkpoint.touch(status="failed")
      self._save(checkpoint)
      raise

  def _checkpoint(
      self,
      run_id: str,
      intent: str,
      harnesses: list[Harness],
      output_dir: Path,
      project_name: str | None,
      *,
      resume: bool,
      metadata: dict[str, object],
  ) -> RunCheckpoint:
    if resume:
      if not self._session_store:
        raise ValueError("resume requires a session store")
      checkpoint = self._session_store.load(run_id)
      if checkpoint.intent != intent:
        raise ValueError("Saved run intent does not match")
      if checkpoint.harnesses != [harness.value for harness in harnesses]:
        raise ValueError("Saved run harnesses do not match")
      if checkpoint.output_dir != str(output_dir):
        raise ValueError("Saved run output directory does not match")
      checkpoint.config.update(metadata)
      self._save(checkpoint)
      return checkpoint
    checkpoint = RunCheckpoint(
        run_id=run_id,
        intent=intent,
        harnesses=[harness.value for harness in harnesses],
        output_dir=str(output_dir),
        project_name=project_name,
        config=metadata,
    )
    self._save(checkpoint)
    return checkpoint

  async def _run_stage(
      self,
      stage: str,
      attempts: list[Callable[[], Awaitable]],
      timeout: float | None,
  ):
    errors: list[BaseException] = []
    for index, attempt in enumerate(attempts):
      try:
        operation = attempt()
        return await asyncio.wait_for(operation, timeout) if timeout else await operation
      except (Exception, asyncio.TimeoutError) as error:
        errors.append(error)
        self._emit(stage, f"attempt-{index + 1}-failed")
    if isinstance(errors[-1], PartialDocumentsError):
      raise errors[-1]
    raise RuntimeError(
        f"{stage} failed after {len(attempts)} attempt(s): "
        + "; ".join(f"{type(error).__name__}: {error}" for error in errors)
    ) from errors[-1]

  async def _collect_with_fallback(
      self,
      intent: str,
      draft: CollectorDraft,
      feedback: str,
      timeout: float | None,
  ) -> CollectorDraft:
    result = await self._run_stage(
        "collector",
        [
            lambda: self._collect_draft(intent, draft, feedback),
            *(
                lambda fallback=fallback: fallback(intent, draft, feedback)
                for fallback in self._collector_fallbacks
            ),
        ],
        timeout,
    )
    if not result:
      raise ValueError("Collector returned an empty draft")
    return result

  @staticmethod
  def _cancel_if_requested(cancel_event: asyncio.Event | None) -> None:
    if cancel_event and cancel_event.is_set():
      raise WorkflowCancelled("Contract generation cancelled")

  def _save(self, checkpoint: RunCheckpoint) -> None:
    if self._session_store:
      self._session_store.save(checkpoint)

  def _emit(self, stage: str, status: str) -> None:
    if self._progress:
      self._progress(stage, status)
