from google import genai
import os
from dotenv import load_dotenv
load_dotenv("../.env")

# global configurations
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL")

TEMPLATE = """
You are an expert data extraction assistant. Your task is to extract specific information from the provided web content with precision and accuracy.

**Content to analyze:**
{dom_content}

**Extraction requirements:**
{parse_description}

**Instructions:**
1. Extract ONLY the information that directly matches the specified requirements
2. Return the data in a clean, structured format (JSON, list, or plain text as appropriate)
3. If multiple items match, present them in an organized manner
4. If no relevant information is found, return an empty string
5. Do not include explanations, comments, or additional text
6. Ensure extracted data is accurate and complete
7. Maintain the original formatting/structure when relevant

**Output the extracted data below:**
"""

client = genai.Client(api_key=GEMINI_API_KEY)

def parse_with_gemini(dom_chunks, parse_description):
    """
    Parses content chunks using the Gemini API.

    Args:
        dom_chunks (list): A list of strings, where each string is a chunk of the DOM.
        parse_description (str): The user's instruction for what to extract.

    Returns:
        str: The combined extracted data from all chunks.
    """
    parsed_results = []
    
    for i, chunk in enumerate(dom_chunks, start=1):
        prompt = TEMPLATE.format(dom_chunks=chunk, parse_description=parse_description)
        
        try:
            response = client.models.generate_content(
                model=GEMINI_MODEL,
                contents=prompt
            )
            # Assuming the response object has a 'text' attribute with the result
            if response and hasattr(response, 'text'):
                parsed_results.append(response.text)
            print(f"Parsed batch: {i} of {len(dom_chunks)}")
            
        except Exception as e:
            print(f"An error occurred while parsing chunk {i}: {e}")
            # Optionally, append an error message or empty string
            parsed_results.append("")

        return "\n".join(parsed_results)
    