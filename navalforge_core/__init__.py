"""NavalForge Concept engineering core.

The package is deliberately independent from the web interface and API.
All calculations use SI units internally.
"""

from .evaluator import avaliar_projeto, evaluate_project
from .models import Project

__all__ = ["Project", "avaliar_projeto", "evaluate_project"]
__version__ = "0.1.6"
