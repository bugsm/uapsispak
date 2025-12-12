"""Web Router Module - Handle HTTP routes untuk aplikasi web"""

import os
import json
import base64
import logging
from datetime import datetime
from typing import Optional, Dict, Any

from fastapi import APIRouter, Request, Form, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from fastapi import Query

from app.services.knowledge_base import (
    get_symptoms, 
    get_nutrient_details, 
    get_nutrients,
    KnowledgeBaseError
)
from app.services.inference_cf import (
    calculate_cf, 
    calculate_cf_with_details,
    InferenceError, 
    get_top_nutrient
)

# Setup logger
logger = logging.getLogger(__name__)

router = APIRouter()

# Setup templates
templates_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "templates")
templates = Jinja2Templates(directory=templates_dir)

# Logs path
LOGS_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 
    "data", 
    "logs.json"
)


def _ensure_logs_file() -> None:
    """
    Memastikan file logs.json ada dan valid.
    Membuat file baru jika tidak ada, atau memperbaiki jika corrupt.
    """
    try:
        if not os.path.exists(LOGS_PATH):
            # Create directory if not exists
            os.makedirs(os.path.dirname(LOGS_PATH), exist_ok=True)
            # Create empty logs file
            with open(LOGS_PATH, "w", encoding="utf-8") as f:
                json.dump([], f)
            logger.info(f"Created logs file: {LOGS_PATH}")
    except Exception as e:
        logger.error(f"Error ensuring logs file exists: {str(e)}", exc_info=True)


