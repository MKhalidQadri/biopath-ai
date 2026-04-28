import requests
import database
from database import SessionLocal, Opportunity

# --- API CONFIGURATION ---
ADZUNA_APP_ID = "74c3c80e"   
ADZUNA_APP_KEY = "faef94592e059bbb018d54c11b747a65" 
COUNTRY = "in"  # 'in' for India. Change to 'us', 'gb', 'au' etc., for other locations.

def seed_academic_programs(db):
    """Keeps a few static academic programs since the API only fetches Jobs."""
    if db.query(Opportunity).filter(Opportunity.category.in_(["Masters", "PhD"])).first():
        return # Academic programs already exist

    academic_opps = [
        Opportunity(
            title="PhD in Molecular Biotechnology",
            category="PhD", field="Molecular Biology", eligibility="Bachelor's in Biology/Chemistry",
            skills_required="PCR, CRISPR, Western Blotting", location="Socorro, NM", deadline="2025-11-15",
            link="https://www.nmt.edu/gradstudies/programs.php", description="Doctoral research focused on biophysical technology."
        ),
        Opportunity(
            title="Master of Liberal Arts in Biotechnology",
            category="Masters", field="General Biotech", eligibility="Bachelor's degree",
            skills_required="Bioinformatics, Ethics, Regulatory Affairs", location="Harvard University", deadline="2025-10-30",
            link="https://extension.harvard.edu/academics/programs/biotechnology-graduate-program/", description="Stackable graduate certificates in management and bioinformatics."
        )
    ]
    db.add_all(academic_opps)
    db.commit()

def fetch_live_jobs(db, search_term="bioinformatics"):
    """Fetches real-time job listings from the Adzuna API using Pagination."""
    print(f"Fetching ALL live jobs for '{search_term}'...")
    
    # Clear out old jobs so the database stays fresh every time you run this
    db.query(Opportunity).filter(Opportunity.category == "Job").delete()
    db.commit()

    page = 1
    max_pages = 5 # SAFETY CAP: 5 pages * 50 jobs = 250 jobs. Increase this if you want more!
    total_jobs_added = 0

    while page <= max_pages:
        print(f"Fetching page {page}...")
        
        # Notice the {page} variable at the end of the URL!
        url = f"https://api.adzuna.com/v1/api/jobs/{COUNTRY}/search/{page}"
        params = {
            "app_id": ADZUNA_APP_ID,
            "app_key": ADZUNA_APP_KEY,
            "results_per_page": 50, # The absolute maximum Adzuna allows per request
            "what": search_term,
            "content-type": "application/json"
        }

        try:
            response = requests.get(url, params=params)
            response.raise_for_status() 
            data = response.json()
            
            results = data.get("results", [])
            
            # If the API returns an empty list, we've reached the very end of the jobs
            if not results:
                print("No more jobs found. Ending search.")
                break
                
            live_opportunities = []
            for job in results:
                opp = Opportunity(
                    title=job.get("title", "Biotech Role"),
                    category="Job",
                    field="Bioinformatics", 
                    eligibility="See description", 
                    skills_required="Python, Machine Learning, Data Analysis", # Default assumed skills
                    location=job.get("location", {}).get("display_name", "Remote"),
                    deadline="Rolling",
                    link=job.get("redirect_url", "#"),
                    description=job.get("description", "")[:400] + "..." 
                )
                live_opportunities.append(opp)
                
            db.add_all(live_opportunities)
            db.commit()
            
            total_jobs_added += len(live_opportunities)
            
            # If a page returns LESS than 50 jobs, we know it's the final page.
            if len(results) < 50:
                print("Reached the final page of results.")
                break
                
            page += 1 # Increase the page number and loop again!
            
        except Exception as e:
            print(f"\n[ERROR] Failed to fetch live jobs on page {page}.")
            print(f"Details: {e}")
            break # Stop looping if we hit an API error

    print(f"\nSuccessfully added a total of {total_jobs_added} live jobs to the database!")

def update_database():
    database.init_db()
    db = SessionLocal()
    
    seed_academic_programs(db)
    fetch_live_jobs(db, search_term="bioinformatics") # You can change this keyword!
    
    db.close()

if __name__ == "__main__":
    update_database()