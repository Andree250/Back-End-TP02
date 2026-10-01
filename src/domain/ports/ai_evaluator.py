from abc import ABC, abstractmethod
from typing import Dict, List, Any

class AIEvaluatorPort(ABC):
    @abstractmethod
    def anonymize_text(self, text: str) -> str:
        """Anonimiza datos personales sensibles (Ley N° 29733)."""
        pass

    @abstractmethod
    def evaluate_tupa_requirements(
        self, 
        procedure_type: str, 
        extracted_docs: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Calcula el cumplimiento de requisitos del TUPA y asigna el score F1."""
        pass
        