import google.generativeai as genai
import os
import logging # Import logging
# from dotenv import load_dotenv # Removed, should be loaded in main.py

logger = logging.getLogger(__name__) # Get logger instance

def configure_gemini():
    """
    Configures the Gemini API with the API key from environment variables.
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        err_msg = "Missing GEMINI_API_KEY in .env file."
        logger.error(err_msg)
        raise ValueError(err_msg)
    try:
        genai.configure(api_key=api_key)
        logger.info("Gemini API configured successfully.")
    except Exception as e:
        logger.error(f"Failed to configure Gemini API: {{e}}", exc_info=True)
        raise

def get_gemini_model(model_name="gemini-2.5-flash"): # Changed to 2.5 as per user request
    """
    Returns an instance of the specified Gemini model.
    """
    try:
        configure_gemini() # Ensure API is configured before getting model
        model = genai.GenerativeModel(model_name)
        logger.info(f"Gemini model '{{model_name}}' loaded successfully.")
        return model
    except Exception as e:
        logger.error(f"Error loading Gemini model '{{model_name}}': {{e}}", exc_info=True)
        raise

def analyze_text_with_gemini(model: genai.GenerativeModel, text_content: str, custom_prompt: str = None):
    """
    Analyzes the given text content using the provided Gemini model.

    Args:
        model: An initialized Gemini GenerativeModel.
        text_content: The text to analyze.
        custom_prompt: An optional custom prompt to guide the analysis.
                       If None, a default prompt for stock discussion analysis will be used.

    Returns:
        The analysis result from Gemini as a string.
    """
    if not text_content:
        logger.warning("No text content provided for Gemini analysis.")
        return '[]' # Return empty JSON array string for no content

    prompt = custom_prompt
    if not prompt:
        prompt = f"""\
Analyze the following text from a social media discussion about finance.
Identify any stock tickers (e.g., GME, AAPL, TSLA) or ETF symbols (e.g., SPY, QQQ) mentioned.

Your response MUST be a JSON array of objects. Each object should represent one identified symbol and have the following fields:
- "symbol": The stock ticker or ETF symbol (string).
- "reason": A brief summary of why it is being discussed in the provided text. If multiple reasons, synthesize them (string).
- "sentiment": The perceived sentiment of the discussion towards this symbol (string, e.g., "positive", "negative", "neutral", "speculative", "mixed", "unknown").

If no specific stocks or ETFs are clearly discussed, or if you cannot determine the context for a mentioned symbol, return an empty JSON array: [].
Do not include any explanations or text outside of the JSON array.

Example of desired JSON output:
[
  {{
    "symbol": "GME",
    "reason": "Discussed due to recent price volatility and short squeeze potential.",
    "sentiment": "speculative"
  }},
  {{
    "symbol": "SPY",
    "reason": "Mentioned in the context of overall market trends.",
    "sentiment": "neutral"
  }}
]

Text for analysis:
---
{{text_content}}
---
JSON Output:
"""

    try:
        generation_config = genai.types.GenerationConfig(
            response_mime_type="application/json"
        )
        response = model.generate_content(prompt, generation_config=generation_config)

        if response.parts:
            logger.debug(f"Gemini raw response text: {{response.text[:500]}}")
            return response.text
        elif response.prompt_feedback:
            logger.warning(f"Gemini prompt feedback: {{response.prompt_feedback}}")
            return '{{ "error": "Analysis failed due to prompt issues", "details": "' + str(response.prompt_feedback).replace('"',"'") + '" }}'
        else:
            logger.warning("Gemini response had no usable parts and no explicit feedback.")
            return '{{ "error": "No analysis result from Gemini" }}'

    except Exception as e:
        logger.error(f"Error analyzing text with Gemini: {{e}}", exc_info=True)
        return '{{ "error": "Error during Gemini analysis", "details": "' + str(e).replace('"',"'") + '" }}'

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG,
                        format='%(asctime)s %(levelname)s [%(name)s] %(message)s',
                        datefmt='%Y-%m-%d %H:%M:%S')
    logger.info("Testing Gemini client with JSON output...")
    try:
        model = get_gemini_model()
        if model:
            sample_text_1 = "I think GME is going to the moon! Cramer said otherwise though. What about SPY today? And some $PLTR for good measure."
            logger.info(f"--- Analyzing sample text 1: ---\n'{{sample_text_1}}'")
            analysis_1 = analyze_text_with_gemini(model, sample_text_1)
            logger.info("--- Gemini Analysis 1 (JSON): ---")
            logger.info(analysis_1)
            import json
            try:
                parsed = json.loads(analysis_1)
                logger.info("Successfully parsed JSON output.")
                if isinstance(parsed, list):
                    logger.info(f"Found {{len(parsed)}} items.")
                elif isinstance(parsed, dict) and "error" in parsed:
                    logger.warning(f"Gemini returned an error object: {{parsed['error']}}")
            except json.JSONDecodeError as je:
                logger.error(f"Failed to parse JSON output: {{je}}")

            sample_text_2 = "Anyone looking at NVDA earnings next week? Could be huge. TSLA also seems quiet lately."
            logger.info(f"--- Analyzing sample text 2: ---\n'{{sample_text_2}}'")
            analysis_2 = analyze_text_with_gemini(model, sample_text_2)
            logger.info("--- Gemini Analysis 2 (JSON): ---")
            logger.info(analysis_2)
            try:
                parsed = json.loads(analysis_2)
                logger.info("Successfully parsed JSON output for sample 2.")
            except json.JSONDecodeError as je:
                logger.error(f"Failed to parse JSON output for sample 2: {{je}}")

            sample_text_3 = "Just bought some apples and bananas at the grocery store."
            logger.info(f"--- Analyzing sample text 3 (no stocks): ---\n'{{sample_text_3}}'")
            analysis_3 = analyze_text_with_gemini(model, sample_text_3)
            logger.info("--- Gemini Analysis 3 (JSON - should be empty array or error): ---")
            logger.info(analysis_3)
            try:
                parsed = json.loads(analysis_3)
                logger.info("Successfully parsed JSON output for sample 3.")
                if isinstance(parsed, list) and not parsed:
                    logger.info("Received empty array as expected for no stocks.")
            except json.JSONDecodeError as je:
                logger.error(f"Failed to parse JSON output for sample 3: {{je}}")

    except ValueError as ve:
        logger.error(f"Configuration Error: {{ve}}")
    except Exception as e:
        logger.error(f"An unexpected error occurred during Gemini client test: {{e}}", exc_info=True)
