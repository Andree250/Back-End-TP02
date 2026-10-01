from typing import Dict, List, Any
from src.domain.ports.ai_evaluator import AIEvaluatorPort
from src.infrastructure.adapters.output.pii_anonymizer import PIIAnonymizerAdapter

class TUPAIEvaluatorAdapter(AIEvaluatorPort):
    def __init__(self):
        self.anonymizer = PIIAnonymizerAdapter()
        # Matriz normativa TUPA Municipalidad Provincial de Huancayo
        self.tupa_rules = {
            "LICENCIA_EDIFICACION": ["FUT", "DNI", "PLANO", "MEMORIA_DESCRIPTIVA"]
        }

    def anonymize_text(self, text: str) -> str:
        return self.anonymizer.anonymize(text)

    def evaluate_tupa_requirements(
        self, 
        procedure_type: str, 
        extracted_docs: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        
        required_docs = self.tupa_rules.get(procedure_type, self.tupa_rules["LICENCIA_EDIFICACION"])
        detected_types = {doc.get("tipo", "").upper() for doc in extracted_docs if doc.get("tipo")}

        detected_list = list(detected_types)
        missing_list = [req for req in required_docs if req not in detected_types]
        
        is_complete = len(missing_list) == 0
        confidence_score = round(len(detected_list) / len(required_docs), 2) if required_docs else 0.0

        return {
            "procedimiento": procedure_type,
            "estado_evaluacion": "COMPLETO" if is_complete else "INCOMPLETO",
            "requisitos_exigidos": required_docs,
            "requisitos_detectados": detected_list,
            "requisitos_faltantes": missing_list,
            "confianza_f1": min(confidence_score, 1.0),
            "requiere_revision_humana": not is_complete or confidence_score < 0.85
        }
    