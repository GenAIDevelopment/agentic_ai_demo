# LangChain SQL Agent for Retail Data Analysis

This project demonstrates how to use a Large Language Model (LLM) as an intelligent agent to query a SQL database using natural language. The agent can understand questions, write and execute SQL queries, and return the results in a user-friendly format, including CSV files and plots.

The repository contains two main components:
1.  `fake_data_generator.py`: A script to create a realistic SQLite database (`lt_walmart_data.db`) containing mock retail data (sales, products, inventory, etc.).
2.  `agent_with_sql.py`: A script that runs a LangChain SQL agent which connects to the generated database to answer questions.

## Features

- **Natural Language to SQL**: Ask complex questions about your data in plain English.
- **Data Generation**: Quickly bootstrap a sample database with realistic, interconnected data.
- **CSV Export**: Automatically saves query results with headers into a CSV file (`outputs/result.csv`).
- **Automatic Charting**: Generates a plot (`outputs/chart.png`) for time-series or categorical data.

## Prerequisites

- Python 3.10+
- A Google Cloud Project with the **Vertex AI API** enabled.
- The `gcloud` CLI installed and authenticated on your local machine.

## Setup & Installation

1.  **Clone the Repository**
    ```bash
    # git clone <repository_url>
    cd agentic_ai_demo
    ```

2.  **Set Up Environment and Install Dependencies**

    We recommend using **`uv`**, an extremely fast Python package installer.

    **Option A: Using `uv` (Recommended)**

    First, install `uv` if you don't have it:
    ```bash
    # On macOS / Linux
    curl -LsSf https://astral.sh/uv/install.sh | sh
    # On Windows
    powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
    ```

    Then, create the virtual environment (it will be named `.venv`) and install the dependencies:
    ```bash
    uv venv
    source .venv/bin/activate # On Windows, use: .venv\Scripts\activate
    uv pip install -r requirements.txt
    ```

    **Option B: Using `venv` and `pip`**

    If you prefer to use Python's built-in tools:
    ```bash
    python -m venv venv
    source venv/bin/activate
    # On Windows, use: venv\Scripts\activate
    pip install -r requirements.txt
    ```

3.  **Authenticate with Google Cloud**
    Log in with your Google account to allow the application to use the Vertex AI services.
    ```bash
    gcloud auth application-default login
    ```

## How to Use

### Step 1: Generate the Database

First, run the data generator script. This will create a `data/` directory and place the SQLite database file (`lt_walmart_data.db`) inside it.

```bash
python fake_data_generator.py
```

You will see output indicating the progress of data generation for each table. This only needs to be done once.

### Step 2: Query the Data with the Agent

Now you can ask the agent questions about the data. Run the `agent_with_sql.py` script and pass your question as a command-line argument.

If you don't provide a question, it will use a default example: *"Show revenue trend for the last 30 days"*.

```bash
python agent_with_sql.py "Your question in quotes"
```

**Example:**

```bash
python agent_with_sql.py "What are the top 5 best-selling products by total revenue?"
```

The agent will then:
1.  Think about the question and construct a SQL query.
2.  Execute the query against the `lt_walmart_data.db` database.
3.  Parse the results.
4.  Save the data to `outputs/result.csv`.
5.  If applicable, create a chart and save it to `outputs/chart.png`.
6.  Print a summary message to the console.

### Example Questions to Try

- "Which 5 stores have the highest total revenue?"
- "Show me the daily sales revenue for the last 14 days."
- "What are the top 10 products with the lowest stock levels across all stores?"
- "Which store location has the most negative feedback comments?"
