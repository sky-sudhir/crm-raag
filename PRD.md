# Product Requirements Document (PRD)

## 1. Overview

We are building a **multi-tenant, role-based RAG (Retrieval-Augmented Generation) platform** where each client has an **isolated PostgreSQL schema**. Whenever a new client is onboarded, a **new dedicated schema** will be created automatically for that client. The application will also have a **global application management schema** to store and manage client information, accessible only by a **Super Admin**.

Clients can create categories, assign users to categories, and control access to documents and RAG features based on roles. The application will use **pgvector** for embeddings and store original documents in AWS S3. The system will support three RAG types:

1. **Basic RAG**
2. **Advanced RAG**
3. **Customized RAG** (with custom prompts & documents)

The platform will have a React-based frontend with a dashboard for document management, chat, and logs.

---

## 2. Goals & Non-Goals

### Goals

- Role & category-based access to RAG responses.
- **Multi-tenant setup with PostgreSQL schema per client**.
- **Automated schema creation on client onboarding**.
- Global application schema to store and manage client metadata.
- Super Admin role to manage clients and global schema.
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
- Automated schema creation logic in onboarding workflow.
- Super Admin management APIs for client creation, schema provisioning, and status updates.

**Frontend:**

- **React.js**
- Multi-tenant login (Super Admin, client admin & client users).
- Dashboard for category management, document upload, chat, and logs.

**Data Flow:**

1. Super Admin adds a client → Application creates a **new PostgreSQL schema** → Inserts client metadata into global `application_management` schema.
2. Client admin uploads documents → Stored in S3 → Embeddings stored in `vector_documents` table in that client's schema.
3. User selects `schema_name` at login → JWT contains `schema_name`, `user_id`, and `role` for access control.
4. User sends a query → Relevant vectors retrieved based on user's allowed categories.
5. LLM generates an answer → Chat stored in `chat_history` table in that client's schema & logs recorded.

---

## 4. Database Schema

### **Global Application Management Schema**

**Table:** `clients`

- client_id (UUID, PK)
- schema_name (string, unique)
- rag_type (enum: basic, advanced, customized)
- onboarding_date (timestamp)
- status (enum: active/inactive)

**Table:** `super_admins`

- id (UUID, PK)
- name (string)
- email (string, unique)
- password (string)
- created_at (timestamp)

### **Per Client Schema** (created automatically at onboarding)

1. **vector_documents**
2. **document_files**
3. **chat_history**
4. **users**
5. **categories**
6. **logs**

---

## 5. RAG Types

Same as before.

---

## 6. Roles & Permissions

**Super Admin:**

- Manage global `clients` table.
- Onboard new clients and create their schemas.
- Activate/deactivate clients.

**Client Admin:**

- Create/edit categories.
- Create/edit users.
- Upload documents.
- View all logs.

**Client User:**

- Query documents only in assigned categories.
- View personal chat history.

**Access Control:**

- JWT will include `schema_name`, `user_id`,`email` and `role`.
- Union-based category access.

---
