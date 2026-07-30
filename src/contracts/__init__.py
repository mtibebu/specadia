"""Generate coding-agent contracts from Specadia specifications.

This top-level namespace is retained for backward compatibility. New
integrations should import :mod:`specadia.contracts`.
"""

from .generator import ContractGenerator
from .models import ContractBundle
from .models import Harness

__all__ = ["ContractBundle", "ContractGenerator", "Harness"]
