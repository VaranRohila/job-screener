# Job Matching Automation Script

This script automates the process of sourcing job postings from Google Jobs via SerpAPI, and then evaluates each job's suitability for a specific candidate profile using OpenAI's GPT model. It outputs a ranked list of job matches based on a weighted scoring system and saves the results in a formatted Excel file.

---

## 🔧 Features

- **Automated Job Scraping**: Uses SerpAPI to pull up to 6 pages of recent job postings for **Senior Data Scientist** roles in the **United States**.
- **Job Filtering**: Filters listings to include only those with a LinkedIn application option.
- **Job Evaluation with GPT**: Evaluates job listings against a resume using a 14-point weighted criteria system.
- **Weighted Scoring**: Calculates a `final_score` as a weighted average of individual criteria scores.
- **Excel Output**: Outputs results to an Excel file with clickable LinkedIn links and sorted by best match.

---

## 📋 Requirements

- Python 3.7+
- A `.env` file with the following environment variables:
  - `SERP_KEY`: SerpAPI key
  - `OPENAI_API_KEY`: OpenAI key

- A `resume.txt` file containing the candidate’s resume as plain text.

---

## 🧠 Evaluation Criteria

Each job is scored on the following criteria (with respective weights):

1. Role Fit – 10  
2. Experience Requirement – 10  
3. Growth Opportunities – 9  
4. Role Level (IC only) – 9  
5. Team & Manager Quality – 8  
6. Company Stability & Mission – 8  
7. Compensation ($240K+ target) – 8  
8. Work-Life Balance – 7  
9. Technical Stack Relevance – 6  
10. Location / Remote Flexibility – 5  
11. Perks & Benefits – 3  
12. Job Description Quality – 2  
13. Distance from Jersey City, NJ – 7  
14. Visa Sponsorship (H1B required) – 10

---

## 🚀 Usage

1. Place your `resume.txt` file in the same directory as the script.
2. Ensure your `.env` file contains valid API keys.
3. Run the script:
   ```bash
   python script_name.py
    ```
4. Output Excel will be saved in the outputs/ folder with today's date in the filename.

## 📁 Outputs
CSV File (in serp_extract/): Raw scraped job listings.

Excel File (in outputs/): Final ranked and formatted job match results, with each job’s score breakdown and clickable LinkedIn links.

## 📝 Notes
The script avoids re-running the SERP job fetch if a file already exists for the current date.

Jobs that fail GPT JSON parsing are skipped but logged for review.
