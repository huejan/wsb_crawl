# WallStreetBets Gemini Crawler

This project crawls the r/wallstreetbets subreddit, uses Google's Gemini 2.5 Flash to analyze discussions for stock and ETF mentions, and presents the findings via a simple web interface. The application is designed to be run as a Docker container.

## Features

-   Fetches recent posts from r/wallstreetbets using the Reddit API (via PRAW).
-   Utilizes Gemini 2.5 Flash for Natural Language Processing to:
    -   Identify discussed stock tickers and ETF symbols.
    -   Summarize the context of the discussion for each symbol.
    -   Attempt to determine sentiment.
-   Analysis tasks are scheduled to run periodically (default: every 2 hours).
-   The first analysis runs shortly after application startup.
-   Provides a simple web UI (Flask-based) to view the analyzed data.
-   Prevents re-processing of already analyzed Reddit posts.
-   Dockerized for easy setup and deployment using Gunicorn as the WSGI server.

## Project Structure

```
wallstreetbets_crawler/
├── app/                  # Main application source code
│   ├── __init__.py
│   ├── reddit_client.py  # Handles Reddit API interaction
│   ├── gemini_client.py  # Handles Gemini API interaction
│   ├── analysis.py       # Core logic for fetching, analyzing, and storing data
│   ├── scheduler.py      # Manages scheduled execution of analysis tasks
│   ├── main.py           # Flask web server and application entry point
│   └── templates/        # HTML templates for the web UI
│       └── index.html
├── tests/                # Placeholder for unit and integration tests
│   ├── __init__.py
│   └── test_placeholder.py
├── .env.example          # Example environment variable configuration file
├── Dockerfile            # Defines the Docker image
├── requirements.txt      # Python dependencies
└── README.md             # This file
```

## Setup and Configuration

1.  **Clone the Repository (if you haven't already):**
    ```bash
    # git clone <repository-url>
    # cd wallstreetbets_crawler
    ```

2.  **Configure Environment Variables:**
    *   Copy the example environment file:
        ```bash
        cp .env.example .env
        ```
    *   Edit the `.env` file with your actual credentials and desired settings. Refer to `.env.example` for all available options:
        ```dotenv
        # Reddit API Credentials (Mandatory)
        REDDIT_CLIENT_ID="YOUR_REDDIT_CLIENT_ID"
        REDDIT_CLIENT_SECRET="YOUR_REDDIT_CLIENT_SECRET"
        REDDIT_USER_AGENT="YOUR_REDDIT_USER_AGENT (e.g., WSBCrawler/0.1 by YourUsername)"
        REDDIT_USERNAME="YOUR_REDDIT_USERNAME" # Optional, but can be useful
        REDDIT_PASSWORD="YOUR_REDDIT_PASSWORD" # Optional

        # Gemini API Credentials (Mandatory)
        GEMINI_API_KEY="YOUR_GEMINI_API_KEY"

        # Scheduler Configuration
        CRAWL_INTERVAL_SECONDS=7200 # Default: 7200 (2 hours) - How often to fetch new data
        POST_LIMIT_PER_CYCLE=15     # Default: 15 - Max new posts to process each cycle

        # Web Server Configuration
        PORT=8080                   # Default: 8080 - Port the web server will listen on
        GUNICORN_WORKERS=2          # Default: 2 - Number of Gunicorn workers (for Docker)
        # SIMPLE_API_KEY=""         # Optional: For securing certain future management/data endpoints
        ```

## How to Run (Docker)

1.  **Build the Docker Image:**
    Ensure Docker is installed and running. From the project's root directory:
    ```bash
    docker build -t wsb-crawler .
    ```

2.  **Run the Docker Container:**
    ```bash
    docker run -d -p 8080:8080 --env-file .env --name wsb-crawler-app wsb-crawler
    ```
    *   `-d`: Run in detached mode (background).
    *   `-p 8080:8080`: Map port 8080 on your host to port 8080 in the container (or adjust if your `PORT` in `.env` is different).
    *   `--env-file .env`: Loads your configured environment variables from the `.env` file.
    *   `--name wsb-crawler-app`: Assigns a convenient name to the container.

3.  **Accessing the Application:**
    Once the container is running, open your web browser and navigate to:
    `http://localhost:8080`
    (If running on a remote server, replace `localhost` with the server's IP address).

    The application will perform an initial data fetch and analysis shortly after starting, so it might take a few minutes for the first results to appear. Subsequent analyses will occur based on the `CRAWL_INTERVAL_SECONDS`.

## Development (Local, without Docker)

1.  **Create a Python virtual environment:**
    ```bash
    python3 -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```
2.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
3.  **Set up your `.env` file** as described in "Setup and Configuration".
4.  **Run the application:**
    ```bash
    python -m app.main
    ```
    The application will be accessible at `http://localhost:PORT` (e.g., `http://localhost:8080`).

## Logs

*   **Docker:** To view logs from the Docker container:
    ```bash
    docker logs wsb-crawler-app
    docker logs -f wsb-crawler-app # To follow logs
    ```

## Running Tests (Basic)

This project includes a basic test setup using Python's `unittest` module.

1.  **Ensure you are in the project's root directory.**
2.  **If you created a virtual environment for local development, activate it.**
3.  **To discover and run all tests:**
    ```bash
    python -m unittest discover tests
    ```
4.  **To run tests from a specific file:**
    ```bash
    python tests/test_app_basic.py
    ```

## TODO / Future Enhancements

-   [ ] **Refine Gemini Prompts:** Iteratively improve the prompts sent to Gemini for more accurate and structured (e.g., JSON) output. This will allow for better parsing and display of stock-specific details (symbol, reason, sentiment).
-   [ ] **Improve Web UI/UX:**
    -   Display parsed, structured data instead of raw Gemini output.
    -   Add filtering or sorting options.
    -   Enhance visual presentation.
-   [ ] **Robust Error Handling & Logging:** Implement more comprehensive error handling (e.g., retries, specific exception catching) and structured logging throughout the application.
-   [ ] **Data Persistence:**
    -   Save `ANALYZED_DATA_STORE` and `PROCESSED_ITEM_IDS` to disk (e.g., JSON files) to persist data across application restarts.
    -   Consider a more robust database solution (e.g., SQLite, PostgreSQL) for larger datasets or more complex querying needs.
-   [ ] **Add Comprehensive Tests:** Develop unit and integration tests for various components (Reddit client, Gemini client, analysis logic, web endpoints).
-.  [ ] **Configuration for Subreddits:** Allow configuration of target subreddits beyond just r/wallstreetbets.
-   [ ] **Advanced Text Cleaning:** Implement more sophisticated cleaning of Reddit text before sending to Gemini.
-   [ ] **Security for Endpoints:** If adding management endpoints, secure them properly (e.g., using the `SIMPLE_API_KEY` or a more robust auth mechanism).

```
