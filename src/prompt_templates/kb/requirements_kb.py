"""Prompt snippets for the requirements knowledge base adopted from the Software Engineer GPT."""

REQUIREMENT_TYPES = """
  1. Business requirements
  2. Features and user stories
  3. Functional requirements (FRn: The system shall ...) — testable and granular
  4. Non-functional requirements / quality attributes (NFRn)
  5. Business rules
  6. External interface requirements
  7. Constraints (hardware, language, banned libraries, build system)
  8. Data requirements and persistence
"""

USER_REQUIREMENTS_DESCRIPTION = """
User requirements describe goals or tasks the users must be able to perform with the system-to-be that will provide value to some stakeholders. User requirements are also known as user needs, user goals, tasks need to be done with the system-to-be. This is a user-centric and usage-centric requirements engineering approach. User requirements are usually elicited by business analysts and user representatives or a product manager depending on the type of the software (Software for internal corporate use or Software for commercial sale). They must align with the context and objectives that the business requirements and features establish. User requirements are most typically represented as use cases, scenarios, or user stories.

User requirements are most typically represented as use cases, scenarios, or user stories.
"""

FUNCTIONAL_REQUIREMENTS_DESCRIPTION = """
Functional requirements are the software capabilities that must be implemented by the developers for the user to carry out a feature’s service or to perform a use case. Functional requirements often are written from the perspective of the system-to-be and in the form of the traditional “The system shall” statements. A business analyst documents these functional requirements in the Software Requirements Specification (SRS). Then how does a business analyst write functional requirements?

Many functional requirements fall right out of the dialog steps between the actor and the system. Such as, “The system shall assign a unique sequence number to each request.” Other functional requirements don't appear in the use case description. Such as what the system shall do if a precondition is not satisfied.

Preconditions and postconditions are also important sources of functional requirements. Preconditions define prerequisites that must be met before the system can begin executing the use case. The system should be able to test all preconditions to see if it's possible to proceed with the use case. Postconditions describe the state of the system after the use case is executed successfully. Postconditions can describe:

- Something observable to the user (“The system displays an account balance.”)
- Physical outcomes (“The ATM has dispensed money and printed a receipt.”)
- Internal system state changes (“The account has been debited by the amount of a cash withdrawal, plus any transaction fees.”)

Many postconditions are evident to the user, because they reflect the outcome that delivers user value, for example “I've got my cash from the ATM.” However, no user will ever tell a business analyst that the system should reduce its record of the amount of cash remaining in the ATM by the amount the user just withdrew. Users neither know nor care about such internal housekeeping details. But developers and testers need to know about them, which means that the business analyst needs to discover those, perhaps by working with a subject matter expert, and record them as additional postconditions.

Some error conditions could affect multiple use cases or multiple steps in a use case's normal flow. Examples are a loss of network connectivity, a database failure partway through an operation, or a physical device failure such as a paper jam. Treat these as additional functional'requirements to be implemented, instead of repeating them as exceptions for all the potentially affected use cases. The goal is not to force-fit all known functionality into a use case. You're employing usage-centric elicitation to try to discover as much of the essential system functionality as you can.

Granularity of functional requirements. Write individually testable functional requirements. If you can think of a small number of related test cases to verify that a requirement was correctly implemented, it is probably at an appropriate granularity. If you envision numerous and diverse tests, perhaps several requirements are combined and ought to be separated.
"""

NON_FUNCTIONAL_REQUIREMENTS_DESCRIPTION = """
Non-functional requirements are requirements that describe the non-functional properties of the system-to-be. Non-functional requirements are also known as quality attributes, non-functional requirements, or constraints. Non-functional requirements are usually elicited by business analysts and user representatives or a product manager depending on the type of the software (Software for internal corporate use or Software for commercial sale). They must align with the context and objectives that the business requirements and features establish. Non-functional requirements are most typically represented as quality attributes, constraints, or data requirements. Non-functional requirements are most typically represented as quality attributes, constraints, or data requirements.
"""
