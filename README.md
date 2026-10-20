# Travel Concierge Agent

An intelligent, cross-session travel exploration and planning concierge built with Google's Agent Development Kit (ADK) and deployed with `agents-cli`.

![Travel Concierge Demo](demo.gif)

---

## Overview

The **Travel Concierge** helps travelers discover destinations, explore curated culinary highlights, plan customized itineraries, and calculate travel budgets. It integrates cross-session memory with persistence across conversations, database storage, secure sandboxed execution, and interactive rich UI components.

---

## Implemented Capabilities & Architecture

Based directly on the codebase in `app/` and `agents-cli-manifest.yaml`, the following services and tools are implemented:

### 1. Vertex AI Memory Bank (Agent Platform)
- **Tool**: `PreloadMemoryTool`
- **Callback**: `generate_memories_callback` (invokes `callback_context.add_session_to_memory()` after each agent turn)
- **Integration**: Backed by a managed Vertex AI Memory Bank instance (`VertexAiMemoryBankService`), retaining user preferences, travel styles, and past conversation context across sessions.
- **Specialized Topic**: Configured custom topic for **allergies and dietary restrictions**, ensuring food restrictions (e.g., seafood, gluten, peanuts) are persistently remembered and respected across conversations.

### 2. Cloud Firestore Database
- **Catalog Management**:
  - `list_destinations`: Streams and filters curated destinations by travel style and budget.
  - `get_destination_details`: Fetches complete destination data, cultural notes, culinary specialties, and seasonal tips.
  - `add_destination`: Allows adding new destination entries to the `destinations` Firestore collection.
- **Itinerary Storage**:
  - `save_trip_itinerary`: Generates and writes customized day-by-day travel itineraries into the `itineraries` Firestore collection.

### 3. Agent Engine Code Execution Sandbox
- **Executor**: `AgentEngineSandboxCodeExecutor`
- **Capability**: Safely executes Python code in a remote cloud container sandbox for budget calculations, multi-day expense modeling, currency conversions, and financial breakdowns.

### 4. Real-Time Tools
- **Live Weather API**: `get_live_destination_weather` calls the Open-Meteo REST API for coordinates, weather condition codes, temperatures, humidity, wind speeds, and tailored packing tips.
- **Local Time Lookup**: `get_current_time` computes current local time and timezones across international destinations using Python `zoneinfo`.

### 5. A2UI (Agent-to-User Interface v0.8)
- **Schema & Prompting**: Structured system instruction via `A2uiSchemaManager` (version 0.8) and `BasicCatalog`.
- **Callback**: `after_model_callback=a2ui_callback` converts A2UI JSON payloads into `application/json+a2ui` data parts.
- **Renderer**: Supported by both the ADK development web UI and the custom FastAPI chat frontend.

---

## Planned / Not Implemented Capabilities

The following features were outlined in the design brief but are **planned / not yet wired into the agent's toolset**:
- **Vertex AI Image Generation (Imagen)**: Generating and storing destination scene images via tools (*planned, not yet implemented*).
- **Public Cloud Storage Bucket Hosting**: Direct tool integration for uploading and returning media URLs (*bucket created, tool integration planned*).

---

## Project Structure

```
travel-concierge/
├── app/
│   ├── agent.py               # Root agent definition, system prompts, callbacks, and function tools
│   ├── a2ui_utils.py          # A2UI response post-processing callback
│   ├── fast_api_app.py        # ADK FastAPI backend server
│   └── app_utils/             # Memory service registry, A2A routes, and reasoning engine adapters
├── frontend/                  # Minimal FastAPI A2A proxy and chat interface
│   ├── main.py                # A2A proxy routing requests to Agent Runtime
│   ├── requirements.txt       # Frontend dependencies
│   └── static/                # Single-page chat UI with native A2UI card renderer
├── demo.gif                   # Looping demo recording of the agent in action
├── demo_video.mp4             # High-definition demo recording with lo-fi soundtrack
├── agents-cli-manifest.yaml   # Deployment manifest
└── pyproject.toml             # Python dependencies and project metadata
```

---

## Running Locally

### 1. Prerequisites
- Python 3.11+
- [uv](https://docs.astral.sh/uv/) package manager
- Google Cloud SDK (`gcloud`) authenticated with Application Default Credentials:
  ```bash
  gcloud auth login
  gcloud auth application-default login
  gcloud config set project <your-project-id>
  ```

### 2. Install Dependencies
```bash
uv sync
```

### 3. Run the ADK Development Playground
To run the ADK web interface with memory service connected:
```bash
uv run adk web . --port 8080 --reload_agents --memory_service_uri=agentengine://<YOUR_AGENT_ENGINE_ID>
```

### 4. Run the Chat Frontend Locally
To test with the dedicated web chat UI:
```bash
cd frontend
uv pip install -r requirements.txt
export AGENT_ENGINE_RESOURCE_NAME="projects/<PROJECT_NUM>/locations/<REGION>/reasoningEngines/<ENGINE_ID>"
export AGENT_DIRECTORY="app"
python main.py
```
