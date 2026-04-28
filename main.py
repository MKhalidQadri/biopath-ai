from fastapi import FastAPI, Request, Depends, Form
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
import database
import ai_module
from database import Opportunity

app = FastAPI(title="BioPath AI")
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Initialize the database on startup 
@app.on_event("startup")
def startup_event():
    database.init_db()

@app.get("/", response_class=HTMLResponse)
async def index(request: Request, db: Session = Depends(database.get_db)):
    opps = db.query(Opportunity).all()
    # UPDATED: Explicitly label request, name, and context
    return templates.TemplateResponse(request=request, name="index.html", context={"request": request, "opportunities": opps})

@app.get("/category/{cat_type}", response_class=HTMLResponse)
async def get_by_category(request: Request, cat_type: str, db: Session = Depends(database.get_db)):
    opps = db.query(Opportunity).filter(Opportunity.category == cat_type).all()
    # UPDATED: Explicitly label request, name, and context
    return templates.TemplateResponse(request=request, name="index.html", context={"request": request, "opportunities": opps, "active_cat": cat_type})

@app.post("/match", response_class=HTMLResponse)
async def match_profile(
    request: Request, 
    skills: str = Form(...), 
    field: str = Form(...),
    db: Session = Depends(database.get_db)):
    user_profile = {"skills": skills, "field": field}
    opps = db.query(Opportunity).all()
    
    results = []
    for opp in opps:
        score, missing = ai_module.calculate_match_score(user_profile, opp)
        results.append({"data": opp, "score": score, "missing": missing})
    
    # Sort results by match score
    results = sorted(results, key=lambda x: x['score'], reverse=True)
    suggestions = ai_module.suggest_careers(user_profile, opps)
    
    # UPDATED: Explicitly label request, name, and context
    return templates.TemplateResponse(request=request, name="index.html", context={
        "request": request, 
        "results": results, 
        "suggestions": suggestions,
        "profile": user_profile
    })

# API Endpoints for external integration 
@app.get("/api/opportunities")
def api_get_opportunities(db: Session = Depends(database.get_db)):
    return db.query(Opportunity).all()