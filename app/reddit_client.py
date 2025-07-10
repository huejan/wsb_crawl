import praw
import os
# from dotenv import load_dotenv # Removed, should be loaded in main.py

# load_dotenv() # Removed

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
        raise ValueError("Missing Reddit API credentials in .env file (CLIENT_ID, CLIENT_SECRET, USER_AGENT)")

    reddit = praw.Reddit(
        client_id=client_id,
        client_secret=client_secret,
        user_agent=user_agent,
        username=username,
        password=password,
        # check_for_async=False # Add this if you encounter issues with async operations, though PRAW handles it mostly
    )
    print("Reddit instance created successfully.")
    return reddit

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
        print(f"Fetched {len(posts)} posts from r/{subreddit_name}")

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
        #     print(f"  Fetched {comment_count} sample comments for post {post.id}")
        return posts
    except Exception as e:
        print(f"Error fetching posts from r/{subreddit_name}: {e}")
        return []

if __name__ == "__main__":
    # This is for testing the reddit_client.py directly
    print("Testing Reddit client...")
    try:
        reddit = get_reddit_instance()
        if reddit:
            # Test read-only access
            print(f"Read-only status: {reddit.read_only}")
            # Attempt to fetch posts
            example_posts = get_wallstreetbets_posts(reddit, 5)
            if example_posts:
                print(f"\nSuccessfully fetched {len(example_posts)} example posts.")
                for i, post in enumerate(example_posts):
                    print(f"Post {i+1}: {post.title[:100]}...")
            else:
                print("No posts fetched or an error occurred.")
    except ValueError as ve:
        print(f"Configuration Error: {ve}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
