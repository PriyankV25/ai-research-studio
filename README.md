# Atlas — AI Research Studio

A polished HTML/CSS/JavaScript frontend for the existing multi-agent research pipeline. The UI talks to a small Flask API, which runs the existing Python agents in the background and exposes live stage/status updates.

## What it does

- Responsive research workspace with animated, accessible UI.
- Starts a research job from a topic prompt.
- Shows the four pipeline stages: web search, source reading, report writing, and critic review.
- Displays the Markdown report and critic feedback when complete.
- Copy report and export the report as Markdown.
- Shows local environment configuration status without exposing API keys.

## Setup (Windows PowerShell)

Use Python 3.12 or another Python version supported by your project's dependencies. Open PowerShell in this folder:

```powershell
uv venv
.venv\Scripts\Activate.ps1
uv pip install -r requirements.txt
```

Create a `.env` file in the project root (do not commit it):

```env
GROQ_API_KEY=your_groq_api_key
TAVILY_API_KEY=your_tavily_api_key
```

Then run:

```powershell
python app.py
```

Open http://127.0.0.1:5000 in your browser.

## Important notes

- The `.env` file and `.venv` are intentionally not included in this package. Keep your keys private.
- This is intended for local development. Do not expose the Flask development server directly to the public internet.
- The status API reports the stage that the existing pipeline has reached; it does not stream token-by-token output.
- Source websites may block scraping or return limited content. The report is AI-generated and should be fact-checked before being used for high-stakes decisions.
- The UI uses Google Fonts and CDN-hosted Marked/DOMPurify. The interface still loads without those libraries, but Markdown rendering will be more basic if the CDN is unavailable.


## Deploy to Render

1. Push this folder to a GitHub repository. Do not commit `.env`, API keys, or `.venv`.
2. In Render, choose **New + → Blueprint** and select the repository containing `render.yaml`, or create a **Web Service** manually.
3. For a manual Web Service, use:
   - Runtime: Python
   - Build command: `pip install -r requirements.txt`
   - Start command: `gunicorn app:app --workers 1 --threads 8 --timeout 180`
4. Add `GROQ_API_KEY` and `TAVILY_API_KEY` under the Render service's Environment settings. Keep `LLM_PROVIDER=groq` for the hosted app.
5. Deploy and check `/api/health` on your deployed URL.

### Provider options

- Local users can set `LLM_PROVIDER=ollama`, install Ollama, pull a model, and use `OLLAMA_BASE_URL=http://localhost:11434`.
- A Render-hosted service cannot access Ollama running on a visitor's own computer via `localhost`. For Ollama on a hosted deployment, configure an Ollama endpoint that is securely reachable from Render.
- Keep credentials in Render Environment settings and never commit `.env`.

The Flask job state is stored in memory and can be lost on restarts or redeploys. This starter uses one Gunicorn worker to avoid splitting in-memory job state across worker processes. For a production multi-worker setup, move job state to a shared store and use a background job queue.
