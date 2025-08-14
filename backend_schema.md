# Backend API & Business Logic Specification

## 1. Route & Endpoint Structure

### Super Admin Routes (Global Schema)

- **POST /superadmin/login**

  - Authenticates a super admin.
  - Returns JWT containing `role=superadmin`.

- **POST /superadmin/client**

  - Creates a new client.
  - Triggers automated creation of a PostgreSQL schema.
  - Inserts client metadata into global `clients` table.

- **GET /superadmin/clients**

  - Lists all clients.

- **PATCH /superadmin/client/{client_id}/status**

  - Activates/deactivates a client.

### Client Authentication Routes

- **POST /auth/login**

  - Authenticates client user (admin or user) using `schema_name` + credentials.
  - Returns JWT containing `schema_name`, `user_id`, `role`.

### Client Admin Routes (Per Client Schema)

- **POST /admin/categories**

  - Create category.

- **GET /admin/categories**

  - List categories.

- **POST /admin/users**

  - Create user with role and category assignment.

- **GET /admin/users**

  - List users.

- **POST /admin/documents/upload**

  - Upload document to S3 and store metadata in `document_files`.
  - Generate embeddings for `vector_documents`.

- **GET /admin/logs**

  - Retrieve all logs.

### Client User Routes (Per Client Schema)

- **POST /chat/query**

  - Send a query to RAG system.
  - Retrieve relevant documents using pgvector search.
  - Return generated answer and store chat history.

- **GET /chat/history**

  - Retrieve user's own chat history.

### Shared Routes (Per Client Schema)

- **GET /documents**

  - List documents in allowed categories.

---

## 2. Business Logic Details

### Super Admin

- Validate credentials against `super_admins` table in global schema.
- On client creation:

  1. Generate unique `schema_name`.
  2. Create new schema in PostgreSQL.
  3. Run migrations for base client schema.
  4. Insert client record in global `clients` table.

### Client Login

- Validate `schema_name` exists in `clients` table.
- Connect to that schema's `users` table for authentication.
- Return JWT with `schema_name`, `user_id`, `role`.

### Category & User Management

- Only `admin` role can create/edit categories and users.
- Store user’s allowed category IDs.
- Enforce role-based restrictions via middleware.

### Document Upload & Embedding Creation

- Upload to S3 using structure `/client_id/category_name/filename`.
- Store metadata in `document_files`.
- Generate embedding via pgvector and store in `vector_documents`.
- Log events in `logs` table.

### RAG Query

- Retrieve relevant embeddings filtered by user’s categories.
- Use LLM to generate answer.
- Store query and answer in `chat_history`.
- Log query in `logs` table.

---

## 3. Security & Access Control

- JWT payload:

  ```json
  {
    "schema_name": "client_schema",
    "user_id": "uuid",
    "role": "admin|user|superadmin"
  }
  ```

- Super Admin JWT allows access to global schema endpoints only.
- Client JWT allows access to that schema’s endpoints only.
- Middleware checks `schema_name` and `role` before processing requests.

---

## 4. Folder Structure Mapping

- `src/feature/superadmin/routes.py` – Super admin endpoints.
- `src/feature/superadmin/service.py` – Client onboarding, global schema ops.
- `src/feature/auth/routes.py` – Login endpoints for super admin and clients.
- `src/feature/admin/routes.py` – Client admin endpoints.
- `src/feature/admin/service.py` – Category, user, document logic.
- `src/feature/user/routes.py` – Client user chat/document access.
- `src/feature/user/service.py` – Chat handling, vector retrieval.
