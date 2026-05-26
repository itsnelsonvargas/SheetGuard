"""Service for interacting with Google Gemini AI to review datasets."""

import os
import pandas as pd
import google.generativeai as genai
from dotenv import load_dotenv

class AIReviewService:
    def __init__(self) -> None:
        load_dotenv()
        self.api_key = os.getenv("GEMINI_API_KEY")
        if self.api_key:
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel("gemini-2.5-flash")
        else:
            self.model = None

    def is_configured(self) -> bool:
        return bool(self.model)

    def review_data(self, df: pd.DataFrame) -> str:
        if not self.is_configured():
            raise ValueError("Gemini API Key is not configured. Please add it to the .env file.")
        
        # Profile the data
        profile = []
        profile.append(f"Total Rows: {len(df)}")
        profile.append(f"Total Columns: {len(df.columns)}")
        profile.append("\nColumns Summary:")
        for col in df.columns:
            dtype = df[col].dtype
            missing = df[col].isna().sum()
            unique = df[col].nunique()
            profile.append(f"- {col} (Type: {dtype}, Missing: {missing}, Unique: {unique})")

        # Get a sample (up to 50 rows)
        sample_size = min(50, len(df))
        # Ensure we have a random sample to catch anomalies, unless it's very small
        sample_df = df.sample(n=sample_size) if len(df) > 50 else df
        sample_csv = sample_df.to_csv(index=False)

        prompt = f"""
You are an expert Data Quality Analyst. I am providing you with a summary profile and a random sample of a spreadsheet dataset.

DATA PROFILE:
{chr(10).join(profile)}

DATA SAMPLE ({sample_size} random rows):
```csv
{sample_csv}
```

Please review this dataset and provide:
1. **General Insights**: What does this data appear to be about? What are the key patterns?
2. **Data Quality Issues**: Are there any obvious anomalies, missing values, or inconsistent formats?
3. **Suggested Cleaning Rules**: Provide 3-5 specific rules we should enforce (e.g. 'Email column must be a valid email', 'Amount must be greater than 0', 'Status should be in [Active, Inactive]'). 

Format your response in Markdown using bullet points, headers, and code blocks where appropriate. Be concise and actionable.
"""
        response = self.model.generate_content(prompt)
        return response.text
