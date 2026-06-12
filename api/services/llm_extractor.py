import os
import instructor
from openai import OpenAI
from pydantic import BaseModel
from typing import Optional
from schemas.gutachten import VehicleData, ModificationData

class LLMGutachtenExtraction(BaseModel):
    vehicle: VehicleData
    modification: ModificationData

def extract_gutachten_with_llm(text: str) -> Optional[LLMGutachtenExtraction]:
    from dotenv import load_dotenv
    load_dotenv()
    
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        return None

    try:
        # Patch the OpenAI client with Instructor
        client = instructor.from_openai(OpenAI(api_key=api_key))

        # Extract structured data
        response = client.chat.completions.create(
            model="gpt-5.4-nano",  # Fallback gracefully or let it use the user's provided routing
            response_model=LLMGutachtenExtraction,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a strict data extraction assistant. Extract vehicle and modification "
                        "data from the provided German 'Gutachten' (vehicle modification document). "
                        "Do not guess. Use exact strings and numbers found in the text."
                    ),
                },
                {"role": "user", "content": text},
            ],
            temperature=0.0,
            max_tokens=2000,
        )
        return response
    except Exception as e:
        print(f"LLM Extraction failed: {e}")
        return None
