# AI Agent Final Project

A full-stack, production-ready AI Chat Agent application. This project features a FastAPI backend, a React + Vite frontend, and uses Redis for memory persistence.

## Architecture
- **Backend:** Python + FastAPI. Handles API requests, communicates with the LLM (Large Language Model), and manages chat history state.
- **Frontend:** React + Vite. A modern, responsive user interface with glassmorphism design to interact with the AI agent. 
- **Database:** Redis. Provides stateless, high-speed memory persistence across chat sessions.

## Project Structure
```
Lab-Final-Project/
├── app/                  # FastAPI Backend source code
├── frontend/             # React/Vite Frontend source code
├── Dockerfile            # Container definition for the Backend
├── docker-compose.yml    # Local development orchestration (API + Redis)
├── requirements.txt      # Python dependencies
└── render.yaml           # Deployment blueprint for Render (IaC)
```

## Running Locally

### 1. Prerequisites
- Docker & Docker Compose
- Node.js & npm (for running the frontend locally)

### 2. Start the Backend & Redis
From the `Lab-Final-Project` directory, run:
```bash
docker-compose up --build
```
This will start:
- FastAPI Backend on `http://localhost:8000`
- Redis instance on port `6379`

### 3. Start the Frontend
Open a new terminal, navigate to the `frontend` folder, and start the development server:
```bash
cd frontend
npm install
npm run dev
```
The frontend UI will be accessible at `http://localhost:5173`.

## Deployment
For deployment instructions to cloud platforms like **Railway** or **Render**, please refer to the [deployments.md](./deployments.md) file.


## Public URL:
Use the chat at https://frontend-production-e8fd.up.railway.app/