def _save_consultation_log(log_entry: Dict[str, Any]) -> bool:
    """Simpan log konsultasi ke file JSON"""
    try:
        _ensure_logs_file()
        
        # Read existing logs
        try:
            with open(LOGS_PATH, "r", encoding="utf-8") as f:
                logs = json.load(f)
                if not isinstance(logs, list):
                    logger.warning("Logs file is not a list, resetting")
                    logs = []
        except json.JSONDecodeError:
            logger.warning("Logs file is corrupted, resetting")
            logs = []
        except FileNotFoundError:
            logger.warning("Logs file not found, creating new")
            logs = []
        
        # Append new log
        logs.append(log_entry)
        
        # Write back
        with open(LOGS_PATH, "w", encoding="utf-8") as f:
            json.dump(logs, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Consultation log saved successfully")
        return True
        
    except Exception as e:
        logger.error(f"Error saving consultation log: {str(e)}", exc_info=True)
        return False


def _parse_symptom_form_data(form_data: Any) -> Dict[str, float]:
    """Parse form data untuk extract gejala yang dipilih"""
    selected_symptoms = {}
    
    try:
        # Iterate over form fields to find symptoms
        # Expected format: symptoms[G01] = 0.8
        for key, value in form_data.items():
            if key.startswith("symptoms[") and key.endswith("]"):
                # Extract symptom code
                symptom_code = key[9:-1]  # Remove 'symptoms[' and ']'
                
                try:
                    cf_value = float(value)
                    # Validasi range
                    if 0.0 < cf_value <= 1.0:  # Only include if confidence > 0
                        selected_symptoms[symptom_code] = cf_value
                    elif cf_value < 0.0 or cf_value > 1.0:
                        logger.warning(
                            f"CF value out of range for {symptom_code}: {cf_value}, "
                            f"skipping"
                        )
                except (ValueError, TypeError):
                    logger.warning(
                        f"Invalid CF value for {symptom_code}: {value}, skipping"
                    )
                    continue
        
        logger.info(f"Parsed {len(selected_symptoms)} symptoms from form data")
        return selected_symptoms
        
    except Exception as e:
        logger.error(f"Error parsing symptom form data: {str(e)}", exc_info=True)
        return {}


@router.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    """Homepage route"""
    try:
        logger.info(f"Homepage accessed from {request.client.host if request.client else 'unknown'}")
        return templates.TemplateResponse("index.html", {"request": request})
    except Exception as e:
        logger.error(f"Error rendering homepage: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/consult", response_class=HTMLResponse)
async def consult_form(request: Request):
    """Form konsultasi route"""
    try:
        logger.info(f"Consult form accessed from {request.client.host if request.client else 'unknown'}")
        
        # Load symptoms dari knowledge base
        symptoms = get_symptoms()
        
        if not symptoms:
            logger.error("No symptoms found in knowledge base")
            raise HTTPException(
                status_code=500, 
                detail="Knowledge base tidak tersedia. Silakan hubungi administrator."
            )
        
        logger.debug(f"Loaded {len(symptoms)} symptoms for consult form")
        
        return templates.TemplateResponse(
            "consult.html", 
            {"request": request, "symptoms": symptoms}
        )
        
    except KnowledgeBaseError as e:
        logger.error(f"Knowledge base error in consult form: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Error loading knowledge base. Silakan coba lagi nanti."
        )
    except Exception as e:
        logger.error(f"Unexpected error in consult form: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/consult", response_class=HTMLResponse)
async def consult_result(
    request: Request,
    name: Optional[str] = Form(None),
    age: Optional[str] = Form(None)
):
    """Process konsultasi dan tampilkan hasil diagnosa"""
    try:
        client_ip = request.client.host if request.client else "unknown"
        logger.info(f"Consultation request from {client_ip}")
        
        # Parse form data
        form_data = await request.form()
        
        # Extract symptoms dari form
        selected_symptoms = _parse_symptom_form_data(form_data)
        
        # Validasi minimal 1 gejala
        if not selected_symptoms:
            logger.warning("No symptoms selected in consultation")
            # Get nutrient names untuk display
            try:
                all_nutrients = get_nutrients()
                nutrient_names = {n['code']: n['name'] for n in all_nutrients}
            except Exception as e:
                logger.error(f"Error getting nutrient names: {str(e)}")
                nutrient_names = {}
            
            empty_details_json = json.dumps({}, ensure_ascii=False)
            empty_details_encoded = base64.b64encode(empty_details_json.encode('utf-8')).decode('utf-8')
            
            return templates.TemplateResponse("result.html", {
                "request": request,
                "name": name or "",
                "age": age or "",
                "cf_results": {},
                "top_nutrient": None,
                "top_cf": 0.0,
                "symptoms_selected": {},
                "nutrient_names": nutrient_names,
                "chart_labels": [],
                "chart_data": [],
                "calculation_details_encoded": empty_details_encoded,
                "error_message": "Silakan pilih minimal 1 gejala untuk melakukan diagnosa."
            })
        
        logger.info(
            f"Processing consultation with {len(selected_symptoms)} symptoms: "
            f"{list(selected_symptoms.keys())}"
        )
        
        # Run Expert System (CF Calculation) dengan detail
        try:
            cf_results, calculation_details = calculate_cf_with_details(
                selected_symptoms, 
                validate_input=True
            )
        except InferenceError as e:
            logger.error(f"Inference error: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail="Error saat menghitung diagnosa. Silakan coba lagi."
            )
        
        # Prepare result data
        if not cf_results or all(v == 0.0 for v in cf_results.values()):
            logger.info("No valid diagnosis found (all CF = 0)")
            # Get nutrient names untuk display
            try:
                all_nutrients = get_nutrients()
                nutrient_names = {n['code']: n['name'] for n in all_nutrients}
            except Exception as e:
                logger.error(f"Error getting nutrient names: {str(e)}")
                nutrient_names = {}
            
            empty_details_json = json.dumps(calculation_details, ensure_ascii=False)
            empty_details_encoded = base64.b64encode(empty_details_json.encode('utf-8')).decode('utf-8')
            
            return templates.TemplateResponse("result.html", {
                "request": request,
                "name": name or "",
                "age": age or "",
                "cf_results": {},
                "top_nutrient": None,
                "top_cf": 0.0,
                "symptoms_selected": selected_symptoms,
                "nutrient_names": nutrient_names,
                "chart_labels": [],
                "chart_data": [],
                "calculation_details_encoded": empty_details_encoded,
                "info_message": "Tidak ada diagnosa yang signifikan. Gejala yang dipilih mungkin tidak cukup spesifik."
            })
        
        # Get top nutrient
        top_result = get_top_nutrient(cf_results)
        
        if not top_result:
            logger.warning("No top nutrient found despite non-zero CF results")
            top_nutrient_code = None
            top_nutrient_data = None
            top_cf_value = 0.0
        else:
            top_nutrient_code, top_cf_value = top_result
            top_nutrient_data = get_nutrient_details(top_nutrient_code)
            
            if not top_nutrient_data:
                logger.warning(f"Nutrient details not found for {top_nutrient_code}")
        
        # Get nutrient names untuk display
        try:
            all_nutrients = get_nutrients()
            nutrient_names = {n['code']: n['name'] for n in all_nutrients}
        except Exception as e:
            logger.error(f"Error getting nutrient names: {str(e)}")
            nutrient_names = {}
        
        # Prepare chart data
        chart_labels = [nutrient_names.get(code, code) for code in cf_results.keys()]
        chart_data = list(cf_results.values())
        
        # Log consultation
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "client_ip": client_ip,
            "name": name or None,
            "age": age or None,
            "symptoms": selected_symptoms,
            "symptom_count": len(selected_symptoms),
            "cf_results": cf_results,
            "top_diagnosis": top_nutrient_data["name"] if top_nutrient_data else "Unknown",
            "top_diagnosis_code": top_nutrient_code or "None",
            "top_cf": top_cf_value
        }
        
        _save_consultation_log(log_entry)
        
        logger.info(
            f"Consultation completed. Top diagnosis: {top_nutrient_data['name'] if top_nutrient_data else 'None'} "
            f"(CF: {top_cf_value:.4f})"
        )
        
        calculation_details_json = json.dumps(calculation_details, ensure_ascii=False)
        calculation_details_encoded = base64.b64encode(calculation_details_json.encode('utf-8')).decode('utf-8')
        
        # Render result template
        return templates.TemplateResponse("result.html", {
            "request": request,
            "name": name or "",
            "age": age or "",
            "cf_results": cf_results,
            "top_nutrient": top_nutrient_data,
            "top_cf": top_cf_value,
            "symptoms_selected": selected_symptoms,
            "nutrient_names": nutrient_names,
            "chart_labels": chart_labels,
            "chart_data": chart_data,
            "calculation_details_encoded": calculation_details_encoded
        })
        
    except HTTPException:
        raise
    except KnowledgeBaseError as e:
        logger.error(f"Knowledge base error in consultation: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Error mengakses knowledge base. Silakan coba lagi nanti."
        )
    except Exception as e:
        logger.error(f"Unexpected error in consultation: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Terjadi error saat memproses konsultasi. Silakan coba lagi."
        )


