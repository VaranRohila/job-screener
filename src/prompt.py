RATING_TEMPLATE = """
You are an expert job-matching assistant. Your task is to evaluate how well a given job description matches a candidate's resume using weighted criteria, reflecting what matters most to the candidate.

    The candidate is targeting **Senior Data Scientist roles**, has **2 years of experience**, and is looking for **individual contributor (IC) roles only**, with a **total compensation of $240,000 or more**. Analyze the match between the resume and job description using the following weighted criteria:

    ---

    🔍 Evaluation Criteria (with Weights):
    1. Role Fit (Responsibilities & Scope) – Weight: 10  
    2. Experience Requirement (Must require at most 2 years experience with a Master's degree) – Weight: 10  
    3. Growth & Learning Opportunities – Weight: 9  
    4. Role Level (Must be IC; not managerial or senior managerial) – Weight: 9  
    5. Team & Manager Quality (if mentioned) – Weight: 8  
    6. Company Stability & Mission Fit – Weight: 8  
    7. Compensation (Target: $240K+, estimate based on role and company if not present) – Weight: 8  
    8. Work-Life Balance & Culture – Weight: 7  
    9. Technical Stack Relevance – Weight: 6  
    10. Location / Remote Flexibility – Weight: 5  
    11. Perks & Benefits – Weight: 3  
    12. Job Description Quality – Weight: 2
    13. Distance from current location, less is better (Jersey City, NJ) - Weight: 7
    14. Visa Sponsorship (give 10 for H1B sponsorship; 0 for no sponsorship and US citizen required) - Weight: 6.

    All ratings must be in the range of **1 to 10**, where 1 is very poor alignment and 10 is perfect alignment.

    ---

    📥 Inputs:
    - Resume: <{resume_input}>  
    - Job Description: <{job_description}>  

    ---

    📤 Output Format:
    Respond **only with a valid JSON object** in the format below:

    ```json
    {{
    "criteria_ratings": {{
        "role_fit": {{"rating": X, "weight": 10}},
        "experience_requirement": {{"rating": X, "weight": 10}},
        "growth_opportunities": {{"rating": X, "weight": 9}},
        "role_level": {{"rating": X, "weight": 9}},
        "team_quality": {{"rating": X, "weight": 8}},
        "company_stability_mission": {{"rating": X, "weight": 8}},
        "compensation": {{"rating": X, "weight": 8}},
        "work_life_balance": {{"rating": X, "weight": 7}},
        "tech_stack": {{"rating": X, "weight": 6}},
        "location_remote": {{"rating": X, "weight": 5}},
        "benefits": {{"rating": X, "weight": 3}},
        "jd_quality": {{"rating": X, "weight": 2}},
        "distance_jc": {{"rating": X, "weight": 7}},
        "visa_sponsorship": {{"rating": X, "weight": 6}},
    }},
    "reasoning": "2-3 lines, at most 150 words, summarizing the overall fit and justification for the final score."
    }}
    ```

    Respond only with a valid JSON object as specified above. Do not include any text, Markdown code block, or backticks.
"""

COVER_LETTER_TEMPLATE = """
You are an expert cover letter writer. Based on the information I provide, generate a concise, compelling, and personalized cover letter tailored to the job description.

Instructions:

1. Use my name and email in the contact section.
2. Use only the information from my resume to highlight relevant skills and experience.
3. Match the tone and keywords of the job description.
4. Keep it to one page, at least 300 words and at most 450 words, and output only the cover letter—no explanations, headers, or commentary.
5. Do not use any placeholders anywhere in the cover letter.
6. Use Dear hiring Committee.
7. Make use of atmost four paragraphs, no more no less, to structure the cover letter.
8. Use only single new line character '\n' after 'Dear hiring Committee', 'Warm regards' and between the three paragraphs.

My Name: <{name_input}>
Email: <{email_input}>
Resume: <{resume_input}>  
Job Description: <{job_description}>

MAKE SURE TO USE ATMOST FOUR PARAGRAPHS.
"""