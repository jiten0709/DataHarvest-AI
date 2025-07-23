from google import genai
from logging_config import parser_logger
import time
from typing import List
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

class GeminiParser:
    def __init__(self):
        self.logger = parser_logger
        self.client = None
        self._initialize_client()

    def _initialize_client(self) -> None:
        """Initialize Gemini client with error handling"""
        try:
            if not GEMINI_API_KEY:
                raise ValueError("GEMINI_API_KEY not found in environment variables")
            
            self.client = genai.Client(api_key=GEMINI_API_KEY)
            self.logger.info("Gemini client initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize Gemini client: {str(e)}")
            raise

    def parse_with_gemini(self, dom_chunks: List[str], parse_description: str) -> str:
        """
        Parse content chunks using the Gemini API with enhanced logging and error handling
        """
        if not dom_chunks:
            self.logger.warning("No DOM chunks provided for parsing")
            return ""
        
        if not parse_description.strip():
            self.logger.warning("No parse description provided")
            return ""
        
        start_time = time.time()
        self.logger.info(f"Starting parsing process for {len(dom_chunks)} chunks")
        self.logger.info(f"Parse description: {parse_description}")
        
        parsed_results = []
        successful_parses = 0
        failed_parses = 0
        
        for i, chunk in enumerate(dom_chunks, start=1):
            chunk_start_time = time.time()
            self.logger.info(f"Processing chunk {i}/{len(dom_chunks)} (size: {len(chunk)} chars)")
            
            try:
                prompt = TEMPLATE.format(dom_content=chunk, parse_description=parse_description)
                
                response = self.client.models.generate_content(
                    model=GEMINI_MODEL,
                    contents=prompt
                )
                
                if response and hasattr(response, 'text') and response.text.strip():
                    parsed_results.append(response.text.strip())
                    successful_parses += 1
                    chunk_time = time.time() - chunk_start_time
                    self.logger.info(f"Chunk {i} parsed successfully in {chunk_time:.2f}s")
                else:
                    self.logger.warning(f"Empty or invalid response for chunk {i}")
                    
            except Exception as e:
                failed_parses += 1
                self.logger.error(f"Error parsing chunk {i}: {str(e)}")
                # Continue processing other chunks
                continue
        
        # Log summary
        total_time = time.time() - start_time
        self.logger.info(f"Parsing completed in {total_time:.2f}s")
        self.logger.info(f"Success rate: {successful_parses}/{len(dom_chunks)} chunks")
        
        if failed_parses > 0:
            self.logger.warning(f"Failed to parse {failed_parses} chunks")
        
        final_result = "\n\n".join(parsed_results) if parsed_results else ""
        self.logger.info(f"Final result length: {len(final_result)} characters")
        
        return final_result

# Create instance for backward compatibility
parser = GeminiParser()
parse_with_gemini = parser.parse_with_gemini