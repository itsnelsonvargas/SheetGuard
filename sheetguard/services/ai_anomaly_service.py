"""Service for interacting with Google Gemini AI to scan for data anomalies."""

import os
import pandas as pd
import google.generativeai as genai
from dotenv import load_dotenv

class AIAnomalyService:
    def __init__(self) -> None:
        load_dotenv()
        self.api_key = os.getenv("GEMINI_API_KEY")
        if self.api_key:
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel("gemini-1.5-flash")
        else:
            self.model = None

    def is_configured(self) -> bool:
        return bool(self.model)

    def scan_anomalies(self, df: pd.DataFrame) -> str:
        if not self.is_configured():
            raise ValueError("Gemini API Key is not configured. Please add it to the .env file.")
        
        # Profile the data briefly
        profile = []
        profile.append(f"Total Rows: {len(df)}")
        profile.append(f"Columns: {', '.join(df.columns)}")
        
        # Get a sample (up to 100 rows) for anomaly detection
        sample_size = min(100, len(df))
        sample_df = df.sample(n=sample_size) if len(df) > 100 else df
        sample_csv = sample_df.to_csv(index=True) # Keep index to reference specific rows

        prompt = f"""
You are an expert Data Forensic Analyst. I am providing you with a sample of a spreadsheet dataset.

DATA SAMPLE ({sample_size} rows):
```csv
{sample_csv}
```

Please scan this data for anomalies, suspicious entries, and logical inconsistencies. Focus on:
1. **Outliers**: Values that are mathematically or contextually extreme.
2. **Logical Breaks**: Data points that contradict each other (e.g., a 'Junior' with 20 years of experience, or a birth date in the future).
3. **Format Inconsistencies**: Hidden patterns of bad data entry that might bypass simple validation.
4. **Suspicious Clusters**: Groups of rows that look like duplicates or procedurally generated errors.

Format your response in Markdown:
- Use **## High Priority** for critical logical errors.
- Use **## Potential Outliers** for statistical anomalies.
- Use **## Observation** for general suspicious patterns.
- Reference specific row indices (the first column in the CSV) when identifying issues.

Be precise, cynical, and professional.
"""
        response = self.model.generate_content(prompt)
        return response.text
