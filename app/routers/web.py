from fastapi import APIRouter, Request, Form
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
import os
import json
from datetime import datetime
from typing import List, Optional

from app.services.knowledge_base import get_symptoms, get_nutrient_details
from app.services.inference_cf import calculate_cf

router = APIRouter()

# Setup templates
templates_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "templates")
templates = Jinja2Templates(directory=templates_dir)

# Logs path
LOGS_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "logs.json")

@router.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@router.get("/consult", response_class=HTMLResponse)
async def consult_form(request: Request):
    symptoms = get_symptoms()
    return templates.TemplateResponse("consult.html", {"request": request, "symptoms": symptoms})

@router.post("/consult", response_class=HTMLResponse)
async def consult_result(
    request: Request,
    name: Optional[str] = Form(None),
    age: Optional[str] = Form(None)
):
    # Parse form data manually to get symptoms and their confidence values
    form_data = await request.form()
    
    selected_symptoms = {}
    
    # Iterate over form fields to find symptoms
    # Expected format: symptoms[G01] = 0.8
    for key, value in form_data.items():
        if key.startswith("symptoms[") and key.endswith("]"):
            # Extract symptom code
            symptom_code = key[9:-1] # Remove 'symptoms[' and ']'
            
            try:
                cf_value = float(value)
                # Only include if confidence > 0
                if cf_value > 0:
                    selected_symptoms[symptom_code] = cf_value
            except ValueError:
                continue
    
    # Run Expert System (CF)
    cf_results = calculate_cf(selected_symptoms)
    
    # Prepare Result Data
    if not cf_results or all(v == 0 for v in cf_results.values()):
        # Handle case where no symptoms selected or no result
        return templates.TemplateResponse("result.html", {
            "request": request,
            "name": name,
            "age": age,
            "cf_results": {},
            "top_nutrient": None,
            "top_cf": 0,
            "symptoms_selected": selected_symptoms
        })

    top_nutrient_code = max(cf_results, key=cf_results.get)
    top_nutrient_data = get_nutrient_details(top_nutrient_code)
    top_cf_value = cf_results[top_nutrient_code]
    
    # Log Consultation
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "name": name,
        "age": age,
        "symptoms": selected_symptoms,
        "cf_results": cf_results,
        "top_diagnosis": top_nutrient_data["name"] if top_nutrient_data else "Unknown"
    }
    
    try:
        # Check if file exists first
        if not os.path.exists(LOGS_PATH):
             with open(LOGS_PATH, "w") as f:
                json.dump([], f)
                
        with open(LOGS_PATH, "r+") as f:
            try:
                logs = json.load(f)
            except json.JSONDecodeError:
                logs = []
            
            logs.append(log_entry)
            f.seek(0)
            f.truncate()
            json.dump(logs, f, indent=2)
    except Exception as e:
        print(f"Error logging: {e}")

    # Create a map of nutrient code to name for display
    from app.services.knowledge_base import get_nutrients
    all_nutrients = get_nutrients()
    nutrient_names = {n['code']: n['name'] for n in all_nutrients}
    
    # Prepare chart data
    chart_labels = [nutrient_names[code] for code in cf_results.keys()]
    chart_data = list(cf_results.values())

    return templates.TemplateResponse("result.html", {
        "request": request,
        "name": name,
        "age": age,
        "cf_results": cf_results,
        "top_nutrient": top_nutrient_data,
        "top_cf": top_cf_value,
        "symptoms_selected": selected_symptoms,
        "nutrient_names": nutrient_names,
        "chart_labels": chart_labels,
        "chart_data": chart_data
    })

@router.get("/about", response_class=HTMLResponse)
async def about(request: Request):
    return templates.TemplateResponse("about.html", {"request": request})
