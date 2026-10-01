from typing import Dict, Any
from src.domain.ports.ai_evaluator import AIEvaluatorPort

class ProcessDossierUseCase:
    def __init__(self, ocr_adapter, dossier_repository, ai_evaluator: AIEvaluatorPort):
        self.ocr_adapter = ocr_adapter
        self.dossier_repository = dossier_repository
        self.ai_evaluator = ai_evaluator

    def execute(self, pdf_bytes: bytes, filename: str) -> Dict[str, Any]:
        # 1. OCR / Extracción
        raw_result = self.ocr_adapter.extract_and_classify(pdf_bytes)
        
        # 2. Anonimización PII
        for doc in raw_result.get("documentos", []):
            if "texto" in doc:
                doc["texto_anonimizado"] = self.ai_evaluator.anonymize_text(doc["texto"])
        
        # 3. Evaluación TUPA con IA
        evaluacion_ia = self.ai_evaluator.evaluate_tupa_requirements(
            procedure_type="LICENCIA_EDIFICACION",
            extracted_docs=raw_result.get("documentos", [])
        )
        
        # 4. Consolidado Final
        final_payload = {
            "id": raw_result.get("id"),
            "nombre_archivo": filename,
            "estado": raw_result.get("estado"),
            "evaluacion_tupa": evaluacion_ia,
            "documentos": raw_result.get("documentos")
        }
        
        # 5. Persistencia SQLite
        self.dossier_repository.save(final_payload)
        return final_payload
    