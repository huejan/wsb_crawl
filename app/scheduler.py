import schedule
import time
import threading
import os
# from dotenv import load_dotenv # Removed, should be loaded in main.py

from .reddit_client import get_reddit_instance
from .gemini_client import get_gemini_model
from .analysis import run_analysis_cycle

load_dotenv()

# Global instances for Reddit and Gemini to avoid re-initializing every time
# This is okay for a single-threaded scheduler. If using multi-threading
# for scheduled jobs, ensure these clients are thread-safe or initialized per thread.
# PRAW instances are generally not thread-safe if multiple threads use the same instance
# for calls that modify its state. For read-only operations, it might be fine.
# Gemini client should be okay.

REDDIT_INSTANCE = None
GEMINI_MODEL = None

def initialize_clients():
    """Initializes and stores global Reddit and Gemini clients."""
    global REDDIT_INSTANCE, GEMINI_MODEL
    try:
        if REDDIT_INSTANCE is None:
            REDDIT_INSTANCE = get_reddit_instance()
        if GEMINI_MODEL is None:
            GEMINI_MODEL = get_gemini_model()

        if REDDIT_INSTANCE and GEMINI_MODEL:
            print("Scheduler: Reddit and Gemini clients initialized successfully.")
            return True
        else:
            print("Scheduler: Failed to initialize one or both clients.")
            return False
    except Exception as e:
        print(f"Scheduler: Error during client initialization: {e}")
        return False


def scheduled_task():
    """
    The task that will be run by the scheduler.
    Initializes clients if not already done, then runs an analysis cycle.
    """
    print(f"\nScheduler: Running scheduled task at {time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())}")
    if REDDIT_INSTANCE is None or GEMINI_MODEL is None:
        print("Scheduler: Clients not initialized. Attempting to initialize...")
        if not initialize_clients():
            print("Scheduler: Halting task due to client initialization failure.")
            return

    try:
        # Define how many posts to fetch per cycle from .env or default
        post_limit_per_cycle = int(os.getenv("POST_LIMIT_PER_CYCLE", 15)) # Default to 15 if not set
        run_analysis_cycle(REDDIT_INSTANCE, GEMINI_MODEL, post_limit=post_limit_per_cycle)
    except Exception as e:
        print(f"Scheduler: Error during scheduled_task execution: {e}")
        # Potentially, re-initialize clients if the error seems related to their state
        # global REDDIT_INSTANCE, GEMINI_MODEL
        # REDDIT_INSTANCE = None
        # GEMINI_MODEL = None


def start_scheduler():
    """
    Configures and starts the job scheduler.
    This function will block and run the scheduler continuously.
    """
    if not initialize_clients():
        print("Scheduler: Could not initialize clients. Scheduler will not start.")
        return

    crawl_interval = int(os.getenv("CRAWL_INTERVAL_SECONDS", 7200)) # Default to 2 hours
    print(f"Scheduler: Scheduling analysis task to run every {crawl_interval} seconds.")

    # Run the task once immediately at startup
    print("Scheduler: Running initial analysis task...")
    scheduled_task()

    # Then schedule it for repeated execution
    schedule.every(crawl_interval).seconds.do(scheduled_task)

    print("Scheduler: Starting scheduler loop. Press Ctrl+C to exit.")
    while True:
        schedule.run_pending()
        time.sleep(1)

def run_scheduler_in_thread():
    """
    Starts the scheduler in a separate daemon thread.
    This is useful if the main thread needs to do other things (e.g., run a web server).
    """
    scheduler_thread = threading.Thread(target=start_scheduler, daemon=True)
    scheduler_thread.start()
    print("Scheduler: Background task scheduler started in a separate thread.")
    return scheduler_thread


if __name__ == "__main__":
    # This is for testing the scheduler.py directly
    # It will run indefinitely until Ctrl+C is pressed.
    print("Testing scheduler module (will run indefinitely)...")
    # Ensure .env file is present with credentials for this test to work

    # For testing, maybe a shorter interval:
    # os.environ['CRAWL_INTERVAL_SECONDS'] = '30' # Run every 30 seconds for test
    # os.environ['POST_LIMIT_PER_CYCLE'] = '3'    # Fetch 3 posts for test

    start_scheduler()
    # If you want to run it in a thread and do something else:
    # thread = run_scheduler_in_thread()
    # print("Main thread can do other things now or just wait.")
    # thread.join() # Wait for the scheduler thread to finish (it won't, as it's a loop)
    # print("Scheduler test finished (if thread.join() was used and thread exited).")
