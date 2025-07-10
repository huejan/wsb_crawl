from .reddit_client import get_reddit_instance, get_wallstreetbets_posts
from .gemini_client import get_gemini_model, analyze_text_with_gemini
import time

# In-memory storage for analyzed data (for now)
# Structure: [{'symbol': 'GME', 'reason': 'Mooning', 'sentiment': 'positive', 'source_id': 'post_id_or_comment_id', 'timestamp': '...'}, ...]
ANALYZED_DATA_STORE = []
PROCESSED_ITEM_IDS = set() # To avoid re-processing posts/comments

def extract_relevant_text_from_post(post):
    """
    Extracts text from a PRAW post object, including title and selftext.
    For comments, it might involve iterating through them.
    """
    text_parts = [post.title]
    if post.selftext:
        text_parts.append(post.selftext)

    # Consider adding top comments for more context, but be mindful of API usage and token limits
    # post.comments.replace_more(limit=0) # load top-level comments
    # for comment in post.comments.list()[:5]: # Example: top 5 comments
    #     text_parts.append(comment.body)

    return "\n".join(text_parts)

def process_single_submission(submission, gemini_model):
    """
    Processes a single Reddit submission (post), analyzes it with Gemini,
    and stores the results.
    """
    if submission.id in PROCESSED_ITEM_IDS:
        print(f"Skipping already processed submission ID: {submission.id}")
        return None

    print(f"\nProcessing Reddit submission: {submission.title[:100]}... (ID: {submission.id})")
    text_to_analyze = extract_relevant_text_from_post(submission)

    if not text_to_analyze.strip():
        print(f"No text content found for submission ID: {submission.id}")
        PROCESSED_ITEM_IDS.add(submission.id)
        return None

    # Here, we might need to parse the Gemini response string into structured data.
    # The current `analyze_text_with_gemini` returns a string.
    # For a more robust system, we'd want Gemini to return JSON or a structured format.
    import json # Make sure json is imported

    analysis_json_str = analyze_text_with_gemini(gemini_model, text_to_analyze)

    try:
        # Attempt to parse the JSON response from Gemini
        parsed_analysis = json.loads(analysis_json_str)

        # Check if Gemini returned an error object (based on our gemini_client error format)
        if isinstance(parsed_analysis, dict) and "error" in parsed_analysis:
            print(f"Gemini analysis for {submission.id} returned an error: {parsed_analysis.get('details', parsed_analysis['error'])}")
            PROCESSED_ITEM_IDS.add(submission.id)
            return None

        # We expect a list of symbol objects, or an empty list
        if not isinstance(parsed_analysis, list):
            print(f"Unexpected data type from Gemini analysis for {submission.id}. Expected list, got {type(parsed_analysis)}. Content: {analysis_json_str[:200]}")
            PROCESSED_ITEM_IDS.add(submission.id)
            return None

        # If parsed_analysis is an empty list, it means no stocks were found, which is valid.
        print(f"Gemini Analysis for {submission.id} (parsed {len(parsed_analysis)} symbols):\n{parsed_analysis}")

        ANALYZED_DATA_STORE.append({
            'source_id': submission.id,
            'source_title': submission.title,
            'source_url': f"https://www.reddit.com{submission.permalink}",
            'analyzed_symbols': parsed_analysis, # Store the list of symbol objects
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())
        })
        PROCESSED_ITEM_IDS.add(submission.id)
        return parsed_analysis # Return the parsed data

    except json.JSONDecodeError as e:
        print(f"Failed to parse JSON analysis from Gemini for submission ID {submission.id}: {e}")
        print(f"Received string: {analysis_json_str[:500]}") # Log part of the problematic string
        PROCESSED_ITEM_IDS.add(submission.id) # Add to processed to avoid retrying unparseable items
        return None
    except Exception as e:
        print(f"An unexpected error occurred during processing of submission {submission.id}: {e}")
        PROCESSED_ITEM_IDS.add(submission.id)
        return None


def run_analysis_cycle(reddit_instance, gemini_model, post_limit=10):
    """
    Runs a full analysis cycle: fetches posts from Reddit, analyzes them with Gemini.
    """
    print(f"\n--- Starting new analysis cycle at {time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())} ---")

    # For now, only processing posts. Could extend to comments later.
    posts = get_wallstreetbets_posts(reddit_instance, limit=post_limit)

    if not posts:
        print("No posts fetched in this cycle.")
        return

    new_analyses_count = 0
    for post in posts:
        if post.id not in PROCESSED_ITEM_IDS:
            # Basic rate limiting / delay if making many API calls quickly
            # time.sleep(1) # Consider if Gemini has strict per-second limits
            result = process_single_submission(post, gemini_model)
            if result:
                new_analyses_count +=1
        else:
            print(f"Post {post.id} already processed. Skipping.")

    print(f"--- Analysis cycle complete. Processed {len(posts)} posts. Added {new_analyses_count} new analyses. ---")
    print(f"Total items in PROCESSED_ITEM_IDS: {len(PROCESSED_ITEM_IDS)}")
    print(f"Total items in ANALYZED_DATA_STORE: {len(ANALYZED_DATA_STORE)}")


def get_analyzed_data():
    """Returns the currently stored analyzed data."""
    return sorted(ANALYZED_DATA_STORE, key=lambda x: x['timestamp'], reverse=True)


if __name__ == "__main__":
    # This is for testing the analysis.py directly
    print("Testing analysis module...")
    try:
        reddit = get_reddit_instance()
        gemini = get_gemini_model()

        if reddit and gemini:
            # Run one cycle
            run_analysis_cycle(reddit, gemini, post_limit=5) # Fetch 5 posts for testing

            print("\n--- Current Analyzed Data Store (Structured): ---")
            for item in get_analyzed_data():
                print(f"ID: {item['source_id']}, Title: {item['source_title'][:60]}..., Symbols: {item.get('analyzed_symbols')}")

            # Run another cycle to test skipping already processed items
            print("\n--- Running second analysis cycle (should skip previous posts) ---")
            run_analysis_cycle(reddit, gemini, post_limit=5) # Fetch 5 posts again

            print("\n--- Final Analyzed Data Store (Structured): ---")
            for item in get_analyzed_data():
                print(f"ID: {item['source_id']}, Title: {item['source_title'][:60]}..., Symbols: {item.get('analyzed_symbols')}")

        else:
            print("Failed to initialize Reddit or Gemini instances for testing.")

    except Exception as e:
        print(f"An error occurred during analysis module test: {e}")
        import traceback
        traceback.print_exc()
