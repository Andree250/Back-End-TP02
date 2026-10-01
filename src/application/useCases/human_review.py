from typing import Dict, Any, List
from datetime import datetime

class HumanReviewUseCase:
    def __init__(self, dossier_repository):
        self.dossier_repository = dossier_repository

    def execute(
        self, 
        dossier_id: str, 
        revisor_id: str, 
        nuevo_estado: str, 
        observaciones: str,
        documentos_convalidados: List[str] = None
    ) -> Dict[str, Any]:
        
        dossier = self.dossier_repository.find_by_id(dossier_id)
        if not dossier:
            return {"error": f"Expediente {dossier_id} no encontrado."}

        payload = dossier.get("payload", {})
        
        registro_auditoria = {
            "fecha_revision": datetime.now().isoformat(),
            "revisor_id": revisor_id,
            "estado_anterior": payload.get("evaluacion_tupa", {}).get("estado_evaluacion"),
            "estado_nuevo": nuevo_estado,
            "observaciones": observaciones,
            "documentos_convalidados": documentos_convalidados or []
        }

        # Actualización de estados
        if "evaluacion_tupa" in payload:
            payload["evaluacion_tupa"]["estado_evaluacion"] = nuevo_estado
            payload["evaluacion_tupa"]["requiere_revision_humana"] = False
        
        payload["estado"] = "REVISADO_POR_HUMANO"
        payload["auditoria_humana"] = registro_auditoria

        self.dossier_repository.save(payload)

        return {
            "mensaje": "Dictamen corregido y validado exitosamente por el evaluador.",
            "expediente_id": dossier_id,
            "nuevo_estado": nuevo_estado,
            "auditoria": registro_auditoria
        }
    