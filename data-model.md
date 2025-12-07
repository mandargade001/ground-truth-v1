# Data Model Documentation

This document outlines the schema and data structures used across the various databases in the **GroundTruth** application.

## 1. Relational Database (PostgreSQL)

We use PostgreSQL to store structured data such as Users, Document metadata, and Chat History. We use **SQLAlchemy** ORM for interactions.

### `users` Table
Stores authentication and user profile data.
*   `id` (Integer, Primary Key): Unique User ID.
*   `email` (String, Unique): User email address.
*   `hashed_password` (String): Bcrypt hashed password.
*   `is_active` (Boolean): Account status.
*   `is_superuser` (Boolean): Admin privileges.
*   `created_at` (DateTime): Registration time.

### `documents` Table
Stores metadata for uploaded files. The actual content is stored on disk/S3 and indexed in Vector DB.
*   `id` (Integer, Primary Key): Unique Document ID.
*   `title` (String): Display name of the file.
*   `filename` (String): Physical filename on disk.
*   `s3_key` (String): Path to the file storage (currently local path).
*   `media_type` (String): MIME type (e.g., `application/pdf`).
*   `status` (String): Ingestion status (`pending`, `processing`, `indexed`, `failed`).
*   `error_message` (Text): Reason for failure if any.
*   `owner_id` (Integer, FK): Foreign Key to `users.id`.
*   `created_at` (DateTime): Upload timestamp.

### `chat_sessions` Table
Groups chat messages into conversation threads.
*   `id` (Integer, Primary Key): Unique Session ID.
*   `user_id` (Integer, FK): Foreign Key to `users.id`.
*   `created_at` (DateTime): Session start time.
*   `updated_at` (DateTime): Last activity time.

### `chat_messages` Table
Stores individual messages within a session.
*   `id` (Integer, Primary Key): Unique Message ID.
*   `session_id` (Integer, FK): Foreign Key to `chat_sessions.id`.
*   `role` (String): Message sender (`user` or `assistant`).
*   `content` (Text): The actual text content.
*   `created_at` (DateTime): Timestamp.

## 2. Vector Database (ChromaDB)

We use ChromaDB to store high-dimensional vector embeddings of document chunks for semantic search.

### Collection: `rag_collection`
Stores document chunks.
*   **Vector**: 1536-dimensional embedding (OpenAI `text-embedding-3-small`).
*   **Metadata**:
    *   `source_doc_id`: ID from Postgres `documents` table (for deletion).
    *   `source`: Filename (for citations).
    *   `page`: Page number (if PDF).

### Collection: `semantic_cache`
Stores Question-Answer pairs to speed up repetitive queries.
*   **Vector**: Embedding of the User Question.
*   **Metadata**:
    *   `question`: The original question text.
    *   `answer`: The generated answer text.
    *   `timestamp`: When it was cached.

## 3. Key-Value Store (Redis)

Redis is primarily used as a message broker for Celery and not for persistent data storage.

*   **Broker Keys**: Celery task queues (`celery`).
*   **Result Backend**: Task results (temporary).

## 4. File System (Blob Storage)

Files are currently stored in a local mounted volume (mapped to `/app/uploads` in Docker).
*   **Naming Convention**: `{user_id}_{filename}` (e.g., `1_invoice.pdf`).
*   **Purpose**: Source of truth for raw files and serving previews.
