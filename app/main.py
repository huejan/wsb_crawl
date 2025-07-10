import os
import threading
# Load environment variables *before* other application imports that might need them
from dotenv import load_dotenv
load_dotenv()

import logging

# --- Basic Logging Setup ---
# Configure logging to output to stdout, which Docker logs will capture.
# Gunicorn will also handle this output.
logging.basicConfig(level=logging.DEBUG, # Set to DEBUG to capture all levels of logs
                    format='%(asctime)s %(levelname)s [%(name)s] [%(threadName)s] %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S')
logger = logging.getLogger(__name__)
# --- End Basic Logging Setup ---

logger.info("dotenv loaded in main.py")
try:
    import google.generativeai as genai # Test import
    logger.info("Successfully imported google.generativeai in main.py")
except ImportError as e:
    logger.critical(f"Failed to import google.generativeai in main.py: {e}", exc_info=True)
    raise
except Exception as e:
    logger.critical(f"Unexpected error importing google.generativeai in main.py: {e}", exc_info=True)
    raise


from flask import Flask, render_template, jsonify

# Import components from your application AFTER load_dotenv
from .analysis import get_analyzed_data, ANALYZED_DATA_STORE, PROCESSED_ITEM_IDS # analysis also uses print, might need update
from .scheduler import run_scheduler_in_thread, initialize_clients as initialize_scheduler_clients # scheduler uses print

app = Flask(__name__)

# --- Configuration ---
PORT = int(os.getenv("PORT", 8080))
EXPECTED_API_KEY = os.getenv("SIMPLE_API_KEY") # Optional: for securing management endpoints

# --- Helper Functions ---
def is_authenticated(request):
    """Simple API key authentication for sensitive endpoints."""
    if not EXPECTED_API_KEY: # No API key set, endpoint is open
        return True
    auth_header = request.headers.get("X-API-KEY")
    return auth_header == EXPECTED_API_KEY

# --- Web Routes ---
@app.route('/')
def index():
    """Serves the main page with analyzed stock data."""
    # Data is fetched by the analysis module and stored in ANALYZED_DATA_STORE
    # We will pass this data to the template.
    # The data format is currently a list of dicts, each with 'source_title', 'source_url', 'analysis_raw', 'timestamp'
    # This needs to be adapted if the structure of ANALYZED_DATA_STORE changes.

    # TODO: The 'analysis_raw' needs to be parsed or the Gemini prompt needs to be
    #       adjusted to return structured data (e.g., list of stocks with reasons/sentiments).
    #       For now, the template will just display the raw analysis.

    data_for_template = get_analyzed_data() # Gets a sorted list
    return render_template('index.html', analyzed_discussions=data_for_template)

@app.route('/health')
def health_check():
    """Health check endpoint."""
    return jsonify({"status": "ok", "message": "WSB Crawler is running"}), 200

@app.route('/status/data', methods=['GET'])
def get_current_data_json():
    """Returns the current analyzed data as JSON."""
    # if not is_authenticated(request):
    #     return jsonify({"error": "Unauthorized"}), 401
    return jsonify(get_analyzed_data())

@app.route('/status/counts', methods=['GET'])
def get_status_counts():
    """Returns counts of processed items and stored analyses."""
    # if not is_authenticated(request):
    #     return jsonify({"error": "Unauthorized"}), 401
    return jsonify({
        "processed_item_ids_count": len(PROCESSED_ITEM_IDS),
        "analyzed_data_store_count": len(ANALYZED_DATA_STORE)
    })


# --- Application Startup ---
# The run_server() function is not directly called when using Gunicorn.
# Gunicorn itself will serve the `app` instance.
# The `if __name__ == '__main__':` block is primarily for local development.

# Gunicorn will load this file as a module, so the code outside of functions/classes
# (like Flask app instantiation and client initialization for the scheduler)
# needs to be handled carefully. Gunicorn typically runs the `if __name__ == '__main__':`
# block in its main process before forking workers if using `--preload`.
# However, to ensure scheduler starts reliably with Gunicorn,
# it's often better to manage it slightly differently or ensure `--preload` is used if startup logic is complex.

# For now, the scheduler initialization logic below is mostly for when running `python -m app.main` directly.
# When Gunicorn runs `app.main:app`, it will create the `app` object.
# The scheduler thread needs to be started by the Gunicorn master process or a dedicated entrypoint
# if we want it to run alongside Gunicorn workers without `--preload` complexities.
# Let's simplify for now: the scheduler will start if this module is run directly.
# For Gunicorn, the scheduler will be started in each worker if not preloaded, which is not ideal.
# A better approach for Gunicorn might be to use a Gunicorn server hook (e.g. `on_starting`)
# or run the scheduler as a separate process/service.
# Given the current setup, the initial_scheduler_clients() and run_scheduler_in_thread()
# will be called when Gunicorn loads `app.main:app`. This means each worker might try to start its own scheduler thread.
# This is not ideal for resource usage but might work for basic functionality.
# A more robust Gunicorn setup would use `--preload` and ensure these are called once.

logger.info("Initializing application components...")
if not initialize_scheduler_clients():
    logger.critical("Failed to initialize clients for the scheduler. Background tasks may not run.")
else:
    scheduler_thread = run_scheduler_in_thread() # This will now run when Gunicorn loads the app
    if scheduler_thread:
        logger.info(f"Scheduler thread '{scheduler_thread.name}' started by Gunicorn worker or main process.")
    else:
        logger.error("Scheduler thread failed to start.")


if __name__ == '__main__':
    # This block is for running the Flask development server directly (e.g., python -m app.main)
    # It's not used by Gunicorn directly, Gunicorn uses the `app` instance.
    logger.info("Running Flask development server directly...")
    # Note: The scheduler thread is already started above when the module is loaded.
    # This is okay for local dev, but for Gunicorn, see notes above.
    app.run(host='0.0.0.0', port=PORT, debug=True, use_reloader=False) # use_reloader=False if scheduler runs in same process
    logger.info("Flask development server shutting down...")
