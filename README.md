# SERA — Securities Engine for Regulatory Action

SERA is an AI-powered regulatory compliance platform designed to help organizations analyze regulations, track obligations, manage implementation plans, and monitor compliance activities through an intuitive web interface. 

It solves the complex regulatory compliance problem by automatically monitoring regulatory bodies (like SEBI), fetching new circulars, and leveraging AI to convert dense regulatory text into actionable compliance information. The frontend dashboard visualizes these results, allowing compliance teams to easily track obligations, map impacts, and orchestrate their implementation plans.

## System Architecture

The system is structured as a multi-stage processing pipeline. Below is the current state of the architecture. Stages that are fully implemented process the data, while others are currently mocked in the pipeline orchestrator pending future AI integration.

* **Regulatory Fetching**: **(Implemented)** Scrapes the latest circulars from SEBI's website and downloads the associated PDF documents.
* **Ingestion**: **(Implemented)** Processes the downloaded PDFs, extracts text layout, headings, numbering, and clauses, and structures them into a clean JSON format via a multi-module pipeline.
* **LLM Extraction**: *(Future Work)* Will extract key entities and requirements using AI providers. Currently mocked in the orchestrator.
* **Obligation Agent**: *(Future Work)* Will identify and categorize specific compliance obligations. Currently mocked in the orchestrator.
* **Applicability Agent**: *(Future Work)* Will determine which obligations apply specifically to the organization. Currently mocked in the orchestrator.
* **Ambiguity Solver**: *(Future Work)* Will identify ambiguous clauses requiring human review or legal interpretation. Currently mocked in the orchestrator.
* **Task Generation Agent**: *(Future Work)* Will automatically generate actionable tasks based on the identified obligations. Currently mocked in the orchestrator.
* **Frontend Dashboard**: **(Implemented)** A React-based web interface to monitor pipeline jobs in real-time, view extracted obligations, and manage compliance tasks.

## Project Structure

```text
.
├── backend/               # FastAPI backend application
│   ├── app/
│   │   ├── agents/        # Agent directories (Obligation, Applicability, etc. - Future Work)
│   │   ├── core/          # Configuration (Pydantic settings) and logging
│   │   ├── ingestion/     # PDF processing and structuring modules
│   │   ├── pipeline/      # Pipeline orchestration and mocked runner
│   │   └── scraper/       # SEBI regulatory scraping tools (Playwright)
│   ├── data/              # Local JSON data stores (documents, change reports)
│   └── downloads/         # Downloaded regulatory PDFs
└── frontend/              # React frontend application
    ├── public/            # Static assets
    └── src/               # React components, routes, and API hooks
```

## Prerequisites

* **Python**: 3.12 (Requires Python 3.12 due to native dependencies. Do NOT use Python 3.13 as it encounters native dependency problems).
* **Environment**: Conda or standard Python `venv`
* **Node.js**: v18 or higher
* **npm**: v9 or higher
* **Database**: None required currently. (Data is stored in local JSON files; Alembic is initialized but no PostgreSQL configuration is currently required).

## Backend Setup

Follow these steps to configure and run the backend from a fresh clone:

```powershell
# 1. Navigate to the backend directory
cd backend

# 2. Create a virtual environment with Python 3.12
# (Using Conda as an example, but standard venv works too)
conda create -n sera python=3.12 -y

# 3. Activate the environment
conda activate sera

# 4. Install backend dependencies
pip install -r requirements.txt

# 5. Install Playwright browsers (required for the SEBI scraper)
playwright install

# 6. Start the backend server (runs on port 8000)
python -m app.main
```
*(The backend will start at `http://0.0.0.0:8000`. API requests from the frontend are proxied here).*

## Frontend Setup

Follow these steps to configure and run the frontend dashboard:

```powershell
# 1. Navigate to the frontend directory
cd frontend

# 2. Install Node dependencies
npm install

# 3. Start the frontend development server (runs on port 5173)
npm run dev
```
*(The frontend uses Vite to automatically proxy API requests starting with `/api` to the backend running at `http://127.0.0.1:8000`).*
