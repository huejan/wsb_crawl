from .reddit_client import get_reddit_instance, get_wallstreetbets_posts
from .gemini_client import get_gemini_model, analyze_text_with_gemini
import time
import json
import logging

logger = logging.getLogger(__name__)

ANALYZED_DATA_STORE = []
PROCESSED_ITEM_IDS = set()

def extract_relevant_text_from_post(post):
    text_parts = [post.title]
    if post.selftext:
        text_parts.append(post.selftext)
    return "\n".join(text_parts)

def process_single_submission(submission, gemini_model):
    if submission.id in PROCESSED_ITEM_IDS:
        logger.debug(f"Skipping already processed submission ID: {{submission.id}}")
        return None

    logger.info(f"Processing Reddit submission: {{submission.title[:100]}}... (ID: {{submission.id}})")
    text_to_analyze = extract_relevant_text_from_post(submission)

    if not text_to_analyze.strip():
        logger.warning(f"No text content found for submission ID: {{submission.id}}")
        PROCESSED_ITEM_IDS.add(submission.id)
        return None

    analysis_json_str = analyze_text_with_gemini(gemini_model, text_to_analyze)

    try:
        parsed_analysis = json.loads(analysis_json_str)

        if isinstance(parsed_analysis, dict) and "error" in parsed_analysis:
            logger.error(f"Gemini analysis for {{submission.id}} returned an error: {{parsed_analysis.get('details', parsed_analysis['error'])}}")
            PROCESSED_ITEM_IDS.add(submission.id)
            return None

        if not isinstance(parsed_analysis, list):
            logger.error(f"Unexpected data type from Gemini analysis for {{submission.id}}. Expected list, got {{type(parsed_analysis)}}. Content: {{analysis_json_str[:200]}}")
            PROCESSED_ITEM_IDS.add(submission.id)
            return None

        logger.info(f"Gemini Analysis for {{submission.id}} (parsed {{len(parsed_analysis)}} symbols)")
        logger.debug(f"Parsed analysis for {{submission.id}}: {{parsed_analysis}}")

        ANALYZED_DATA_STORE.append({
            'source_id': submission.id,
            'source_title': submission.title,
            'source_url': f"https://www.reddit.com{{submission.permalink}}",
            'analyzed_symbols': parsed_analysis,
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())
        })
        PROCESSED_ITEM_IDS.add(submission.id)
        return parsed_analysis

    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON analysis from Gemini for submission ID {{submission.id}}: {{e}}", exc_info=True)
        logger.debug(f"Received string from Gemini for {{submission.id}}: {{analysis_json_str[:500]}}")
        PROCESSED_ITEM_IDS.add(submission.id)
        return None
    except Exception as e:
        logger.error(f"An unexpected error occurred during processing of submission {{submission.id}}: {{e}}", exc_info=True)
        PROCESSED_ITEM_IDS.add(submission.id)
        return None

def run_analysis_cycle(reddit_instance, gemini_model, post_limit=10):
    logger.info(f"--- Starting new analysis cycle at {{time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())}} ---")

    posts = get_wallstreetbets_posts(reddit_instance, limit=post_limit)

    if not posts:
        logger.warning("No posts fetched in this cycle.")
        return

    new_analyses_count = 0
    for post in posts:
        if post.id not in PROCESSED_ITEM_IDS:
            result = process_single_submission(post, gemini_model)
            if result is not None: # Check if result is not None (can be an empty list)
                new_analyses_count +=1
        else:
            logger.debug(f"Post {{post.id}} already processed. Skipping.")

    logger.info(f"--- Analysis cycle complete. Processed {{len(posts)}} posts. Added {{new_analyses_count}} new analyses. ---")
    logger.debug(f"Total items in PROCESSED_ITEM_IDS: {{len(PROCESSED_ITEM_IDS)}}")
    logger.debug(f"Total items in ANALYZED_DATA_STORE: {{len(ANALYZED_DATA_STORE)}}")

def get_analyzed_data():
    return sorted(ANALYZED_DATA_STORE, key=lambda x: x['timestamp'], reverse=True)

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG,
                        format='%(asctime)s %(levelname)s [%(name)s] [%(threadName)s] %(message)s',
                        datefmt='%Y-%m-%d %H:%M:%S')
    logger.info("Testing analysis module...")
    try:
        reddit = get_reddit_instance()
        gemini = get_gemini_model()

        if reddit and gemini:
            run_analysis_cycle(reddit, gemini, post_limit=5)

            logger.info("--- Current Analyzed Data Store (Structured): ---")
            for item in get_analyzed_data():
                logger.info(f"ID: {{item['source_id']}}, Title: {{item['source_title'][:60]}}..., Symbols: {{item.get('analyzed_symbols')}}")

            logger.info("--- Running second analysis cycle (should skip previous posts) ---")
            run_analysis_cycle(reddit, gemini, post_limit=5)

            logger.info("--- Final Analyzed Data Store (Structured): ---")
            for item in get_analyzed_data():
                logger.info(f"ID: {{item['source_id']}}, Title: {{item['source_title'][:60]}}..., Symbols: {{item.get('analyzed_symbols')}}")
        else:
            logger.error("Failed to initialize Reddit or Gemini instances for testing.")

    except Exception as e:
        logger.error(f"An error occurred during analysis module test: {{e}}", exc_info=True)
