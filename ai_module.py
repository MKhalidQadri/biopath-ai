import re

def calculate_match_score(user_profile, opportunity):
    """
    Rule-based matching logic.
    Returns a score and a list of missing skills (skill gap).
    """
    # Tokenize skills
    user_skills = set(skill.strip().lower() for skill in user_profile.get('skills', '').split(','))
    required_skills = set(skill.strip().lower() for skill in opportunity.skills_required.split(','))
    
    if not required_skills:
        return 0,

    # Calculate matches
    matches = user_skills.intersection(required_skills)
    missing = required_skills - user_skills
    
    # Weighting factors
    score = (len(matches) / len(required_skills)) * 100
    
    # Field alignment bonus 
    if user_profile.get('field', '').lower() == opportunity.field.lower():
        score += 15
        
    return min(100, round(score, 2)), list(missing)

def suggest_careers(user_profile, all_opportunities):
    """
    Generates suggestions based on identified skill gaps.
    """
    suggestions = []
    for opp in all_opportunities:
        score, missing = calculate_match_score(user_profile, opp)
        if 40 < score < 90: # Suggest roles where the student is almost qualified
            suggestions.append({
                "role": opp.title,
                "missing_skills": missing[:3],
                "potential_score": score
            })
    return sorted(suggestions, key=lambda x: x['potential_score'], reverse=True)[:3]