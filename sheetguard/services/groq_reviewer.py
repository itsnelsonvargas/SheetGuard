"""Service for interacting with Groq AI to review datasets using open models like Llama 3."""

import os
import pandas as pd
from groq import Groq
from dotenv import load_dotenv

class GroqReviewService:
    def __init__(self) -> None:
        load_dotenv()
        self.api_key = os.getenv("GROQ_API_KEY")
        if self.api_key:
            self.client = Groq(api_key=self.api_key)
            self.model = "llama-3.3-70b-versatile" # Latest flagship model
        else:
            self.client = None
            self.model = None

    def is_configured(self) -> bool:
        return bool(self.client)

    def review_data(self, df: pd.DataFrame) -> str:
        if not self.is_configured():
            raise ValueError("Groq API Key is not configured. Please add it to the .env file.")
        
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
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "You are a professional data analyst."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1, # Low temperature for analytical consistency
        )
        return response.choices[0].message.content
