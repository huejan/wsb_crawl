import google.generativeai as genai
import os
# from dotenv import load_dotenv # Removed, should be loaded in main.py

# load_dotenv() # Removed

def configure_gemini():
    """
    Configures the Gemini API with the API key from environment variables.
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("Missing GEMINI_API_KEY in .env file.")
    genai.configure(api_key=api_key)
    print("Gemini API configured successfully.")

def get_gemini_model(model_name="gemini-1.5-flash-latest"): # Using 1.5 Flash as requested
    """
    Returns an instance of the specified Gemini model.
    """
    try:
        configure_gemini() # Ensure API is configured before getting model
        model = genai.GenerativeModel(model_name)
        print(f"Gemini model '{model_name}' loaded successfully.")
        return model
    except Exception as e:
        print(f"Error loading Gemini model '{model_name}': {e}")
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
        print("No text content provided for analysis.")
        return None

    prompt = custom_prompt
    if not prompt:
        # Default prompt designed to identify stock tickers and reasons for discussion
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
  {
    "symbol": "GME",
    "reason": "Discussed due to recent price volatility and short squeeze potential.",
    "sentiment": "speculative"
  },
  {
    "symbol": "SPY",
    "reason": "Mentioned in the context of overall market trends.",
    "sentiment": "neutral"
  }
]

Text for analysis:
---
{text_content}
---
JSON Output:
"""

    try:
        # Configure the model to output JSON
        generation_config = genai.types.GenerationConfig(
            response_mime_type="application/json"
        )
        response = model.generate_content(prompt, generation_config=generation_config)

        # Debug: print the full response if needed
        # print("Full Gemini Response:", response)

        if response.parts:
            # Assuming the model respects the JSON output instruction
            return response.text
        elif response.prompt_feedback:
             # Handle cases where the prompt might be blocked
            print(f"Gemini prompt feedback: {response.prompt_feedback}")
            # Return a string that indicates an error but won't break JSON parsing if something tries
            return '{ "error": "Analysis failed due to prompt issues", "details": "' + str(response.prompt_feedback).replace('"',"'") + '" }'
        else:
            # This case should ideally be covered by response.parts or prompt_feedback
            print("Gemini response had no usable parts and no explicit feedback.")
            return '{ "error": "No analysis result from Gemini" }' # Return valid JSON error

    except Exception as e:
        print(f"Error analyzing text with Gemini: {e}")
        # Potentially log more details about the error or the text that caused it
        return '{ "error": "Error during Gemini analysis", "details": "' + str(e).replace('"',"'") + '" }' # Return valid JSON error

if __name__ == "__main__":
    # This is for testing the gemini_client.py directly
    print("Testing Gemini client with JSON output...")
    try:
        model = get_gemini_model()
        if model:
            sample_text_1 = "I think GME is going to the moon! Cramer said otherwise though. What about SPY today? And some $PLTR for good measure."
            print(f"\n--- Analyzing sample text 1: ---\n'{sample_text_1}'")
            analysis_1 = analyze_text_with_gemini(model, sample_text_1)
            print("\n--- Gemini Analysis 1 (JSON): ---")
            print(analysis_1)
            # Try parsing it
            import json
            try:
                parsed = json.loads(analysis_1)
                print("Successfully parsed JSON output.")
                if isinstance(parsed, list):
                    print(f"Found {len(parsed)} items.")
                elif isinstance(parsed, dict) and "error" in parsed:
                    print(f"Gemini returned an error object: {parsed['error']}")
            except json.JSONDecodeError as je:
                print(f"Failed to parse JSON output: {je}")


            sample_text_2 = "Anyone looking at NVDA earnings next week? Could be huge. TSLA also seems quiet lately."
            print(f"\n--- Analyzing sample text 2: ---\n'{sample_text_2}'")
            analysis_2 = analyze_text_with_gemini(model, sample_text_2)
            print("\n--- Gemini Analysis 2 (JSON): ---")
            print(analysis_2)
            try:
                parsed = json.loads(analysis_2)
                print("Successfully parsed JSON output.")
            except json.JSONDecodeError as je:
                print(f"Failed to parse JSON output for sample 2: {je}")

            sample_text_3 = "Just bought some apples and bananas at the grocery store."
            print(f"\n--- Analyzing sample text 3 (no stocks): ---\n'{sample_text_3}'")
            analysis_3 = analyze_text_with_gemini(model, sample_text_3)
            print("\n--- Gemini Analysis 3 (JSON - should be empty array or error): ---")
            print(analysis_3)
            try:
                parsed = json.loads(analysis_3)
                print("Successfully parsed JSON output for sample 3.")
                if isinstance(parsed, list) and not parsed:
                    print("Received empty array as expected for no stocks.")
            except json.JSONDecodeError as je:
                print(f"Failed to parse JSON output for sample 3: {je}")

    except ValueError as ve:
        print(f"Configuration Error: {ve}")
    except Exception as e:
        print(f"An unexpected error occurred during Gemini client test: {e}")
        import traceback
        traceback.print_exc()
        # For now, using default generation config.
        # response = model.generate_content(prompt, generation_config=genai.types.GenerationConfig(...))
        response = model.generate_content(prompt)

        # Debug: print the full response if needed
        # print("Full Gemini Response:", response)

        if response.parts:
            return response.text
        elif response.prompt_feedback:
             # Handle cases where the prompt might be blocked
            print(f"Gemini prompt feedback: {response.prompt_feedback}")
            return f"Analysis failed due to prompt issues: {response.prompt_feedback}"
        else:
            # This case should ideally be covered by response.parts or prompt_feedback
            print("Gemini response had no usable parts and no explicit feedback.")
            return "No analysis result from Gemini."

    except Exception as e:
        print(f"Error analyzing text with Gemini: {e}")
        # Potentially log more details about the error or the text that caused it
        return f"Error during Gemini analysis: {str(e)}"

if __name__ == "__main__":
    # This is for testing the gemini_client.py directly
    print("Testing Gemini client...")
    try:
        model = get_gemini_model()
        if model:
            sample_text_1 = "I think GME is going to the moon! Cramer said otherwise though. What about SPY today?"
            print(f"\n--- Analyzing sample text 1: ---\n'{sample_text_1}'")
            analysis_1 = analyze_text_with_gemini(model, sample_text_1)
            print("\n--- Gemini Analysis 1: ---")
            print(analysis_1)

            sample_text_2 = "Anyone looking at NVDA earnings next week? Could be huge. TSLA also seems quiet lately."
            print(f"\n--- Analyzing sample text 2: ---\n'{sample_text_2}'")
            analysis_2 = analyze_text_with_gemini(model, sample_text_2)
            print("\n--- Gemini Analysis 2: ---")
            print(analysis_2)

            sample_text_3 = "Just bought some appels and bananas at the grocery store."
            print(f"\n--- Analyzing sample text 3 (no stocks): ---\n'{sample_text_3}'")
            analysis_3 = analyze_text_with_gemini(model, sample_text_3)
            print("\n--- Gemini Analysis 3: ---")
            print(analysis_3)

    except ValueError as ve:
        print(f"Configuration Error: {ve}")
    except Exception as e:
        print(f"An unexpected error occurred during Gemini client test: {e}")
