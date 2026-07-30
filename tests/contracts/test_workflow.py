from pathlib import Path

import pytest

from contracts.models import Harness
from contracts.session_store import SessionStore
from contracts.workflow import ApprovalAction
from contracts.workflow import ApprovalDecision
from contracts.workflow import ContractWorkflow
from contracts.workflow import GeneratedDocuments
from contracts.workflow import PartialDocumentsError
from contracts.workflow import WorkflowCancelled


class Gate:

  def __init__(self, decisions: list[ApprovalDecision]):
    self.decisions = decisions
    self.drafts: list[dict[str, object]] = []

  def review(self, draft: dict[str, object], attempt: int) -> ApprovalDecision:
    self.drafts.append(draft)
    return self.decisions.pop(0)


def documents() -> GeneratedDocuments:
  return GeneratedDocuments(
      srs="# Approved Product\n\n## Functional Requirements\n\n- FR-1: Do the approved thing.",
      design="# Design\n\n## Architecture\n\nFR-1 is implemented by a service boundary.",
  )


@pytest.mark.asyncio
async def test_approval_runs_downstream_and_writes_contracts(tmp_path: Path):
  calls: list[str] = []

  async def collect(intent, previous, feedback):
    calls.append("collector")
    return {"FRs": ["Do the approved thing"], "NFRs": []}

  async def downstream(intent, approved):
    calls.append("downstream")
    return documents()

  result = await ContractWorkflow(
      collect, downstream, Gate([ApprovalDecision(ApprovalAction.APPROVE)])
  ).run("Build it", [Harness.CODEX], tmp_path)

  assert calls == ["collector", "downstream"]
  assert result.refinement_count == 0
  assert (tmp_path / "sources" / "srs.md").is_file()
  assert (tmp_path / "sources" / "design.md").is_file()
  assert (tmp_path / "AGENTS.md").is_file()


@pytest.mark.asyncio
async def test_refinement_reruns_only_collector_before_approval(tmp_path: Path):
  events: list[tuple] = []

  async def collect(intent, previous, feedback):
    events.append(("collector", previous, feedback))
    version = 1 if previous is None else 2
    return {"version": version, "FRs": ["Do the approved thing"], "NFRs": []}

  async def downstream(intent, approved):
    events.append(("downstream", approved))
    return documents()

  gate = Gate([
      ApprovalDecision(ApprovalAction.REFINE, "Add audit logging"),
      ApprovalDecision(ApprovalAction.APPROVE),
  ])
  result = await ContractWorkflow(collect, downstream, gate).run(
      "Build it", [Harness.GENERIC], tmp_path
  )

  assert events == [
      ("collector", None, None),
      (
          "collector",
          {"version": 1, "FRs": ["Do the approved thing"], "NFRs": []},
          "Add audit logging",
      ),
      (
          "downstream",
          {"version": 2, "FRs": ["Do the approved thing"], "NFRs": []},
      ),
  ]
  assert result.refinement_count == 1


@pytest.mark.asyncio
async def test_cancel_never_runs_downstream(tmp_path: Path):
  downstream_called = False

  async def collect(intent, previous, feedback):
    return {"FRs": ["Draft"]}

  async def downstream(intent, approved):
    nonlocal downstream_called
    downstream_called = True
    return documents()

  workflow = ContractWorkflow(collect, downstream, Gate([ApprovalDecision(ApprovalAction.CANCEL)]))
  with pytest.raises(WorkflowCancelled):
    await workflow.run("Build it", [Harness.CODEX], tmp_path)

  assert downstream_called is False
  assert list(tmp_path.iterdir()) == []


@pytest.mark.asyncio
async def test_refinement_limit_blocks_downstream(tmp_path: Path):
  downstream_called = False

  async def collect(intent, previous, feedback):
    return {"draft": True}

  async def downstream(intent, approved):
    nonlocal downstream_called
    downstream_called = True
    return documents()

  workflow = ContractWorkflow(
      collect,
      downstream,
      Gate([ApprovalDecision(ApprovalAction.REFINE, "Try again")]),
  )
  with pytest.raises(ValueError, match="Maximum"):
    await workflow.run(
        "Build it",
        [Harness.CODEX],
        tmp_path,
        max_refinements=0,
    )

  assert downstream_called is False


@pytest.mark.asyncio
async def test_existing_contract_refuses_before_writing_sources(tmp_path: Path):
  (tmp_path / "AGENTS.md").write_text("existing", encoding="utf-8")

  async def collect(intent, previous, feedback):
    return {"FRs": ["Approved"]}

  async def downstream(intent, approved):
    return documents()

  workflow = ContractWorkflow(collect, downstream, Gate([ApprovalDecision(ApprovalAction.APPROVE)]))
  with pytest.raises(FileExistsError):
    await workflow.run("Build it", [Harness.CODEX], tmp_path)

  assert not (tmp_path / "sources").exists()
  assert (tmp_path / "AGENTS.md").read_text(encoding="utf-8") == "existing"


