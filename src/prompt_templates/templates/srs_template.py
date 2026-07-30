"""Prompt snippet for the IEEE 830-1984 SRS template adopted from https://raw.githubusercontent.com/jam01/SRS-Template/refs/heads/master/srs-template-bare.md."""

IEEE_830_SRS_TEMPLATE = """
Header
- Software Requirements Specification
- For [project name] (replace)
- Version (from input or "0.1 (missing)")
- Prepared by [author] (from input or "missing")
- [organization] (from input or "missing")
- [date_modified] (from input or current date if provided; else "missing")

Table of Contents (keep same structure)

Revision History (fill rows with changes from inputs or mark initial)

1. Introduction
- 1.1 Document Purpose (2–4 sentences drawn from inputs)
- 1.2 Product Scope (concise product name/version, purpose, key capabilities, boundaries)
- 1.3 Definitions, Acronyms, and Abbreviations (alphabetized glossary from inputs)
- 1.4 References (list input references with title, owner, version, date, URL, normative/informative)
- 1.5 Document Overview (structure and conventions used)

2. Product Overview
- 2.1 Product Perspective (new product/replacement/part of family; interfaces to other systems from inputs)
- 2.2 Product Functions (5–10 concise bullet major functions extracted from collector_output)
- 2.3 Product Constraints (design/implementation constraints present in inputs)
- 2.4 User Characteristics (personas/roles from analyzer_output or collector; include capabilities and needs)
- 2.5 Assumptions and Dependencies (explicit list from inputs)
- 2.6 Apportioning of Requirements (requirements deferred to later releases; only if present in inputs)

3. Requirements
- 3.1 External Interfaces (detailed interface requirements from collector_output: GUI, API, hardware, communication protocols)
- 3.2 Functional Requirements
  - Provide a Template and use it for every FR:
    - ID:
    - Title:
    - Description:
    - Rationale / business value:
    - Source (collector reference):
    - Priority:
    - Preconditions:
    - Trigger:
    - Postconditions / success criteria:
    - Related Use Cases (IDs from analyzer_output.useCases):
    - Related Business Rules (IDs from analyzer_output.businessRules):
    - Related Domain Classes / Data Elements:
    - Acceptance Criteria (testable)
    - Verification Method (inspection, test, demonstration)
    - Dependencies:
    - Notes / constraints
  - List all FRs from collector_output filled into this template. If additional FR detail appears in analyzer outputs (use cases), incorporate and cite.

- 3.3 Quality of Service (non-functional requirements)
  - For each NFR, specify measurable acceptance criteria and verification methods (performance, scalability, availability, security, maintainability, usability). Use inputs; if unspecified, mark missing and follow missing-data rule.

- 3.4 Compliance (laws, standards, policies from inputs)
- 3.5 Design and Implementation Constraints (explicit constraints from inputs)
- 3.6 AI/ML (if present in inputs: data needs, model behavior, training/serving constraints, evaluation metrics; otherwise mark missing)

Overview of Data Requirements (explicit required section)
- Provide a concise overview of data requirements: data elements, types, cardinality, retention, privacy classification, access control, expected volumes, formats.
- Include any data dictionaries present in inputs.

User View of Product Use (explicit required section)
- For each primary persona/role, provide 2–3 concise usage scenarios derived from use cases and describe typical workflows and goals.

Template for Describing Functional Requirements (include the template above here once; all FRs must use it)

4. Verification
- For each requirement (functional and non-functional), list verification method and acceptance criteria. Provide a traceability table mapping requirement IDs to verification methods and related use cases/tests.

5. Appendixes
- Appendix A: Business Rules (list all from analyzer_output.businessRules with IDs and full text)
- Appendix B: Domain Classes and Data Model
  - Insert analyzer_output.domainClasses diagram (or mark missing)
  - Insert analyzer_output.dataModel diagram (or mark missing)
  - If diagrams are images not present, include textual class listings and data model summary from inputs.
- Appendix C: Use Cases (full text from analyzer_output.useCases, each with ID, actors, main flow, alternate flows)
- Appendix D: Traceability Matrices
  - FR → Use Case
  - FR → Business Rule
  - FR → Domain Class / Data Element
"""
