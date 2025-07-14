import google.generativeai as genai
import os
import logging
import json

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
        logger.error(f"Failed to configure Gemini API: {e}", exc_info=True)
        raise

def get_gemini_model(model_name="gemini-1.5-flash"): # Reverted to 1.5 flash, as 2.5 is not a known public model
    try:
        configure_gemini()
        model = genai.GenerativeModel(model_name)
        logger.info(f"Gemini model '{model_name}' loaded successfully.")
        return model
    except Exception as e:
        logger.error(f"Error loading Gemini model '{model_name}': {e}", exc_info=True)
        raise

def analyze_text_with_gemini(model: genai.GenerativeModel, text_content: str, custom_prompt: str = None):
    """
    Analyzes the given text and returns a concise summary.
    """
    # Define a constant for no summary
    NO_SUMMARY_MARKER = "NO_SUMMARY_AVAILABLE"

    if not text_content or not text_content.strip():
        logger.warning("No text content provided for Gemini analysis.")
        return NO_SUMMARY_MARKER

    prompt = custom_prompt
    if not prompt:
        prompt = f"""\
You are a financial news summarizer. Read the following text from a Reddit post.
Your task is to provide a concise, neutral, 1-2 sentence summary of the main topic or question in the text.

- If the text is a substantive discussion, question, or DD (due diligence) about finance, stocks, or markets, summarize it.
- If the text is just a low-effort "meme", a screenshot of gains/losses without context, contains no real text, or is otherwise not a meaningful discussion, please respond with the exact string "{NO_SUMMARY_MARKER}" and nothing else.

Do not add any preamble like "This post is about...". Respond only with the summary or the marker string.

Text for analysis:
---
{text_content}
---
Summary:
"""

    try:
        # We are now requesting plain text, not JSON
        response = model.generate_content(prompt)

        if response.parts:
            summary = response.text.strip()
            logger.debug(f"Gemini raw summary response: {summary}")
            return summary
        elif response.prompt_feedback:
            logger.warning(f"Gemini prompt feedback: {response.prompt_feedback}")
            return NO_SUMMARY_MARKER
        else:
            logger.warning("Gemini response had no usable parts and no explicit feedback.")
            return NO_SUMMARY_MARKER

    except Exception as e:
        logger.error(f"Error analyzing text with Gemini for summary: {e}", exc_info=True)
        return NO_SUMMARY_MARKER

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG,
                        format='%(asctime)s %(levelname)s [%(name)s] [%(threadName)s] %(message)s',
                        datefmt='%Y-%m-%d %H:%M:%S')
    logger.info("Testing Gemini client with new summarization prompt...")
    try:
        # This test requires a valid GEMINI_API_KEY in the environment
        model = get_gemini_model()
        if model:
            sample_texts = [
                "I think GME is going to the moon! Cramer said otherwise though. What about SPY today? The market seems volatile.",
                "Check out my 1000% gain on this options play! [image]",
                "Daily Discussion Thread",
                "Just a picture of a rocket emoji"
            ]

            for i, text in enumerate(sample_texts):
                logger.info(f"--- Analyzing sample text {i+1}: ---\n'{text}'")
                summary = analyze_text_with_gemini(model, text)
                logger.info(f"--- Gemini Summary {i+1}: ---")
                logger.info(summary)
                logger.info("--- End Sample ---")

    except ValueError as ve:
        logger.error(f"Configuration Error, likely missing API key for test: {ve}")
    except Exception as e:
        logger.error(f"An unexpected error occurred during Gemini client test: {e}", exc_info=True)
