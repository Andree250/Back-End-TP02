from fastapi import FastAPI, UploadFile, File, HTTPException
from pydantic import BaseModel
from typing import List, Optional

# 1. Importación de Casos de Uso
from src.application.useCases.process_dossier import ProcessDossierUseCase
from src.application.useCases.generate_dictamen import GenerateTupaDictamenUseCase
from src.application.useCases.human_review import HumanReviewUseCase

# 2. Importación de Adaptadores de Infraestructura
from src.infrastructure.adapters.output.tupa_ai_adapter import TUPAIEvaluatorAdapter

# NOTA: Importa aquí los adaptadores de BD y OCR que creó tu equipo en el proyecto
# Descomenta y ajusta los nombres según la carpeta exacta de tu equipo:
# from src.infrastructure.adapters.output.sqlite_repository import SQLiteRepository
# from src.infrastructure.adapters.output.ocr_adapter import RapidOCRAdapter

app = FastAPI(
    title="Sistema de Procesamiento de Expedientes Municipalidad Provincial de Huancayo",
    version="1.0.0"
)

# -------------------------------------------------------------------------
# 3. INSTANCIACIÓN DE COMPONENTES (Resuelve las líneas amarillas)
# -------------------------------------------------------------------------
ai_evaluator = TUPAIEvaluatorAdapter()

# Reemplaza estas dos líneas por las instancias reales de tu repositorio y OCR:
dossier_repository = None  # Ejemplo: SQLiteRepository()
ocr_adapter = None         # Ejemplo: RapidOCRAdapter()

process_dossier_use_case = ProcessDossierUseCase(ocr_adapter, dossier_repository, ai_evaluator)
generate_dictamen_use_case = GenerateTupaDictamenUseCase(dossier_repository)
human_review_use_case = HumanReviewUseCase(dossier_repository)


# -------------------------------------------------------------------------
# 4. SCHEMAS PYDANTIC
# -------------------------------------------------------------------------
class HumanReviewRequest(BaseModel):
    revisor_id: str
    nuevo_estado: str  # "COMPLETO" o "RECHAZADO"
    observaciones: str
    documentos_convalidados: Optional[List[str]] = []


# -------------------------------------------------------------------------
# 5. ENDPOINTS DE LA API (HU01, HU03, HU04)
# -------------------------------------------------------------------------

# --- HU01: Extracción, Anonimización y Evaluación ---
@app.post("/api/expedientes", tags=["HU01 - Evaluación TUPA"])
async def cargar_expediente(archivo: UploadFile = File(...)):
    contents = await archivo.read()
    resultado = process_dossier_use_case.execute(contents, archivo.filename)
    return resultado

# --- HU03: Emisión de Dictamen Técnico Oficial ---
@app.get("/api/expedientes/{dossier_id}/dictamen", tags=["HU03 - Dictamen Oficial"])
def obtener_dictamen_oficial(dossier_id: str):
    resultado = generate_dictamen_use_case.execute(dossier_id)
    if "error" in resultado:
        raise HTTPException(status_code=404, detail=resultado["error"])
    return resultado

# --- HU04: Validación Asistida Human-in-the-Loop ---
@app.post("/api/expedientes/{dossier_id}/revision-humana", tags=["HU04 - Human in the Loop"])
def registrar_revision_humana(dossier_id: str, review_data: HumanReviewRequest):
    resultado = human_review_use_case.execute(
        dossier_id=dossier_id,
        revisor_id=review_data.revisor_id,
        nuevo_estado=review_data.nuevo_estado,
        observaciones=review_data.observaciones,
        documentos_convalidados=review_data.documentos_convalidados
    )
    if "error" in resultado:
        raise HTTPException(status_code=404, detail=resultado["error"])
    return resultado
