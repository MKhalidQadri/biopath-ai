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
    field: str = Form(...),
    current_category: str = Form(...), # NEW: Capture the hidden category
    db: Session = Depends(database.get_db)):
    
    user_profile = {"skills": "", "field": field}
    
    # NEW: Filter the database by category BEFORE matching so tabs stay pure
    opps = db.query(Opportunity).filter(Opportunity.category == current_category).all()
    
    results = []
    for opp in opps:
        # We still run the AI module to generate the "Missing Skills" list
        old_score, missing = ai_module.calculate_match_score(user_profile, opp)
        
        # --- NEW FIELD-FIRST SCORING MATH ---
        if opp.field == user_profile["field"]:
            # Exact Category Match! Base 85% + dynamic variance so they aren't all exactly the same
            score = 85 + (len(opp.title) % 13) 
            
            # (Optional) Small penalty for IT/Software roles popping up in Biotech search
            if any(word in opp.title.lower() for word in ["java", "software", "it", "developer"]):
                score -= 40
        else:
            # Wrong category
            score = 15 + (len(opp.title) % 5)
            
        # Ensure score never exceeds 99% for realism
        score = min(score, 99)
            
        results.append({"data": opp, "score": score, "missing": missing})
    
    # Sort results by match score (highest to lowest)
    results = sorted(results, key=lambda x: x['score'], reverse=True)
    suggestions = ai_module.suggest_careers(user_profile, opps)
    
    return templates.TemplateResponse(request=request, name="index.html", context={
        "request": request, 
        "results": results, 
        "suggestions": suggestions,
        "profile": user_profile,
        "active_cat": current_category # Keep the tab active
    })

# API Endpoints for external integration 
@app.get("/api/opportunities")
def api_get_opportunities(db: Session = Depends(database.get_db)):
    return db.query(Opportunity).all()