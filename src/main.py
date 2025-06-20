# Loading keys
import os
from datetime import datetime
import pandas as pd

from dotenv import load_dotenv
import json
import argparse

import glob

from serpapi import GoogleSearch
from openai import OpenAI
from docx import Document

from tqdm import tqdm

from src.prompt import RATING_TEMPLATE, COVER_LETTER_TEMPLATE

# SETTINGS
SERP_PAGE_LIMIT = 6
TODAY = datetime.today().strftime("%Y-%m-%d")

SERP_FOLDER = "serp_extract"
SERP_FILENAME = f"serp_{TODAY}.csv"

OUTPUT_DIR = "outputs"
OUTPUT_FILENAME = f"output_{TODAY}.xlsx"

COVER_LETTER_DIR = "cover_letters"
COVER_LETTER_TODAY = COVER_LETTER_DIR + f'/{TODAY}'

os.makedirs(SERP_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

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
            if 'serpapi_pagination' in results:
                next_page_token = results["serpapi_pagination"]["next_page_token"]
            else:
                break

        # Development break
        if args.dev: break

    # Save DataFrame
    df = pd.DataFrame(data)
    df.to_csv(SERP_FOLDER + "/" + SERP_FILENAME, index=False)

def openai_rating_run():
    df = pd.read_csv(SERP_FOLDER + "/" + SERP_FILENAME)
    with open("resume.txt", "r") as f:
        resume_input = f.read()

    print(f"[INFO] Running rating prompt for {len(df)} jobs")
    for i, row in tqdm(df.iterrows(), total=len(df)):
        # Fill in the prompt
        filled_prompt = RATING_TEMPLATE.format(resume_input=resume_input, job_description=row["description"])

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

        # Development break
        if args.dev: break

    # Current columns
    cols = list(df.columns)

    cols.remove("linkedin_link")
    cols.append("linkedin_link")
    df = df[cols]

    df['linkedin_link'] = df['linkedin_link'].apply(lambda x: f'=HYPERLINK("{x}", "{x}")')
    df = df.sort_values(by="final_score", ascending=False, na_position="last")
    df.to_excel(OUTPUT_DIR + "/" + OUTPUT_FILENAME, sheet_name="Job_Match_Results", index=False)

def openai_cover_letter_run():
    df = pd.read_excel(OUTPUT_DIR + "/" + OUTPUT_FILENAME, sheet_name="Job_Match_Results")
    with open("resume.txt", "r") as f:
        resume_input = f.read()
    
    # Filter df
    if not args.dev:
        df = df[
            (df['final_score'] > 6) &
            (df['visa_sponsorship_rating'] > 0)
        ]

    print(f"[INFO] Running cover letter prompt for {len(df)} jobs")
    print(f"[INFO] Making dirs for cover letters")
    os.makedirs(COVER_LETTER_DIR, exist_ok=True)
    os.makedirs(COVER_LETTER_TODAY, exist_ok=True)
    for i, row in tqdm(df.iterrows(), total=len(df)):
        # Fill in the prompt
        filled_prompt = COVER_LETTER_TEMPLATE.format(
            name_input=os.environ.get("NAME"),
            email_input=os.environ.get("EMAIL"),
            resume_input=resume_input, 
            job_description=row["description"]
        )

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
        # Create a new Word document
        doc = Document()

        # Add the cover letter text (you can split into paragraphs for formatting)
        for paragraph in response_text.split('\n\n'):
            doc.add_paragraph(paragraph)
        
        # Save the document
        name = os.environ.get('NAME')
        name = ''.join(name.split(' '))
        title = ''.join(row['title'].split(' '))
        company = ''.join(row['company_name'].split(' '))
        doc.save(COVER_LETTER_TODAY + '/' + f"{name}_CoverLetter-{title}_{company}.docx")

        # Development break
        if args.dev: break


if __name__ == "__main__":
    # Parser setup
    parser = argparse.ArgumentParser(description="AI-powered Job Screener")

    # Add arguments
    parser.add_argument('--dev', type=bool, required=False, help='Development Flag', default=False)
    parser.add_argument('--serp_override', type=bool, required=False, help='SERP Override Flag', default=False)

    args = parser.parse_args()

    print("[INFO] Running SERP extract...")
    serp_files = glob.glob(SERP_FOLDER + "/*.csv")
    serp_run_flag = True
    for file in serp_files:
        if file.split("_")[-1].split(".")[0] == TODAY:
            serp_run_flag = False
    
    if serp_run_flag or args.serp_override:
        serp_run()
    else:
        print("[INFO] Serp already ran today, skipping..")

    print("[INFO] Running OpenAI Rating prompt...")
    openai_rating_run()
    print("[INFO] Save successful!")

    print("[INFO] Running OpenAI Cover Letter prompt...")
    openai_cover_letter_run()
    print("[INFO] Save successful!")