@router.get("/calculation-details", response_class=HTMLResponse)
async def calculation_details_page(
    request: Request,
    data: Optional[str] = Query(None, description="Encoded calculation details"),
    back: Optional[str] = Query(None, description="Back URL parameter")
):
    """Halaman detail perhitungan CF secara manual"""
    try:
        if not data:
            raise HTTPException(
                status_code=400,
                detail="Data perhitungan tidak ditemukan. Silakan lakukan konsultasi terlebih dahulu."
            )
        
        # Determine back URL - default menggunakan history.back() untuk kembali ke halaman sebelumnya
        back_url = "javascript:history.back()"
        
        try:
            calculation_details_json = base64.b64decode(data.encode('utf-8')).decode('utf-8')
            calculation_details = json.loads(calculation_details_json)
        except Exception as e:
            logger.error(f"Error decoding calculation details: {str(e)}")
            raise HTTPException(
                status_code=400,
                detail="Data perhitungan tidak valid."
            )
        
        # Get nutrient names untuk display
        try:
            all_nutrients = get_nutrients()
            nutrient_names = {n['code']: n['name'] for n in all_nutrients}
        except Exception as e:
            logger.error(f"Error getting nutrient names: {str(e)}")
            nutrient_names = {}
        
        logger.info("Calculation details page accessed")
        
        return templates.TemplateResponse("calculation_details.html", {
            "request": request,
            "calculation_details": calculation_details,
            "nutrient_names": nutrient_names,
            "back_url": back_url
        })
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error rendering calculation details page: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/about", response_class=HTMLResponse)
async def about(request: Request):
    """About page route"""
    try:
        logger.info(f"About page accessed from {request.client.host if request.client else 'unknown'}")
        return templates.TemplateResponse("about.html", {"request": request})
    except Exception as e:
        logger.error(f"Error rendering about page: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")
