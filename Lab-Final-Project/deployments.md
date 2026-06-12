# Deployment Guide

This document outlines how to deploy the AI Agent Final Project to cloud platforms. The application consists of three main components:
1. **Redis Database:** For session memory persistence.
2. **Backend API (FastAPI):** Docker containerized service.
3. **Frontend UI (React/Vite):** Static site generation.

---

## 🚂 Option 1: Deploying on Railway (Recommended)

Railway is highly recommended for its ease of use, fast builds, and excellent monorepo support.

### 1. Setup Github
Ensure your entire project is pushed to a GitHub repository.

### 2. Provision Redis
1. Log in to [Railway](https://railway.app/).
2. Click **New Project** -> **Provision PostgreSQL, Redis, etc.** -> **Add Redis**.

### 3. Deploy the Backend
1. In your Railway project, click **New** -> **GitHub Repo** and select your repository.
2. Go to the new service's **Settings** tab.
3. Scroll down to **Root Directory** and enter: `/Lab-Final-Project`.
   *(Railway will automatically detect the `Dockerfile` here and build it).*
4. Go to the **Variables** tab and add:
   - `AGENT_API_KEY`: A secure random string (e.g., `my-super-secret-key-123`).
   - `REDIS_URL`: `${{ Redis.REDIS_URL }}` *(This auto-links to the Redis service).*
5. Go back to **Settings**, under Networking, click **Generate Domain**.

### 4. Deploy the Frontend
1. Click **New** -> **GitHub Repo** again and select the exact same repository.
2. Go to the **Settings** tab for this newly created service.
3. Scroll down to **Root Directory** and enter: `/Lab-Final-Project/frontend`.
4. Go to the **Variables** tab and add:
   - `VITE_API_URL`: The public domain URL generated for your Backend in Step 3.
   - `VITE_AGENT_API_KEY`: The exact same secret key you set in the Backend.
5. Go to **Settings**, under Networking, click **Generate Domain**.

Your Frontend will automatically build using `npm run build` and start using `serve -s dist`. Once the domain is ready, click it to chat!

---

## ☁️ Option 2: Deploying on Render

Render uses the provided `render.yaml` Blueprint file for Infrastructure as Code (IaC).

1. Push your code to GitHub.
2. Log in to [Render](https://render.com/).
3. Click **New** -> **Blueprint**.
4. Connect your GitHub repository.
5. Render will automatically read the `render.yaml` file located in the `Lab-Final-Project` folder.
   *(Note: If your `render.yaml` is not in the repository root, you may need to configure Render's Blueprint search path or recreate the services manually).*
6. The Blueprint will automatically provision:
   - A Managed Redis instance.
   - A Web Service for the FastAPI Backend.
   - A Static Site for the React Frontend.
7. Make sure to provide the `VITE_API_URL` and `VITE_AGENT_API_KEY` environment variables to the Frontend service in the Render Dashboard so it can successfully communicate with the Backend.
