# GroundTruth - Advanced RAG Application Documentation

## 1. Overview
**GroundTruth** is a scalable, production-ready Retrieval-Augmented Generation (RAG) application. It allows users to upload documents to build a personalized knowledge base and interact with it using an intelligent AI Assistant. The system features advanced RAG capabilities including **Semantic Caching**, **Re-ranking**, **Source Citations**, and **Streaming Responses**.

## 2. Technology Stack

### Frontend
*   **Framework**: [Next.js 14](https://nextjs.org/) (App Router)
*   **Language**: TypeScript
*   **Styling**: TailwindCSS, Shadcn/UI
*   **State Management**: Zustand, React Query (TanStack Query)
*   **HTTP Client**: Axios (with Interceptors)
*   **Markdown Rendering**: `react-markdown`, `prism-react-renderer`, `remark-gfm`

### Backend
*   **Framework**: [FastAPI](https://fastapi.tiangolo.com/) (Python 3.11+)
*   **Database (Relational)**: PostgreSQL 15 (Async `asyncpg`)
*   **Database (Vector)**: ChromaDB (Client-Server Mode)
*   **Task Queue**: Celery (with Redis Broker)
*   **LLM Integration**: LangChain, OpenAI (`gpt-4o`, `text-embedding-3-small`)
*   **Re-ranking**: FlashRank (`ms-marco-MiniLM-L-12-v2`)

### Infrastructure
*   **Containerization**: Docker & Docker Compose
*   **Cache**: Redis (Task Broker) & ChromaDB (Semantic Cache)

## 3. Core Features

### 🧠 Advanced RAG Pipeline
1.  **Ingestion**: Supports PDF, DOCX, TXT, and Markdown. Documents are chunked (RecursiveCharacterTextSplitter) and embedded.
2.  **Hybrid Retrieval**: Features a multi-stage retrieval process.
    *   **Phase 1**: Semantic Search (Top 20 docs).
    *   **Phase 2**: Re-ranking using FlashRank to select the most relevant Top 5.
3.  **Source Citations**: Every answer includes links to the specific source documents used.

### ⚡ Performance Optimization
*   **Semantic Caching**: Implements a "Cache-First" strategy.
    *   Incoming questions are embedded and compared against a `semantic_cache` collection in ChromaDB.
    *   If a similar question (>90% similarity) exists, the cached answer is returned instantly (<100ms), bypassing the costly LLM call.

### 💻 Modern Chat Interface
*   **Rich Text**: Full Markdown support including tables, lists, and syntax-highlighted code blocks.
*   **Streaming**: Real-time token streaming using Server-Sent Events (SSE).
*   **Sessions**: Persistent chat history with a responsive Sidebar.

## 4. Architecture & Flows

### Document Ingestion Flow
1.  **Upload**: User uploads file via Frontend -> `POST /documents/upload`.
2.  **Storage**: File saved to local volume (Persistent Storage).
3.  **DB Record**: Metadata saved to PostgreSQL (`status="pending"`).
4.  **Async Task**: Celery worker picks up the task.
    *   Loads file using LangChain Loaders.
    *   Splits text into chunks (1000 chars).
    *   Embeds chunks via OpenAI.
    *   Upserts to ChromaDB `rag_collection`.
5.  **Completion**: Updates Postgres status to `indexed`.

### Chat Retrieval Flow (The "RAG Engine")
1.  **User Request**: `POST /chat/message`.
2.  **Semantic Cache Check**: 
    *   Embeds question.
    *   Queries `semantic_cache`.
    *   **HIT**: Returns cached answer immediately.
    *   **MISS**: Proceeds to step 3.
3.  **Vector Retrieval**: Queries `rag_collection` for Top 20 chunks.
4.  **Re-ranking**: Passes 20 chunks + Question to **FlashRank**. Returns Top 5.
5.  **Generation**:
    *   Constructs Prompt with Context (Top 5 chunks).
    *   Calls OpenAI `gpt-4o` (Streaming).
6.  **Response**: Streams tokens to client.
7.  **Cache/Persist**:
    *   Saves conversation to Postgres.
    *   Upserts (Question, Answer) pair to `semantic_cache` for future hits.

## 5. Security
*   **Authentication**: OAuth2 Password Flow.
*   **Authorization**: JWT (JSON Web Tokens) required for all protected endpoints.
*   **Data Isolation**: Chat sessions and Documents are scoped to the `user_id`.
