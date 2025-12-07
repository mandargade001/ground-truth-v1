# GroundTruth (RAG Application)

GroundTruth is a production-ready, Full-Stack Retrieval Augmented Generation (RAG) application built with **FastAPI**, **Next.js**, **LangChain**, and **ChromaDB**.

## 🚀 Key Features

*   **Intelligent RAG**: Re-ranking (FlashRank) and Semantic Caching for high precision and low latency.
*   **Knowledge Base**: Upload PDF, Docx, or MD files to chat with your data.
*   **Rich Chat**: Markdown support, Code Syntax Highlighting, and Source Citations.
*   **Scalable**: Containerized architecture with Async Workers (Celery).

## 🛠️ Project Structure

```
.
├── backend/            # FastAPI Application
│   ├── app/            # Source code (API, RAG, DB, Worker)
│   └── ...
├── frontend/           # Next.js Application
│   ├── components/     # React Components (Chat, KnowledgeBase)
│   └── ...
├── docker-compose.yml  # Infrastructure (DB, Redis, Chroma)
└── ...
```

## ⚡ Deployment & Setup

### Prerequisites
*   Docker & Docker Compose
*   Node.js 18+ (for local frontend dev)
*   OpenAI API Key

### Quick Start (Full Stack)

1.  **Configure Environment**:
    Create `.env` in the root (or `backend/`):
    ```bash
    # IMPORTANT: Ensure OPENAI_API_KEY is set in your .env
    cp .env.template .env
    ```

2.  **Start Application (Docker)**:
    This spins up Backend, Frontend support, DB, Redis, and ChromaDB.
    ```bash
    docker-compose up -d --build
    ```

3.  **Initialize Database**:
    Apply migrations and create a test user.
    ```bash
    # Apply Alembic Migrations
    docker-compose exec backend alembic upgrade head
    
    # Seed Test User
    docker-compose exec backend python create_test_user.py
    # Creates -> Email: test@example.com / Password: password123
    ```

4.  **Access the App**:
    *   **Frontend**: [http://localhost:3000](http://localhost:3000) (Login with `test@example.com` / `password123`)
    *   **Swagger UI**: [http://localhost:8000/docs](http://localhost:8000/docs)
    *   **Dashboard**: [http://localhost:3000/dashboard](http://localhost:3000/dashboard)

## 🧪 Testing

### Automated E2E Tests (Playwright)
We use Playwright to verify the critical path (Login -> Upload -> Chat).

1.  Ensure the stack is running (`docker-compose up`).
2.  Run the tests from the frontend directory:
    ```bash
    cd frontend
    npx playwright test
    ```

### Manual Verification Steps
1.  **Login**: Go to `http://localhost:3000`, login with `test@example.com`.
2.  **Upload**: Use the "Knowledge Base" sidebar to upload a PDF or TXT file.
3.  **Verify**: Wait for the "Indexed" status (approx 5-10s).
4.  **Chat**: Ask a question related to your document. Verify the answer includes citations.

## 📚 Documentation
For a deep dive into the architecture, tech stack, and data flows, please read [PROJECT_DOCUMENTATION.md](./PROJECT_DOCUMENTATION.md).
