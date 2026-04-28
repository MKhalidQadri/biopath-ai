import requests
import time
import random
from datetime import datetime, timedelta
import database
from database import SessionLocal, Opportunity

# --- API CONFIGURATION ---
ADZUNA_APP_ID = "74c3c80e"   
ADZUNA_APP_KEY = "faef94592e059bbb018d54c11b747a65" 
COUNTRY = "in"  

def generate_massive_academic_database(db):
    """Generates 300+ realistic University Programs across all your fields."""
    print("Generating massive academic database...")
    
    universities = [
        ("Harvard University", "Cambridge, MA, USA"),
        ("Oxford University", "Oxford, UK"),
        ("MIT", "Cambridge, MA, USA"),
        ("Stanford University", "Stanford, CA, USA"),
        ("Johns Hopkins University", "Baltimore, MD, USA"),
        ("ETH Zurich", "Zurich, Switzerland"),
        ("University of Toronto", "Toronto, Canada"),
        ("National University of Singapore", "Singapore"),
        ("IISc Bangalore", "Bangalore, India"),
        ("IIT Delhi", "New Delhi, India"),
        ("IIT Bombay", "Mumbai, India"),
        ("AIIMS", "New Delhi, India"),
        ("Tata Institute of Fundamental Research", "Mumbai, India"),
        ("Central University of Kashmir", "Ganderbal, J&K"),
        ("Pune University", "Pune, India"),
        ("Jawaharlal Nehru University", "New Delhi, India"),
        ("University of Melbourne", "Melbourne, Australia"),
        ("Imperial College London", "London, UK"),
        ("University of California, Berkeley", "Berkeley, CA, USA"),
        ("Brainware University", "Barasat, India")
    ]

    fields = [
        "Agricultural Biotechnology", "Biochemical Engineering", "Bioinformatics", 
        "Biomanufacturing", "Biomedical Engineering", "Biophysics", 
        "Clinical Research", "Computational Biology", "Environmental Biotechnology", 
        "Genetics", "Immunology", "Industrial Biotechnology", "Marine Biotechnology", 
        "Microbiology", "Molecular Biology", "Neurobiology", "Pharmacogenomics", 
        "Plant Sciences", "Stem Cell Research", "Synthetic Biology"
    ]

    buzzwords = ["Advanced", "Applied", "Computational", "Translational", "Quantitative", "Integrative"]
    skills_bank = ["Python", "R", "CRISPR", "Next-Gen Sequencing", "Machine Learning", "Data Analysis", "PCR", "Western Blot", "Cell Culture", "Mass Spectrometry", "Clinical Trials", "Regulatory Affairs"]

    academic_opps = []

    for field in fields:
        # Generate 8 to 12 Masters programs per field
        for _ in range(random.randint(8, 12)):
            uni_name, loc = random.choice(universities)
            days_to_add = random.randint(30, 300)
            deadline_date = (datetime.now() + timedelta(days=days_to_add)).strftime('%Y-%m-%d')
            
            opp = Opportunity(
                title=f"MSc in {random.choice(buzzwords)} {field}",
                category="Masters",
                field=field,
                eligibility="Bachelor's degree in related Life Sciences field",
                skills_required=", ".join(random.sample(skills_bank, 3)),
                location=f"{uni_name} | {loc}",
                deadline=deadline_date,
                link="#",
                description=f"An intensive Master's program at {uni_name} focusing on the latest advancements and laboratory techniques in {field}."
            )
            academic_opps.append(opp)

        # Generate 8 to 12 PhD programs per field
        for _ in range(random.randint(8, 12)):
            uni_name, loc = random.choice(universities)
            days_to_add = random.randint(60, 365)
            deadline_date = (datetime.now() + timedelta(days=days_to_add)).strftime('%Y-%m-%d')
            
            opp = Opportunity(
                title=f"PhD Fellowship in {field}",
                category="PhD",
                field=field,
                eligibility="Master's degree with strong research background",
                skills_required=", ".join(random.sample(skills_bank, 4)),
                location=f"{uni_name} | {loc}",
                deadline=deadline_date,
                link="#",
                description=f"Fully funded doctoral research position at {uni_name} exploring novel paradigms in {field}. Candidates will be expected to publish in high-impact journals."
            )
            academic_opps.append(opp)

    db.add_all(academic_opps)
    db.commit()
    print(f"  -> Successfully generated {len(academic_opps)} Academic Programs!")

