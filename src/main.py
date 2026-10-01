from fastapi import FastAPI, UploadFile, File, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import fitz  # PyMuPDF para lectura e inspección real de PDFs
import re

app = FastAPI(
    title="Sistema de Procesamiento Definitivo - MPH",
    version="1.0.0"
)

# -------------------------------------------------------------------------
# REPOSITORIO DE DATOS EN MEMORIA
# -------------------------------------------------------------------------
db_expedientes = {}

# -------------------------------------------------------------------------
# MOTOR DE EVALUACIÓN DINÁMICA DE REQUISITOS TUPA
# -------------------------------------------------------------------------
class TUPAEvaluatorEngine:
    @staticmethod
    def extract_text(pdf_bytes: bytes) -> str:
        """Extrae el texto real de todas las páginas del PDF."""
        try:
            doc = fitz.open(stream=pdf_bytes, filetype="pdf")
            texto = ""
            for page in doc:
                texto += page.get_text("text") + " "
            return texto.strip()
        except Exception:
            return ""

    def process_document(self, pdf_bytes: bytes, filename: str) -> dict:
        texto = self.extract_text(pdf_bytes)
        texto_upper = texto.upper()

        requisitos_exigidos = ["FUT", "DNI", "PLANO", "MEMORIA_DESCRIPTIVA"]
        requisitos_detectados = []

        # 1. Detección de FUT
        if any(kw in texto_upper for kw in ["FUT", "FORMULARIO UNICO", "FORMULARIO ÚNICO", "PETITORIO"]):
            requisitos_detectados.append("FUT")

        # 2. Detección de DNI (por palabra clave o patrón de 8 dígitos)
        if any(kw in texto_upper for kw in ["DNI", "DOCUMENTO NACIONAL", "PASAPORTE"]) or re.search(r"\b\d{8}\b", texto):
            requisitos_detectados.append("DNI")

        # 3. Detección de Plano
        if any(kw in texto_upper for kw in ["PLANO", "UBICACION", "UBICACIÓN", "ARQUITECTURA", "LOCALIZACION", "ESCALA"]):
            requisitos_detectados.append("PLANO")

        # 4. Detección de Memoria Descriptiva
        if any(kw in texto_upper for kw in ["MEMORIA DESCRIPTIVA", "MEMORIA_DESCRIPTIVA", "ESPECIFICACIONES"]):
            requisitos_detectados.append("MEMORIA_DESCRIPTIVA")

        requisitos_faltantes = [req for req in requisitos_exigidos if req not in requisitos_detectados]
        total_detectados = len(requisitos_detectados)

        # Determinar el estado dinámico (3 Escenarios)
        if total_detectados == 4:
            estado_eval = "COMPLETO"
            estado_general = "APROBADO_AUTOMATICO"
            requiere_revision = False
            confianza = 0.98
        elif total_detectados > 0:
            estado_eval = "PARCIALMENTE_INCOMPLETO"
            estado_general = "PENDIENTE_REVISION_HUMANA"
            requiere_revision = True
            confianza = round(total_detectados / 4.0, 2)
        else:
            estado_eval = "TOTALMENTE_INCOMPLETO"
            estado_general = "OBSERVADO_SIN_DOCUMENTOS"
            requiere_revision = True
            confianza = 0.0

        expediente_id = f"EXP-2026-{abs(hash(filename + str(len(pdf_bytes)))) % 10000:04d}"

        resultado = {
            "id": expediente_id,
            "nombre_archivo": filename,
            "estado": estado_general,
            "evaluacion_tupa": {
                "procedimiento": "LICENCIA_EDIFICACION_MPH",
                "estado_evaluacion": estado_eval,
                "requisitos_exigidos": requisitos_exigidos,
                "requisitos_detectados": requisitos_detectados,
                "requisitos_faltantes": requisitos_faltantes,
                "confianza_f1": confianza,
                "requiere_revision_humana": requiere_revision
            },
            "muestra_texto_extraido": texto[:200] + "..." if texto else "No se pudo extraer texto (PDF escaneado o en blanco)."
        }

        # Guardar en memoria para consultas en HU03 y HU04
        db_expedientes[expediente_id] = resultado
        return resultado

engine = TUPAEvaluatorEngine()

# -------------------------------------------------------------------------
# SCHEMAS DE ENTRADA
# -------------------------------------------------------------------------
class HumanReviewRequest(BaseModel):
    revisor_id: str
    nuevo_estado: str  # "APROBADO" o "RECHAZADO"
    observaciones: str
    documentos_convalidados: Optional[List[str]] = []

# -------------------------------------------------------------------------
# ENDPOINTS DEFINITIVOS
# -------------------------------------------------------------------------
@app.post("/api/expedientes", tags=["HU01 - Evaluación TUPA Real"])
async def cargar_expediente(archivo: UploadFile = File(...)):
    if not archivo.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Solo se procesan archivos en formato PDF.")
    
    pdf_bytes = await archivo.read()
    return engine.process_document(pdf_bytes, archivo.filename)

@app.get("/api/expedientes/{dossier_id}/dictamen", tags=["HU03 - Dictamen Oficial"])
def obtener_dictamen_oficial(dossier_id: str):
    if dossier_id not in db_expedientes:
        raise HTTPException(status_code=404, detail=f"El expediente {dossier_id} no existe.")
    
    expediente = db_expedientes[dossier_id]
    evaluacion = expediente["evaluacion_tupa"]
    
    return {
        "dossier_id": dossier_id,
        "dictamen_oficial": "APROBADO" if evaluacion["estado_evaluacion"] == "COMPLETO" else "OBSERVADO",
        "requisitos_faltantes": evaluacion["requisitos_faltantes"],
        "requiere_subsanacion": evaluacion["requiere_revision_humana"],
        "detalle_expediente": expediente
    }

@app.post("/api/expedientes/{dossier_id}/revision-humana", tags=["HU04 - Human in the Loop"])
def registrar_revision_humana(dossier_id: str, review_data: HumanReviewRequest):
    if dossier_id not in db_expedientes:
        raise HTTPException(status_code=404, detail=f"El expediente {dossier_id} no existe.")
    
    expediente = db_expedientes[dossier_id]
    expediente["estado"] = f"REVISADO_POR_HUMANO_{review_data.nuevo_estado}"
    expediente["evaluacion_tupa"]["requiere_revision_humana"] = False
    
    if review_data.nuevo_estado.upper() == "APROBADO":
        expediente["evaluacion_tupa"]["estado_evaluacion"] = "COMPLETO_CONVALIDADO"
        expediente["evaluacion_tupa"]["requisitos_faltantes"] = []

    expediente["revision_humana"] = {
        "revisor_id": review_data.revisor_id,
        "observaciones": review_data.observaciones,
        "documentos_convalidados": review_data.documentos_convalidados
    }
    
    return {
        "mensaje": "Revisión humana guardada correctamente.",
        "expediente": expediente
    }
