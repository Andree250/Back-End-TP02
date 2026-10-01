from typing import Dict, Any

class GenerateTupaDictamenUseCase:
    def __init__(self, dossier_repository):
        self.dossier_repository = dossier_repository

    def execute(self, dossier_id: str) -> Dict[str, Any]:
        dossier = self.dossier_repository.find_by_id(dossier_id)
        if not dossier:
            return {"error": f"Expediente {dossier_id} no encontrado."}

        payload = dossier.get("payload", {})
        evaluacion = payload.get("evaluacion_tupa", {})
        
        return {
            "dictamen_id": f"DICT-MPH-{dossier_id[:8].upper()}",
            "expediente_id": dossier_id,
            "entidad": "Municipalidad Provincial de Huancayo",
            "procedimiento": evaluacion.get("procedimiento", "LICENCIA_EDIFICACION"),
            "resultado_evaluacion": evaluacion.get("estado_evaluacion", "INCOMPLETO"),
            "score_confianza": evaluacion.get("confianza_f1", 0.0),
            "resumen_requisitos": {
                "cumplidos": evaluacion.get("requisitos_detectados", []),
                "faltantes": evaluacion.get("requisitos_faltantes", []),
                "total_exigidos": len(evaluacion.get("requisitos_exigidos", []))
            },
            "normativa_aplicada": "Texto Único de Procedimientos Administrativos (TUPA - MPH)",
            "requiere_intervencion_humana": evaluacion.get("requiere_revision_humana", True)
        }
    