@pytest.mark.asyncio
async def test_resume_preserves_approval_and_retries_failed_documents(tmp_path: Path):
  calls = {"collector": 0, "documents": 0}
  store = SessionStore(tmp_path / "sessions")

  async def collect(intent, previous, feedback):
    calls["collector"] += 1
    return {"FRs": ["FR-1: Approved"]}

  async def failing_documents(intent, approved):
    calls["documents"] += 1
    raise ConnectionError("temporary provider failure")

  workflow = ContractWorkflow(
      collect,
      failing_documents,
      Gate([ApprovalDecision(ApprovalAction.APPROVE)]),
      session_store=store,
  )
  with pytest.raises(RuntimeError, match="temporary provider failure"):
    await workflow.run(
        "Build it",
        [Harness.CODEX],
        tmp_path / "out",
        run_id="resume-me",
    )

  checkpoint = store.load("resume-me")
  assert checkpoint.approved_draft == {"FRs": ["FR-1: Approved"]}
  assert checkpoint.status == "failed"

  async def working_documents(intent, approved):
    calls["documents"] += 1
    return documents()

  resumed = ContractWorkflow(
      collect,
      working_documents,
      Gate([]),
      session_store=store,
  )
  await resumed.run(
      "Build it",
      [Harness.CODEX],
      tmp_path / "out",
      run_id="resume-me",
      resume=True,
  )

  assert calls == {"collector": 1, "documents": 2}
  assert store.load("resume-me").status == "complete"


@pytest.mark.asyncio
async def test_stage_fallback_runs_after_primary_failure(tmp_path: Path):
  events: list[str] = []

  async def primary(intent, previous, feedback):
    events.append("primary")
    raise TimeoutError("slow")

  async def fallback(intent, previous, feedback):
    events.append("fallback")
    return {"FRs": ["FR-1: Approved"]}

  async def downstream(intent, approved):
    return documents()

  workflow = ContractWorkflow(
      primary,
      downstream,
      Gate([ApprovalDecision(ApprovalAction.APPROVE)]),
      collector_fallbacks=[fallback],
  )
  await workflow.run("Build it", [Harness.CODEX], tmp_path)

  assert events == ["primary", "fallback"]


@pytest.mark.asyncio
async def test_partial_srs_is_checkpointed_when_design_fails(tmp_path: Path):
  store = SessionStore(tmp_path / "sessions")

  async def collect(intent, previous, feedback):
    return {"FRs": ["FR-1: Approved"]}

  async def downstream(intent, approved):
    raise PartialDocumentsError("design failed", srs="# SRS\n\n## Requirements\n\nFR-1: Approved")

  workflow = ContractWorkflow(
      collect,
      downstream,
      Gate([ApprovalDecision(ApprovalAction.APPROVE)]),
      session_store=store,
  )
  with pytest.raises(PartialDocumentsError):
    await workflow.run(
        "Build it",
        [Harness.CODEX],
        tmp_path / "out",
        run_id="partial",
    )

  assert store.load("partial").srs.startswith("# SRS")


@pytest.mark.asyncio
async def test_quality_failure_can_refine_collector_and_regenerate(tmp_path: Path):
  events: list[tuple[str, object]] = []

  async def collect(intent, previous, feedback):
    events.append(("collector", feedback))
    return {"FRs": ["FR-2: Corrected"]}

  async def downstream(intent, approved):
    events.append(("documents", approved["FRs"][0]))
    if len([event for event in events if event[0] == "documents"]) == 1:
      return GeneratedDocuments("# SRS\n\n## Requirements\n\nTBD", "# Design\n\nTODO")
    return GeneratedDocuments(
        "# SRS\n\n## Functional Requirements\n\nFR-2: Corrected behavior.",
        "# Design\n\n## Architecture\n\nComponent implements FR-2.",
    )

  workflow = ContractWorkflow(
      collect,
      downstream,
      Gate([ApprovalDecision(ApprovalAction.APPROVE)]),
      quality_gate=lambda report: ApprovalDecision(
          ApprovalAction.REFINE, "Add stable IDs and architecture"
      ),
  )
  result = await workflow.run("Build it", [Harness.CODEX], tmp_path)

  assert result.refinement_count == 1
  assert events == [
      ("collector", None),
      ("documents", "FR-2: Corrected"),
      ("collector", "Add stable IDs and architecture"),
      ("documents", "FR-2: Corrected"),
  ]
