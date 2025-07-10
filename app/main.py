import os
import threading
# Load environment variables *before* other application imports that might need them
from dotenv import load_dotenv
load_dotenv()

print("dotenv loaded in main.py") # Debug print
try:
    import google.generativeai as genai
    print("Successfully imported google.generativeai in main.py")
except ImportError as e:
    print(f"CRITICAL ERROR: Failed to import google.generativeai in main.py: {e}")
    # Optionally, re-raise or sys.exit to make failure more obvious if this is the root cause
    raise # This will definitely stop Gunicorn if the import fails here
except Exception as e:
    print(f"CRITICAL ERROR: Unexpected error importing google.generativeai in main.py: {e}")
    raise


from flask import Flask, render_template, jsonify

# Import components from your application AFTER load_dotenv
from .analysis import get_analyzed_data, ANALYZED_DATA_STORE, PROCESSED_ITEM_IDS
from .scheduler import run_scheduler_in_thread, initialize_clients as initialize_scheduler_clients

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
def run_server():
    """Runs the Flask development server."""
    # Flask's dev server is not recommended for production.
    # Use a production-ready WSGI server like Gunicorn or uWSGI behind a reverse proxy (Nginx).
    # For Docker, Gunicorn is a common choice.
    print(f"Flask server starting on http://0.0.0.0:{PORT}")
    app.run(host='0.0.0.0', port=PORT, debug=False) # debug=False for production/docker

if __name__ == '__main__':
    print("Initializing application...")

    # Initialize Reddit/Gemini clients for the scheduler
    # This ensures they are ready before the first scheduled job runs.
    # The scheduler itself will also try to initialize if they are not set.
    if not initialize_scheduler_clients():
        print("CRITICAL: Failed to initialize clients for the scheduler. Background tasks may not run.")
        # Decide if the app should exit or continue with web server only
        # For now, it will continue, but scheduler won't work.
    else:
        # Start the background scheduler
        scheduler_thread = run_scheduler_in_thread()
        print(f"Scheduler thread started: {scheduler_thread.name}")

    # Start the Flask web server
    # This will block the main thread. The scheduler runs in a background thread.
    run_server()

    # Note: If run_server() is blocking, code here won't be reached until server stops.
    print("Application shutting down...")
