# Frontend Requirements & Routes

This document defines the **frontend screens, routes, and user flows** for the multi-tenant, role-based RAG platform, covering **Super Admin**, **Client Admin**, and **Client User** roles.

---

## 1. Global Structure

- **Tech Stack:** React.js + React Router, Tailwind CSS (or similar), State Management (Redux/Zustand/Context API)
- **Authentication:** JWT-based login flows per role.
- **Routing:** Separate layout and route groups for **Super Admin** vs **Client (Admin/User)**.
- **Error Handling:** Global error pages (401 Unauthorized, 403 Forbidden, 404 Not Found, 500 Server Error)
- **Responsive:** All screens optimized for desktop & tablet.

---

## 2. Role-Based Routes & Screens

### 2.1 **Super Admin**

Base Path: `/superadmin`

#### **Authentication & Account**

- `/superadmin/login` — Super Admin Login Screen.
- `/superadmin/forgot-password` — Password reset initiation.

#### **Dashboard**

- `/superadmin/dashboard` — Overview of clients (active/inactive, usage stats).

#### **Client Management**

- `/superadmin/clients` — List of all clients (table with search, filters).
- `/superadmin/clients/new` — Onboard new client (name, schema name, RAG type).
- `/superadmin/clients/:id` — Client details (status, schema info, onboarding date, RAG type).
- `/superadmin/clients/:id/edit` — Update client info & status (activate/suspend).

#### **Account Settings**

- `/superadmin/profile` — View/update profile, change password.

---

### 2.2 **Client Admin**

Base Path: `/admin`

#### **Authentication & Account**

- `/login` — Client Admin & User login (role resolved after auth).
- `/forgot-password` — Password reset initiation.

#### **Dashboard**

- `/admin/dashboard` — Summary of categories, users, documents, logs.

#### **Category Management**

- `/admin/categories` — List categories.
- `/admin/categories/new` — Create category.
- `/admin/categories/:id/edit` — Edit category.

#### **User Management**

- `/admin/users` — List users.
- `/admin/users/new` — Create user (assign role, categories, rag_type).
- `/admin/users/:id/edit` — Edit user (role, categories).
- `/admin/users/:id/view` — View user details.

#### **Document Management**

- `/admin/documents` — List documents (filter by category, status).
- `/admin/documents/upload` — Upload new document (presigned URL flow).
- `/admin/documents/:id` — Document details (status, metadata, preview if possible).
- `/admin/rag-table` — View **RAG Chunks Table**: displays only `chunk_text` and associated `metadata` for uploaded documents (no vector data).

#### **Logs**

- `/admin/logs` — View tenant-specific logs.
- `/admin/logs/:id` — Log details.

#### **Account Settings**

- `/admin/profile` — View/update profile, change password.

---

### 2.3 **Client User**

Base Path: `/user`

#### **Dashboard / Chat**

- `/chat` — Main chat interface (question input, answer display, citations sidebar).

#### **Chat History**

- `/chat/history` — Paginated list of previous chats.
- `/chat/history/:id` — View chat details (question, answer, citations).

#### **Document Browser** (Read-only)

- `/documents` — List of documents in assigned categories.
- `/documents/:id` — Document metadata & preview.
- `/rag-table` — View **RAG Chunks Table** for assigned categories: only `chunk_text` and `metadata` shown.

#### **Account Settings**

- `/profile` — View/update profile, change password.

---

## 3. Common / Shared Screens

- `/` — Role-based redirect after login.
- `/error/401` — Unauthorized.
- `/error/403` — Forbidden.
- `/error/404` — Not Found.
- `/error/500` — Server Error.

---

## 4. Navigation Structure

- **Super Admin Navbar:** Dashboard, Clients, Logs, Profile.
- **Client Admin Navbar:** Dashboard, Categories, Users, Documents, RAG Table, Logs, Profile.
- **Client User Navbar:** Chat, History, Documents, RAG Table, Profile.

---

## 5. Key UI Components

- **Login Form** (with client selector for admin/user login)
- **Data Tables** (with search, sort, filter, pagination)
- **Forms** (category, user, client creation)
- **Chat UI** (streamed responses, citation display)
- **File Upload Component** (S3 presigned URL integration)
- **RAG Chunks Viewer** (table showing chunk_text and metadata)
- **Logs Viewer**
- **Profile Editor**
- **Modal Dialogs** (confirmation prompts, file details)

---

## 6. API Integration Points

- Auth API: `/auth/login`, `/auth/refresh`
- Client Management API: `/tenants`, `/tenants/:id`
- User Management API: `/users`, `/users/:id`
- Category API: `/categories`, `/categories/:id`
- Documents API: `/documents`, `/documents/presign`
- RAG Table API: `/vector-documents` (filtered to return only chunk_text + metadata)
- Chat API: `/chat/query`, `/chat/history`
- Logs API: `/logs`, `/logs/:id`

---

## 7. Notes

- Super Admin panel is **completely separate** from client-facing app.
- Client Admin and Client User share login but differ in visible features/routes.
- Frontend should enforce **role-based route protection**.
- UI should display **tenant-specific branding** if applicable.
- RAG table **must not** expose vector embeddings in the UI or API response.
