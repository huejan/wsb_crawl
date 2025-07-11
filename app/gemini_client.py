import google.generativeai as genai
import os
import logging

logger = logging.getLogger(__name__)

def configure_gemini():
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
    try:
        configure_gemini()
        model = genai.GenerativeModel(model_name)
        logger.info(f"Gemini model '{{model_name}}' loaded successfully.")
        return model
    except Exception as e:
        logger.error(f"Error loading Gemini model '{{model_name}}': {{e}}", exc_info=True)
        raise

def analyze_text_with_gemini(model: genai.GenerativeModel, text_content: str, custom_prompt: str = None):
    if not text_content:
        logger.warning("No text content provided for Gemini analysis.")
        # Return a JSON object string with empty lists, matching the new expected structure
        return '{ "analyzed_symbols": [], "discussion_topics": [], "mentioned_companies": [] }'

    prompt = custom_prompt
    if not prompt:
        prompt = f"""\
Analyze the following text from a social media discussion about finance.
Your response MUST be a single JSON object.

The JSON object should have the following top-level fields:
- "analyzed_symbols": An array of objects. Each object represents one identified stock ticker (e.g., GME, AAPL, TSLA) or ETF symbol (e.g., SPY, QQQ) and MUST have the following fields:
    - "symbol": The stock ticker or ETF symbol (string).
    - "reason": A brief summary of why this specific symbol is being discussed in the provided text (string).
    - "sentiment": The perceived sentiment of the discussion towards this specific symbol (string, e.g., "positive", "negative", "neutral", "speculative", "mixed", "unknown").
- "discussion_topics": An array of strings, listing 1-3 main financial topics or themes discussed in the text (e.g., "Earnings Report", "Market Volatility", "Short Squeeze Interest", "New Product Launch", "Analyst Upgrade/Downgrade"). If no clear topics, return an empty array.
- "mentioned_companies": An array of strings, listing any company names explicitly mentioned in the text, even if not as a ticker symbol (e.g., "NVIDIA Corp", "Microsoft", "Citadel Securities"). If no specific companies are named, return an empty array.

If no specific stocks/ETFs are discussed, "analyzed_symbols" should be an empty array: [].
If no topics are identified, "discussion_topics" should be an empty array: [].
If no companies are named, "mentioned_companies" should be an empty array: [].

Do not include any explanations or text outside of the main JSON object.

Example of desired JSON output:
{{
  "analyzed_symbols": [
    {{
      "symbol": "GME",
      "reason": "Price surge and renewed interest in short squeeze potential.",
      "sentiment": "speculative"
    }},
    {{
      "symbol": "TSLA",
      "reason": "Mentioned regarding upcoming earnings announcement.",
      "sentiment": "neutral"
    }}
  ],
  "discussion_topics": [
    "Short Squeeze Speculation",
    "Upcoming Earnings Reports",
    "Retail Investor Activity"
  ],
  "mentioned_companies": [
    "GameStop",
    "Tesla Inc."
  ]
}}

If the text contains no relevant financial discussion, the output should be:
{{
  "analyzed_symbols": [],
  "discussion_topics": [],
  "mentioned_companies": []
}}

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
            return '{{ "error": "Analysis failed due to prompt issues", "details": "' + str(response.prompt_feedback).replace('"',"'") + '", "analyzed_symbols": [], "discussion_topics": [], "mentioned_companies": [] }}'
        else:
            logger.warning("Gemini response had no usable parts and no explicit feedback.")
            return '{{ "error": "No analysis result from Gemini", "analyzed_symbols": [], "discussion_topics": [], "mentioned_companies": [] }}'

    except Exception as e:
        logger.error(f"Error analyzing text with Gemini: {{e}}", exc_info=True)
        return '{{ "error": "Error during Gemini analysis", "details": "' + str(e).replace('"',"'") + '", "analyzed_symbols": [], "discussion_topics": [], "mentioned_companies": [] }}'

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG,
                        format='%(asctime)s %(levelname)s [%(name)s] [%(threadName)s] %(message)s',
                        datefmt='%Y-%m-%d %H:%M:%S')
    logger.info("Testing Gemini client with new JSON object output...")
    try:
        model = get_gemini_model()
        if model:
            sample_texts = [
                "I think GME is going to the moon! Cramer said otherwise though. What about SPY today? And some $PLTR for good measure. The main topic is clearly stonks going up, maybe also something about market manipulation by Citadel.",
                "Anyone looking at NVDA earnings next week for NVIDIA Corp? Could be huge. TSLA also seems quiet lately. General market sentiment seems a bit off.",
                "Just bought some apples and bananas at the grocery store. This is not financial advice."
            ]

            import json
            for i, text in enumerate(sample_texts):
                logger.info(f"--- Analyzing sample text {{i+1}}: ---\n'{{text}}'")
                analysis_str = analyze_text_with_gemini(model, text)
                logger.info(f"--- Gemini Analysis {{i+1}} (JSON Object): ---")
                logger.info(analysis_str)
                try:
                    parsed = json.loads(analysis_str)
                    logger.info(f"Successfully parsed JSON output for sample {{i+1}}.")
                    if "error" in parsed:
                        logger.warning(f"Gemini returned an error object: {{parsed['error']}}")
                    else:
                        logger.info(f"  Symbols: {{parsed.get('analyzed_symbols')}}")
                        logger.info(f"  Topics: {{parsed.get('discussion_topics')}}")
                        logger.info(f"  Companies: {{parsed.get('mentioned_companies')}}")

                except json.JSONDecodeError as je:
                    logger.error(f"Failed to parse JSON output for sample {{i+1}}: {{je}}")
                logger.info("--- End Sample ---")

    except ValueError as ve: # Catches API key issues etc.
        logger.error(f"Configuration Error: {{ve}}", exc_info=True)
    except Exception as e:
        logger.error(f"An unexpected error occurred during Gemini client test: {{e}}", exc_info=True)
