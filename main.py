# Loading keys
import os
from datetime import datetime
import pandas as pd

from dotenv import load_dotenv
import json

import glob

from serpapi import GoogleSearch
from openai import OpenAI

from tqdm import tqdm


# SETTINGS
SERP_PAGE_LIMIT = 6
TODAY = datetime.today().strftime("%Y-%m-%d")

SERP_FOLDER = "serp_extract"
SERP_FILENAME = f"serp_{TODAY}.csv"

OUTPUT_DIR = "outputs"
OUTPUT_FILENAME = f"output_{TODAY}.xlsx"


# Load environment variables from .env file
load_dotenv()

# Access the API key
serp_key = os.getenv("SERP_KEY")
client = OpenAI(
    # This is the default and can be omitted
    api_key=os.environ.get("OPENAI_API_KEY"),
)

def serp_run():
    data = {
        "title": [],
        "company_name": [],
        "location": [],
        "via": [],
        "description": [],
        "salary": [],
        "linkedin_link": []
    }
    next_page_token = ""
    for _ in range(SERP_PAGE_LIMIT):
        params = {
            "engine": "google_jobs",
            "q": "senior data scientist since yesterday in united states full time",
            "google_domain": "google.com",
            "gl": "us",
            "hl": "en",
            "api_key": serp_key,
            "next_page_token": next_page_token
        }

        search = GoogleSearch(params)
        results = search.get_dict()

        for job in results["jobs_results"]:
            linkedIn_flag = False
            linkedIn_link = None
            for option in job["apply_options"]:
                if option["title"] == "LinkedIn":
                    linkedIn_flag = True
                    linkedIn_link = option["link"]
                    break

            if linkedIn_flag:
                data["title"].append(job["title"])
                data["company_name"].append(job["company_name"])
                data["location"].append(job["location"])
                data["via"].append(job["via"])
                data["linkedin_link"].append(linkedIn_link)

                # Description
                header = " | ".join(f"{key}: {value}" for key, value in job["detected_extensions"].items())
                data["description"].append(header + "\n" + job["description"])

                # Salary
                if "salary" in job["detected_extensions"]:
                    data["salary"].append(job["detected_extensions"]["salary"])
                else:
                    data["salary"].append(None)

            # Set next page token
            next_page_token = results["serpapi_pagination"]["next_page_token"]

    # Save DataFrame
    df = pd.DataFrame(data)
    print(len(df))
    df.to_csv(SERP_FOLDER + "/" + SERP_FILENAME, index=False)

def openai_run():
    df = pd.read_csv(SERP_FOLDER + "/" + SERP_FILENAME)
    with open("resume.txt", "r") as f:
        resume_input = f.read()
    
    # Load prompt base template
    prompt_template = """
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
    14. Visa Sponsorship (H1B sponsorship required, give no sponsorship and US citizen required 0) - Weight: 10

    All ratings must be in the range of **1 to 10**, where 1 is very poor alignment and 10 is perfect alignment.

    ---

    📥 Inputs:
    - Resume: {resume_input}  
    - Job Description: {job_description}  

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
        "visa_sponsorship": {{"rating": X, "weight": 10}},
    }},
    "reasoning": "2-3 lines, at most 150 words, summarizing the overall fit and justification for the final score."
    }}
    ```

    Respond only with a valid JSON object. Do not include any text, Markdown code block, or backticks.
    """

    print(f"[INFO] Running prompt for {len(df)} jobs")
    for i, row in tqdm(df.iterrows(), total=len(df)):
        # Fill in the prompt
        filled_prompt = prompt_template.format(resume_input=resume_input, job_description=row["description"])

        # Call the API
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": filled_prompt}
            ],
            temperature=0.1  # lower temperature for more consistent structure
        )

        # Extract and parse the JSON output
        response_text = response.choices[0].message.content
        try:
            if 'json' in response_text:
                result = json.loads(response_text[8:-4])
            else:
                result = json.loads(response_text)
        except json.JSONDecodeError:
            print("Could not parse JSON. Here's the raw output:")
            print(response_text)
            continue  # skip this row
        # Flatten and add ratings and weights
        total_score = 0
        total_weight = 0

        for criterion, values in result["criteria_ratings"].items():
            rating = values.get("rating", 0)
            weight = values.get("weight", 0)

            # Store rating and weight in DataFrame
            df.at[i, f"{criterion}_rating"] = rating
            df.at[i, f"{criterion}_weight"] = weight

            # Accumulate weighted score
            total_score += rating * weight
            total_weight += weight

        # Add reasoning
        df.at[i, "reasoning"] = result.get("reasoning")

        # Compute and add final weighted average score
        final_score = total_score / total_weight if total_weight else 0
        df.at[i, "final_score"] = round(final_score, 2)

    # Current columns
    cols = list(df.columns)

    cols.remove("linkedin_link")
    cols.append("linkedin_link")
    df = df[cols]

    df['linkedin_link'] = df['linkedin_link'].apply(lambda x: f'=HYPERLINK("{x}", "{x}")')
    df = df.sort_values(by="final_score", ascending=False, na_position="last")
    df.to_excel(OUTPUT_DIR + "/" + OUTPUT_FILENAME, sheet_name="Job_Match_Results", index=False)


if __name__ == "__main__":
    print("[INFO] Running SERP extract...")
    serp_files = glob.glob(SERP_FOLDER + "/*.csv")
    serp_run_flag = False
    for file in serp_files:
        if file.split("_")[-1].split(".")[0] == TODAY:
            serp_run_flag = True
    
    if serp_run_flag:
        print("[INFO] Serp already ran today, skipping..")
    else:
        serp_run()
    print("[INFO] Running OpenAI model...")
    openai_run()
    print("[INFO] Save successful!")
