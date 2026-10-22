# PharmaTrace

**Pharmaceutical supply chain traceability and risk intelligence, powered by Neo4j.**

PharmaTrace tracks medicine batches from manufacturer to pharmacy, visualizes supply-chain relationships as an interactive graph, flags suspicious routes and records, and analyzes the impact of product recalls. It is a university DBMS case study built with a FastAPI backend and a React frontend.

**Live demo:** https://pharma-trace-six.vercel.app

> **Note:** All data is synthetic. Organizations, medicines, batches, and anomalies are fictional and intended for demonstration only.

## Features

- **Graph Explorer** — Search nodes, expand neighbours, and find shortest paths.
- **Batch Traceability** — Follow a batch's journey and download a traceability report.
- **Risk Intelligence** — Rule-based findings for duplicate lots, unverified suppliers, unexpected routes, expired batches, quantity mismatches, missing events, and incomplete paths.
- **Recall Analysis** — Identify affected batches, pharmacies, and delivered units.
- **Database Lab** — Run 24 allowlisted Cypher templates, including `EXPLAIN` and `PROFILE`.
- **Database Insights** — Explore database counts, indexes, constraints, and query plans.
- **Dark and light themes** — Switch the interface to your preferred theme.

## Tech Stack

| Layer | Technologies |
|---|---|
| Database | Neo4j 5 |
| Backend | Python, FastAPI, Neo4j Python driver |
| Frontend | React, TypeScript, Vite, Tailwind CSS, Cytoscape.js |
| Deployment configuration | Vercel (frontend), Render (API), Neo4j Aura (database) |

## Architecture

![PharmaTrace architecture](docs/images/architecture.svg)

## Getting Started

### Prerequisites

- Python 3.11 or newer
- Node.js 20 or newer
- A running Neo4j 5 database (Neo4j Desktop or Neo4j Aura)

### 1. Clone the repository

```bash
git clone https://github.com/SholingaramRithika/PharmaTrace.git
cd PharmaTrace
```

### 2. Configure Neo4j

Create a **root-level** `.env` file in the project directory with your Neo4j connection details:

```env
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your-password
```

Use the URI and credentials provided by your Neo4j instance if you use Neo4j Aura. Never commit your real credentials.

### 3. Install dependencies and load the database

Run these commands from the **project root**:

```bash
python -m venv backend/.venv
source backend/.venv/bin/activate
# Windows PowerShell: .\backend\.venv\Scripts\Activate.ps1

pip install -r backend/requirements.txt
python database/setup_db.py all
```

Keep this terminal at the project root for database setup. Then start the backend in the same environment:

```bash
cd backend
python -m uvicorn app.main:app --reload --port 8000
```

The API documentation is available at http://localhost:8000/docs.

### 4. Configure and start the frontend

Open a **new terminal** from the project root:

```bash
cd frontend
```

Create `frontend/.env` with the following value (or copy `frontend/.env.example` if it contains the same setting):

```env
VITE_API_URL=http://localhost:8000
```

Then install dependencies and start the development server:

```bash
npm install
npm run dev
```

Open http://localhost:5173.

## Project Structure

```text
PharmaTrace/
├── backend/       # FastAPI application, routers, services, tests
├── database/      # Neo4j schema, data generator, setup script, Cypher catalogue
├── frontend/      # React application, pages, components, theme
├── docs/          # Setup, architecture, schema, security, and demo documentation
├── tests/         # End-to-end smoke tests
└── render.yaml    # Render deployment blueprint
```

## Tests

Run backend tests from the project root with the virtual environment activated:

```bash
cd backend
python -m pytest -q
```

Run frontend tests in a separate terminal:

```bash
cd frontend
npm test
```

Previously reported project checks include 106 backend offline tests and 28 frontend tests. Live Neo4j tests and real-browser visual verification may require additional setup; rerun the tests on your current checkout to confirm their status.

## Documentation

See [`docs/`](docs/) for detailed setup instructions, architecture, graph schema, deployment, security notes, testing, and the demo guide.

## Scope and Limitations

PharmaTrace is an academic demonstration built with fictional data and simulated anomalies. It is not a production pharmaceutical tracking system and is not intended for regulatory or clinical decision-making.
