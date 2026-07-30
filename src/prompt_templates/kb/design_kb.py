"""Prompt snippets for the design knowledge base adopted from the Software Engineer GPT."""

OBJECT_ORIENTED_DESIGN_GUIDELINES = """- identify key classes that users use to describe the problem domain and implementers use to describe the solution domain,
- assign responsibilities to each class,
- provide properties and operations to each class that are needed to carry out these responsibilities,
- come up with an object collaboration so that the objects of the classes can collaborate to carry out the functional requirements of a use case.

You will use classes to model abstractions that are drawn from the problem you are trying to solve or from the technology you are using to implement a solution to that problem. Each of these abstractions is a part of the vocabulary of the system, meaning that, together, they represent the things that are important to users and to implementers. For users, most abstractions are not that hard to identify because they are drawn from the things that users already use to describe their systems. For implementers, these abstractions are typically just the things in the technology that are parts of the solution.

There are two broad categories of classes you need to find: analysis classes and design classes.

An analysis class describes a data abstraction directly drawn from the model of the problem domain. For example, “Plane” in a traffic control system, “Paragraph” in a document processing system, “Part” in an inventory control system. Analysis classes belong to the problem domain or problem space.

A design class describes a software architectural choice. Design classes represent architectural abstractions that help produce elegant, extensible, and maintainable software structures. Those classes can come from various design patterns. Examples include “command” classes in the command pattern, “state” classes in the state pattern, “controller” classes in the MVC pattern, “repository” classes and “service” classes in domain-driven design (DDD), “factory” classes in the factory pattern, “client” classes used to interact with external libraries or API, “adapter” classes in the adapter pattern and so on. Design classes belong to the solution domain or solution space.
"""

HEURISTICS_FOR_FINDING_ANALYSIS_CLASSES = """From the requirements document, you should pay attention to:

- Terms that occur frequently.
- Terms to which the text devotes explicit definitions.
- Terms that are not defined precisely but taken for granted throughout the document.
- Important abstractions of the problem domain.
- Specific jargon of the problem domain.

You must also note that classes can represent conceptual or intangible things as well as material or tangible or physical things in the problem domain.

When you are assessing whether a certain notion should yield a class or not, here is the right criterion: do the objects of the system under discussion exhibit enough specific operations and properties of their own, relevant to the system and not covered by existing classes? If all of the operations and properties that you can identify for a type of objects are irrelevant in this sense or are already covered by the operations and properties of a previously identified class, the conclusion is that the class itself is irrelevant: it must not yield a class. For example, an elevator control system might not include “Floor” as a class because from the point of view of the elevator system, floors have no relevant properties other than those of the associated integer numbers, whereas a Computer Aided Design system designed for architects will have a “Floor” class - since in that case the floor has several specific properties and operations."""

HEURISTICS_FOR_FINDING_DESIGN_CLASSES = """When developing a software system, besides all the things that simulate concepts in the problem domain, you need to come up with some utility classes to model the design abstractions, such as “controller” classes, “service” classes, “repository” classes, “client” classes and so on. They corresponds to the objects in the controllers layer and services layer in the clean architecture. Basically, they are utility classes responsible for interacting with databases, IO, external API, devices, UI, network, libraries, and infrastructures. The Domain-Driven Development (DDD) and the clean architecture are good approaches to follow.

A few guidelines are worth noting:

- Many design classes have been devised by others before. By reading books and articles that describe precise solutions to design problems, you will gain many fruitful ideas. You should consult articles written by the lead designers of various industrial projects who describe their architectural solutions in detail, providing precious guidance to others faced with similar problems in telecommunications, real-time systems, web projects, mobile projects, Computer-Aided Design, artificial intelligence, and other application areas.
- The book on “design patterns” by Gamma et al. has started an effort of capturing proven design solutions and is now being followed by several others.
- Reuse is preferable to invention. You can hope that many of the “patterns” currently being studied will soon cease to be mere ideas, yielding instead directly usable library classes."""

CRITERIA_FOR_REJECTING_CANDIDATE_CLASSES = """
| Danger signal                                                | Why suspicious                                               |
| ------------------------------------------------------------ | ------------------------------------------------------------ |
| Class with verbal name (infinitive or imperative)            | May be a simple subroutine, not a class.                     |
| Fully effective class with only one exported routine         | May be a simple subroutine, not a class.                     |
| Class described as “performing” something                    | May not be a proper data abstraction.                        |
| Class with no routine                                        | May be an opaque piece of information, not an ADT. Or may be an ADT, the routines having just been missed. |
| Class introducing no or very few features (but inherits features from parents) | May be a case of “taxomania”.                                |
| Class covering several abstractions                          | Should be split into several classes, one per abstraction.   |
"""

IDEAL_CLASSES_PROPERTIES = """
- The class provides a crisp abstraction of something drawn from the vocabulary of the problem domain or the solution domain.
- The class name is a noun or adjective, adequately characterizing the abstraction.
- Embodies a small, well-defined set of responsibilities and carries them all out very well.
- The class represents a set of possible run-time objects, its instances. (Some classes are meant to have only one instance during an execution; that is acceptable too.) 
- Several queries are available to find out properties of an instance.
- Several commands are available to change the state of an instance. (In some cases, there are no commands but instead functions producing other objects of the same type, as with the operations on integers; that is acceptable too.)
- Is understandable and simple, yet extensible and adaptable.

This list describes a set of informal goals, not a strict rule. A legitimate class may have only some of the properties listed.

The classes derived from the functional requirements shall conform to the SOLID design principles: Single Responsibility Principle (SRP), Open/Close Principle (OCP), Liskov Substitution Principle (LSP), Dependency Inversion Principle (DIP).
"""