def fetch_live_jobs(db, search_term, db_field_name):
    """Fetches real corporate jobs from Adzuna."""
    print(f"Fetching corporate jobs for: {db_field_name}...")
    
    url = f"https://api.adzuna.com/v1/api/jobs/{COUNTRY}/search/1"
    params = {
        "app_id": ADZUNA_APP_ID,
        "app_key": ADZUNA_APP_KEY,
        "results_per_page": 20, # Reduced to 20 so API doesn't time out with the massive new list
        "what": search_term,
        "content-type": "application/json"
    }

    try:
        response = requests.get(url, params=params)
        response.raise_for_status() 
        data = response.json()
        
        results = data.get("results", [])
        if not results:
            print(f"  -> No data found for {db_field_name} today.")
            return
            
        live_opportunities = []
        for job in results:
            title = job.get("title", "Biotech Role")
            title_lower = title.lower()
            
            # Smart Sorter - just in case Adzuna catches a rare fellowship
            if any(word in title_lower for word in ["phd", "postdoc", "doctoral", "post doctoral"]):
                dynamic_category = "PhD"
            elif any(word in title_lower for word in ["msc", "master", "m.sc", "mtech", "m.tech"]):
                dynamic_category = "Masters"
            else:
                dynamic_category = "Job"
                
            opp = Opportunity(
                title=title,
                category=dynamic_category, 
                field=db_field_name, 
                eligibility="See description", 
                skills_required="Degree in Biotech, Lab Experience", 
                location=job.get("location", {}).get("display_name", "Remote"),
                deadline="Rolling",
                link=job.get("redirect_url", "#"),
                description=job.get("description", "")[:400] + "..." 
            )
            live_opportunities.append(opp)
            
        db.add_all(live_opportunities)
        db.commit()
        print(f"  -> Added {len(live_opportunities)} jobs!")
        
    except Exception as e:
        print(f"  -> [ERROR] Failed to fetch. Details: {e}")

def update_database():
    database.init_db()
    db = SessionLocal()
    
    print("Sweeping out old database completely...")
    db.query(Opportunity).delete() 
    db.commit()
    
    # 1. Generate our massive 300+ university program database FIRST
    generate_massive_academic_database(db)
    
    # 2. Map exact HTML Dropdown Values to API Search Terms
    categories_to_fetch = [
        ("Agricultural Biotechnology", "Agricultural Biotechnology"),
        ("Biochemical Engineering", "Biochemical Engineer"),
        ("Bioinformatics", "Bioinformatics"),
        ("Biomanufacturing", "Biomanufacturing"),
        ("Biomedical Engineering", "Biomedical Engineer"),
        ("Biophysics", "Biophysics"),
        ("Clinical Research", "Clinical Research"),
        ("Computational Biology", "Computational Biology"),
        ("Environmental Biotechnology", "Environmental Biotechnology"),
        ("Genetics", "Genetics"),
        ("Immunology", "Immunology"),
        ("Industrial Biotechnology", "Industrial Biotechnology"),
        ("Marine Biotechnology", "Marine Biology"),
        ("Microbiology", "Microbiology"),
        ("Molecular Biology", "Molecular Biology"),
        ("Neurobiology", "Neurobiology"),
        ("Pharmacogenomics", "Pharmacogenomics"),
        ("Plant Sciences", "Plant Sciences"),
        ("Stem Cell Research", "Stem Cell"),
        ("Synthetic Biology", "Synthetic Biology")
    ]
    
    # 3. Pull real corporate jobs from the internet
    print("\n--- Fetching Live Corporate Jobs ---")
    for html_value, api_search_term in categories_to_fetch:
        fetch_live_jobs(db, search_term=api_search_term, db_field_name=html_value)
        time.sleep(1) 
    
    print("\n✅ Database Fully Loaded with Jobs, Masters, and PhDs!")
    db.close()

if __name__ == "__main__":
    update_database()