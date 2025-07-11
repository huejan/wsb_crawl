import praw
import os
import logging # Import logging
# from dotenv import load_dotenv # Removed, should be loaded in main.py

# load_dotenv() # Removed

logger = logging.getLogger(__name__) # Get logger instance

def get_reddit_instance():
    """
    Initializes and returns a Reddit instance using credentials from environment variables.
    """
    client_id = os.getenv("REDDIT_CLIENT_ID")
    client_secret = os.getenv("REDDIT_CLIENT_SECRET")
    user_agent = os.getenv("REDDIT_USER_AGENT")
    username = os.getenv("REDDIT_USERNAME")
    password = os.getenv("REDDIT_PASSWORD")

    if not all([client_id, client_secret, user_agent]):
        # Log error and raise ValueError
        err_msg = "Missing Reddit API credentials in .env file (CLIENT_ID, CLIENT_SECRET, USER_AGENT)"
        logger.error(err_msg)
        raise ValueError(err_msg)

    try:
        reddit = praw.Reddit(
            client_id=client_id,
            client_secret=client_secret,
            user_agent=user_agent,
            username=username,
            password=password,
            # check_for_async=False # Add this if you encounter issues with async operations, though PRAW handles it mostly
        )
        logger.info("Reddit instance created successfully (PRAW object initialized).")

        # Add detailed logging about the PRAW instance state
        try:
            user_me = reddit.user.me()
            user_identity = str(user_me) if user_me else "None (app-only or unauthenticated user context)"
            logger.debug(f"PRAW instance check: read_only={reddit.read_only}, user.me()='{user_identity}'")
        except Exception as praw_check_exc:
            # This can happen if not authenticated or if .me() fails for other reasons
            logger.warning(f"PRAW instance check for user.me() failed: {praw_check_exc}", exc_info=True)
            logger.debug(f"PRAW instance check: read_only={reddit.read_only} (user.me() check failed)")

        return reddit
    except Exception as e:
        logger.error(f"Failed to create Reddit instance during praw.Reddit() call: {e}", exc_info=True)
        raise # Re-raise the exception after logging

def get_wallstreetbets_posts(reddit: praw.Reddit, limit: int = 25):
    """
    Fetches recent posts (hot) from r/wallstreetbets.

    Args:
        reddit: An initialized PRAW Reddit instance.
        limit: The maximum number of posts to fetch.

    Returns:
        A list of PRAW Submission objects.
    """
    subreddit_name = "wallstreetbets"
    try:
        subreddit = reddit.subreddit(subreddit_name)
        # Fetching 'hot' posts for now, could also be 'new', 'top', etc.
        # Consider fetching a mix or focusing on 'new' for timely analysis.
        posts = list(subreddit.hot(limit=limit))
        logger.info(f"Fetched {len(posts)} posts from r/{subreddit_name}")

        # Example: Print titles and get some comments
        # for post in posts:
        #     print(f"\nTitle: {post.title}")
        #     print(f"Score: {post.score}")
        #     print(f"ID: {post.id}")
        #     print(f"URL: {post.url}")
        #     post.comments.replace_more(limit=0) # Load top-level comments
        #     comment_count = 0
        #     for comment in post.comments.list()[:5]: # Limiting comments for now
        #         # print(f"  Comment: {comment.body[:100]}...") # Print first 100 chars
        #         comment_count +=1
        #     logger.debug(f"  Fetched {comment_count} sample comments for post {post.id}")
        return posts
    except Exception as e:
        logger.error(f"Error fetching posts from r/{subreddit_name}: {e}", exc_info=True)
        return []

if __name__ == "__main__":
    # This is for testing the reddit_client.py directly
    # Basic logging setup for direct execution testing
    logging.basicConfig(level=logging.DEBUG,
                        format='%(asctime)s %(levelname)s [%(name)s] %(message)s',
                        datefmt='%Y-%m-%d %H:%M:%S')
    logger.info("Testing Reddit client...")
    try:
        reddit = get_reddit_instance()
        if reddit:
            # Test read-only access
            logger.info(f"Read-only status: {reddit.read_only}")
            # Attempt to fetch posts
            example_posts = get_wallstreetbets_posts(reddit, 5)
            if example_posts:
                logger.info(f"Successfully fetched {len(example_posts)} example posts.")
                for i, post in enumerate(example_posts):
                    logger.info(f"Post {i+1}: {post.title[:100]}...")
            else:
                logger.warning("No posts fetched or an error occurred during test.")
    except ValueError as ve:
        logger.error(f"Configuration Error: {ve}")
    except Exception as e:
        logger.error(f"An unexpected error occurred during Reddit client test: {e}", exc_info=True)
