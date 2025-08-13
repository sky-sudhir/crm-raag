# Product Requirements Document (PRD)

## 1. Overview

We are building a **multi-tenant, role-based RAG (Retrieval-Augmented Generation) platform** where each client has an isolated PostgreSQL schema. Clients can create categories, assign users to categories, and control access to documents and RAG features based on roles. The application will use **pgvector** for embeddings and store original documents in AWS S3. The system will support three RAG types:

1. **Basic RAG**
2. **Advanced RAG**
3. **Customized RAG** (with custom prompts & documents)

The platform will have a React-based frontend with a dashboard for document management, chat, and logs.

---

## 2. Goals & Non-Goals

### Goals

- Role & category-based access to RAG responses.
- Multi-tenant setup with **PostgreSQL schema per client**.
- Support multiple RAG types per client.
- Secure document storage in AWS S3.
- Embeddings generated at upload time using pgvector.
- Scalable architecture for future thousands of clients.

### Non-Goals (MVP Scope)

- No SSO/OAuth (future scope).
- No category hierarchy (flat structure only).
- No automatic log expiration (future scope).
- No per-client LLM isolation initially.

---

## 3. Architecture Overview

**Backend:**

- **FastAPI / Node.js** (TBD)
- PostgreSQL with **pgvector** for vector search.
- AWS S3 for document storage (`client_id/category/files`).
- LLM instance for all clients (future isolation possible).
- Role-based authorization layer.

**Frontend:**

- **React.js**
- Multi-tenant login (client admin & client users).
- Dashboard for category management, document upload, chat, and logs.

**Data Flow:**

1. Client admin uploads documents → Stored in S3 → Embeddings stored in pgvector table.
2. User sends a query → Relevant vectors retrieved based on user's allowed categories.
3. LLM generates an answer → Chat stored in `chat` table & logs recorded.

---

## 4. Database Schema (per client)

Each client has a dedicated **PostgreSQL schema** with 5 collections (tables):

1. **vector_documents**

   - id (UUID, PK)
   - category_id (FK)
   - embedding (vector)
   - metadata (JSON)
   - created_at (timestamp)

1. **document_files**

   - id (UUID, PK)
   - category_id (FK)
   - s3_url (string)
   - metadata (JSON)
   - created_at (timestamp)

1. **chat_history**

   - id (UUID, PK)
   - user_id (FK)
   - question (text)
   - answer (text)
   - created_at (timestamp)

1. **users**

   - id (UUID, PK)
   - name (string)
   - email (string)
   - password_hash (string)
   - categories (array of category_ids)
   - role (enum: admin/user)
   - rag_type (enum: basic, advanced, customized)
   - created_at (timestamp)

1. **categories**

   - id (UUID, PK)
   - name (string)
   - created_at (timestamp)

1. **logs**

   - id (UUID, PK)
   - user_id (FK)
   - event_type (enum: error, query, upload, embedding_creation, api_call)
   - details (JSON)
   - created_at (timestamp)

**Global (Application-level) DB:**

- `clients` table for storing:

  - client_id
  - schema_name
  - rag_type
  - onboarding_date

---

## 5. RAG Types

1. **Basic RAG** – Standard vector retrieval + LLM.
2. **Advanced RAG** – Includes metadata filtering, improved chunking, hybrid search.
3. **Customized RAG** – Client can define:

   - Custom prompts/templates.
   - Specialized chunking strategies.

---

## 6. Roles & Permissions

**Client Admin:**

- Create/edit categories.
- Create/edit users.
- Upload documents.
- View all logs.

**Client User:**

- Query documents only in assigned categories.
- View personal chat history.

**Access Control:**

- Union-based: If user has multiple categories, they see all combined data.
- Single category possible per user.

---

## 7. Document Storage

- AWS S3 Bucket Structure:

  ```
  /client_id/
      /category_name/
          file1.pdf
          file2.docx
  ```

- Metadata stored in `vector_documents` table.
- Embeddings created at upload time.

---

## 8. Logs

- Stored per client in `logs` table.
- Types:

  - System errors
  - Query history
  - API calls
  - Embedding creation

- Retention: No limit (future scope for time-based cleanup).

---

## 9. Frontend Features

### Client Admin Dashboard

- Category management CRUD.
- User management CRUD.
- Document upload per category.
- Logs viewer.

### Client User Dashboard

- Chat interface.
- View personal chat history.

---

## 10. APIs (Sample)

- `POST /client/document/upload`
- `POST /api/chat`
- `GET /api/categories`
- `POST /api/user`
- `GET /api/logs`
- `GET /api/docs`

---

## 11. Security

- Email/password login.
- Role-based middleware.
- JWT authentication for client ID and authorization
- Data isolation at schema level.
- HTTPS in transit.

---

## 12. Future Scope

- SSO/OAuth integration.
- Per-client LLM instance.
- Log retention policy.
- Category hierarchy.
- Concurrent scaling optimizations.

---

## 13. Considerations

- Expected to scale to hundreds/thousands of clients.
- Large document handling in S3.
- Multi-tenant vector search in pgvector.
- Role-based filtering at query time.

---

**This PRD forms the MVP blueprint for the multi-tenant, role-based RAG system with PostgreSQL schema isolation and React frontend.**
