# Tools & Technologies Guide

This document explains the core tools, frameworks, and components used in the **GroundTruth** architecture and how they function together.

## 1. Backend Core

### ⚡ FastAPI
*   **What it is**: A modern, high-performance web framework for building APIs with Python 3.11+.
*   **Role**: Handles all HTTP requests, routing, validation (Pydantic), and Dependency Injection.
*   **Why we chose it**: Native support for **async/await** is critical for holding concurrent WebSocket/SSE connections during LLM streaming.

### 🐍 SQLAlchemy (Async)
*   **What it is**: The most mature SQL Toolkit and ORM for Python.
*   **Role**: Manages database interactions with PostgreSQL.
*   **Usage**: We use the `asyncpg` driver for non-blocking database queries, ensuring the API remains responsive under load.

## 2. Async Task Queue

### 🥬 Celery
*   **What it is**: A distributed task queue system.
*   **Role**: Handles heavy background processes like **Document Ingestion**.
*   **Workflow**:
    1.  User uploads a file.
    2.  API saves file and returns "Pending" instantly.
    3.  API pushes a `process_document` task to the Queue.
    4.  A Background Worker picks up the task, parses the PDF, embeds it, and indexes it.
*   **Why we chose it**: Decouples heavy processing from the user-facing API.

### 🔺 Redis
*   **What it is**: In-memory data structure store.
*   **Role**: Acts as the **Message Broker** for Celery (passing messages between API and Worker).

## 3. RAG Pipeline

### 🦜🔗 LangChain
*   **What it is**: Framework for developing applications powered by LLMs.
*   **Role**: The "Glue" code. It handles:
    *   **Loaders**: Extracting text from PDFs/Docs.
    *   **Splitters**: Chunking text into managed pieces.
    *   **Prompts**: Managing the context injection for GPT-4o.

### 🌈 ChromaDB
*   **What it is**: Open-source embedding database.
*   **Role**: Stores vector embeddings of our data.
*   **How it works**: It compares the "angle" (Cosine Similarity) between the user's question vector and our document vectors to find relevant matches.

### ⚡ FlashRank
*   **What it is**: Ultra-lightweight Re-ranking library.
*   **Role**: The "Second Pass".
    *   Chroma gets the top 20 "approximate" matches.
    *   FlashRank uses a Cross-Encoder model (`ms-marco`) to carefully score those 20 and picks the best 5.
*   **Benefit**: drastically improves answer quality.

### 🦆 DuckDuckGo Search
*   **What it is**: Privacy-focused search engine API.
*   **Role**: Provide "Hybrid Intelligence". If local documents don't answer the question, the system falls back to a live web search.

## 4. Frontend

### ⚛️ Next.js 14
*   **What it is**: The React Framework for the Web.
*   **Role**: Renders the UI (using App Router).
*   **Key Features**: Server-Side Rendering (SSR) for initial load, Client-Side Rendering for the Chat.

### 🛡️ Shadcn/UI
*   **What it is**: a collection of re-usable components built using `Radix UI` and `Tailwind CSS`.
*   **Role**: Provides the polished look and feel (Buttons, Dialogs, Toasts).

### 🚀 React Query (TanStack)
*   **What it is**: Data-fetching library for React.
*   **Role**: Manages server state. It handles caching, polling (for document status), and optimistic UI updates (chat messages).
