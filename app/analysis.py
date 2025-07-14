from .reddit_client import get_reddit_instance, get_wallstreetbets_posts
from .gemini_client import analyze_text_with_gemini
import time
import logging

logger = logging.getLogger(__name__)

# --- In-Memory Data Stores ---
ANALYZED_DATA_STORE = []
PROCESSED_ITEM_IDS = set()

def extract_relevant_text_from_post(post):
    """
    Extracts text from a PRAW post object, including title and selftext.
    """
    text_parts = [post.title]
    if post.selftext:
        text_parts.append(post.selftext)
    return "\n".join(text_parts)

def process_single_submission(submission, gemini_model):
    """
    Processes a single Reddit submission, gets a summary from Gemini,
    and stores the result.
    """
    if submission.id in PROCESSED_ITEM_IDS:
        logger.debug(f"Skipping already processed submission ID: {{submission.id}}")
        return None

    logger.info(f"Processing Reddit submission for summary: {{submission.title[:100]}}... (ID: {{submission.id}})")
    text_to_analyze = extract_relevant_text_from_post(submission)

    if not text_to_analyze.strip():
        logger.warning(f"No text content found for submission ID: {{submission.id}}")
        PROCESSED_ITEM_IDS.add(submission.id)
        return None

    # Get the summary string from Gemini
    summary = analyze_text_with_gemini(gemini_model, text_to_analyze)

    # The NO_SUMMARY_MARKER is now handled in the template,
    # but we can still log if we get a valid summary or not.
    if summary and summary != "NO_SUMMARY_AVAILABLE":
        logger.info(f"Generated summary for {{submission.id}}: {{summary}}")
    else:
        logger.info(f"No summary generated for {{submission.id}} (post may be irrelevant).")

    # Store the result, including the marker if applicable
    ANALYZED_DATA_STORE.append({
        'source_id': submission.id,
        'source_title': submission.title,
        'source_url': f"https://www.reddit.com{{submission.permalink}}",
        'summary': summary,
        'timestamp': time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())
    })
    PROCESSED_ITEM_IDS.add(submission.id)
    return summary

def run_analysis_cycle(reddit_instance, gemini_model, post_limit=15):
    logger.info(f"--- Starting new analysis cycle at {{time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())}} ---")

    posts = get_wallstreetbets_posts(reddit_instance, limit=post_limit)

    if not posts:
        logger.warning("No posts fetched in this cycle.")
        return

    new_analyses_count = 0
    for i, post in enumerate(posts):
        if post.id not in PROCESSED_ITEM_IDS:
            if i > 0:
                logger.debug("Rate limit mitigation: Sleeping for 6 seconds before next Gemini API call.")
                time.sleep(6)

            result = process_single_submission(post, gemini_model)
            if result is not None:
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
    logger.info("Testing analysis module (summarization)...")
    try:
        # This test requires a valid Reddit and Gemini API key in the environment
        from .gemini_client import get_gemini_model
        reddit = get_reddit_instance()
        gemini = get_gemini_model()

        if reddit and gemini:
            run_analysis_cycle(reddit, gemini, post_limit=5)

            logger.info("--- Final Analyzed Data Store (Summaries): ---")
            for item in get_analyzed_data():
                logger.info(f"ID: {{item['source_id']}}, Title: {{item['source_title'][:60]}}..., Summary: {{item.get('summary')}}")
        else:
            logger.error("Failed to initialize Reddit or Gemini instances for testing.")

    except Exception as e:
        logger.error(f"An error occurred during analysis module test: {{e}}", exc_info=True)
