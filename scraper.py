import requests
import time
from datetime import datetime
import database
from database import SessionLocal, Opportunity

# --- API CONFIGURATION ---
ADZUNA_APP_ID = "74c3c80e"   
ADZUNA_APP_KEY = "faef94592e059bbb018d54c11b747a65" 
COUNTRIES = ["in", "us", "gb"] 

def fetch_broad_sweep(db, search_term, forced_field=None, base_pages=2):
    print(f"\n[ SYSTEM ]: Harvesting data for '{search_term}' (India Prioritized)...")

    for country in COUNTRIES:
        if country == "in":
            actual_pages = base_pages * 6  
        else:
            actual_pages = 1  

        for page in range(1, actual_pages + 1):
            url = f"https://api.adzuna.com/v1/api/jobs/{country}/search/{page}"
            params = {
                "app_id": ADZUNA_APP_ID,
                "app_key": ADZUNA_APP_KEY,
                "results_per_page": 50, 
                "what": search_term,
                "content-type": "application/json"
            }

            try:
                response = requests.get(url, params=params)
                if response.status_code != 200:
                    break 
                
                data = response.json()
                results = data.get("results", [])
                if not results:
                    break 
                    
                live_opportunities = []
                for job in results:
                    title = job.get("title", "Biotech Role")
                    desc = job.get("description", "")
                    title_lower = title.lower()
                    desc_lower = desc.lower()
                    
                    if any(word in title_lower for word in ["phd", "postdoc", "doctoral", "jrf", "srf", "research fellow", "scientist"]):
                        cat = "PhD"
                    elif any(word in title_lower for word in ["msc", "master", "m.sc", "graduate", "project assistant", "project associate", "research assistant", "post graduate"]):
                        cat = "Masters"
                    elif any(word in title_lower for word in ["intern", "internship", "trainee", "student"]):
                        cat = "Internship"
                    elif any(word in title_lower for word in ["workshop", "training", "seminar", "course"]):
                        cat = "Workshop"
                    else:
                        cat = "Job"

                    final_field = forced_field
                    if not final_field:
                        fields_to_check = [
                            "Bioinformatics", "Genetics", "Microbiology", "Clinical Research", 
                            "Synthetic Biology", "Biomedical Engineering", "Biomanufacturing",
                            "Agricultural Biotechnology", "Pharmacogenomics"
                        ]
                        assigned = False
                        for f in fields_to_check:
                            if f.lower() in title_lower or f.lower() in desc_lower:
                                final_field = f
                                assigned = True
                                break
                        if not assigned:
                            final_field = "Biotechnology (General)"

                    company_name = job.get("company", {}).get("display_name", "Institution")
                    loc_name = job.get("location", {}).get("display_name", "Remote")
                    flag = "🇮🇳" if country == "in" else "🇺🇸" if country == "us" else "🇬🇧"
                    full_location = f"{flag} {company_name} | {loc_name}"
                    
                    created_raw = job.get("created", "")
                    try:
                        upload_date = datetime.strptime(created_raw, "%Y-%m-%dT%H:%M:%SZ").strftime("%Y-%m-%d")
                    except:
                        upload_date = datetime.now().strftime("%Y-%m-%d")
                        
                    opp = Opportunity(
                        title=title,
                        category=cat, 
                        field=final_field, 
                        eligibility="See official description.", 
                        skills_required="Review Official Portal", 
                        location=full_location,
                        uploaded_date=upload_date,
                        deadline="Rolling / Check Portal",
                        exams_required="Refer to Official Portal",
                        fellowship_details="Review compensation on official site.",
                        link=job.get("redirect_url", "#"),
                        description=desc[:400] + "..." 
                    )
                    live_opportunities.append(opp)
                    
                db.add_all(live_opportunities)
                db.commit()
                time.sleep(1.5) 
                
            except Exception as e:
                print(f"  -> [API LIMIT] Interrupted. Details: {e}")
                break

def update_database():
    database.init_db()
    db = SessionLocal()
    
    print("Sweeping out old database completely...")
    db.query(Opportunity).delete() 
    db.commit()
    
    core_fields = [
        "Bioinformatics", "Genetics", "Microbiology", "Clinical Research", 
        "Biomedical Engineering", "Synthetic Biology", "Agricultural Biotechnology"
    ]
    for field in core_fields:
        fetch_broad_sweep(db, search_term=field, forced_field=field, base_pages=1)
        
    academic_sweeps = [
        "JRF Biotechnology",
        "SRF Life Sciences",
        "PhD Life Sciences",
        "Biotechnology Internship", 
        "Clinical Trainee",
        "Biotech Workshop"
    ]
    for term in academic_sweeps:
        fetch_broad_sweep(db, search_term=term, forced_field=None, base_pages=3)

    masters_sweeps = [
        "MSc Biotechnology",
        "M.Sc Life Sciences",
        "Project Assistant Biology",
        "Project Associate Biotech",
        "Research Assistant Life Sciences",
        "Post Graduate Biology",
        "Project Assistant",
        "Project Associate",
        "MSc Life Sciences",
        "Master Biotechnology"
    ]
    for term in masters_sweeps:
        fetch_broad_sweep(db, search_term=term, forced_field=None, base_pages=6)
    
    total_records = db.query(Opportunity).count()
    print(f"\n✅ SUCCESS: Database Fully Loaded with {total_records} Records!")
    db.close()

if __name__ == "__main__":
    update_database()