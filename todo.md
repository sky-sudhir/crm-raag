# Project TODOs - Multi-Tenant RAG Platform

## Phase 1: Project Setup & Infrastructure

### 1.1 Environment Configuration

- [ ] Configure environment variables: `DATABASE_URL`, `JWT_SECRET`, `S3_BUCKET`, `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `EMBEDDING_MODEL`, etc.

### 1.2 Database Setup

- [ ] Set up database connection with async support (asyncpg)
- [ ] Configure connection pooling (pgbouncer recommended)
- [ ] Create global schema structure for application management

---

## Phase 2: Backend Core Infrastructure

### 2.1 Database Models & Migrations

- [ ] Create Alembic migration setup with dual heads (public + tenant)
- [ ] Implement global schema models (`clients`, `super_admins`, `api_keys`)
- [ ] Create tenant schema models (`users`, `categories`, `user_categories`, `document_files`, `vector_documents`, `chat_history`, `logs`)
- [ ] Set up pgvector indexes (`ivfflat` for embeddings, `gin` for metadata)
- [ ] Add pg_trgm extension and indexes for hybrid search

### 2.2 Core Backend Structure

- [ ] Set up FastAPI application with proper folder structure
- [ ] Implement `src/config.py` with Pydantic Settings for configuration
- [ ] Create `src/db/main.py` with async engine, session management, and schema routing

### 2.3 Security & Authentication

- [ ] Implement JWT token generation and validation in `src/core/security.py`
- [ ] Create password hashing utilities (Argon2/bcrypt)
- [ ] Implement role-based access control (RBAC) decorators
- [ ] Set up rate limiting middleware
- [ ] Create request ID tracking and logging

**Dependencies**: Complete Phase 1 before Phase 2

---

## Phase 3: Multi-Tenant Schema Management

### 3.1 Tenant Management Core

- [ ] Implement schema creation utilities in `src/core/tenants.py`
- [ ] Create tenant schema routing logic (search_path management)
- [ ] Implement schema migration runner for new tenants
- [ ] Add schema validation and naming conventions

### 3.2 Client Onboarding Service

- [ ] Create `src/feature/superadmin/service.py` with client onboarding logic
- [ ] Implement automated PostgreSQL schema creation
- [ ] Add client metadata insertion to global `clients` table
- [ ] Create initial admin user seeding for new tenants
- [ ] Implement client status management (active/suspended/deleted)

### 3.3 Super Admin Features

- [ ] Implement `src/feature/superadmin/routes.py` with all endpoints
- [ ] Create super admin authentication endpoints
- [ ] Build client CRUD operations
- [ ] Add client listing with pagination and filters
- [ ] Implement client activation/deactivation

**Dependencies**: Complete Phase 2 before Phase 3

---

## Phase 4: Authentication & User Management

### 4.1 Authentication System

- [ ] Create `src/feature/auth/routes.py` with auth endpoints
- [ ] Implement multi-tenant login with schema validation
- [ ] Add JWT token mechanism
- [ ] Create password reset functionality

### 4.2 User Management Service

- [ ] Build `src/feature/admin/service.py` for user operations
- [ ] Create user CRUD with role and category assignment
- [ ] Implement user-category many-to-many relationships
- [ ] Add user validation and email uniqueness checks
- [ ] Create user profile update functionality

### 4.3 User Management API

- [ ] Implement `src/feature/admin/routes.py` for user endpoints
- [ ] Create user creation with category assignment
- [ ] Add user listing with pagination and role filters
- [ ] Implement user update (role, categories, rag_type)
- [ ] Add soft delete functionality for users

**Dependencies**: Complete Phase 3 before Phase 4

---

## Phase 5: Category & Document Management

### 5.1 Category Management

- [ ] Create category CRUD operations in admin service
- [ ] Implement category validation and uniqueness checks
- [ ] Add category deletion with dependency checking
- [ ] Create category assignment utilities
- [ ] Implement category-based access control filters

### 5.2 Document Upload & Storage

- [ ] Implement S3 presigned URL generation in `src/core/s3.py`
- [ ] Create document upload workflow with validation
- [ ] Add file type and size validation
- [ ] Implement S3 key structure (`client_id/category/filename`)
- [ ] Create document metadata storage

### 5.3 Document Processing Pipeline

- [ ] Build text extraction utilities in `src/core/chunking.py`
- [ ] Implement chunking strategies (Basic/Advanced/Customized)
- [ ] Create embedding generation service
- [ ] Add background job for document processing
- [ ] Implement document status tracking (uploaded/ingesting/ready/failed)

**Dependencies**: Complete Phase 4 before Phase 5

---

## Phase 6: RAG & Vector Search

### 6.1 Vector Search Core

- [ ] Implement vector search utilities in `src/core/vector.py`
- [ ] Create pgvector KNN search functions
- [ ] Add hybrid search (vector + BM25/pg_trgm) for Advanced RAG
- [ ] Implement metadata filtering and category scoping
- [ ] Create result ranking and diversity algorithms

### 6.2 RAG Pipeline

- [ ] Build RAG service in `src/core/rag.py`
- [ ] Implement candidate retrieval with category filtering
- [ ] Create prompt building utilities
- [ ] Add LLM integration for answer generation
- [ ] Implement citation extraction and formatting

### 6.3 Chat & Query API

- [ ] Create `src/feature/user/routes.py` for chat endpoints
- [ ] Implement query processing with user category authorization
- [ ] Add streaming response support
- [ ] Create chat history storage and retrieval
- [ ] Implement query logging and metrics collection

**Dependencies**: Complete Phase 5 before Phase 6

---

## Phase 9: Frontend Authentication & Routing

### 9.1 Authentication Flow

- [ ] Create login forms for Super Admin and Client users
- [ ] Implement JWT token management and refresh
- [ ] Build role-based route protection components
- [ ] Create password reset flow
- [ ] Add session timeout handling

### 9.2 Route Structure Implementation

- [ ] Set up Super Admin routes (`/superadmin/*`)
- [ ] Create Client Admin routes (`/admin/*`)
- [ ] Implement Client User routes (`/user/*`)
- [ ] Add shared routes and error pages
- [ ] Create role-based navigation components

### 9.3 State Management

- [ ] Create authentication Redux slice or user the current one
- [ ] Implement user profile state management
- [ ] Add client/tenant state for Super Admin
- [ ] Create document management state
- [ ] Set up chat/query state management

**Dependencies**: Complete Phase 8 before Phase 9

---

## Phase 10: Frontend Super Admin Panel

### 10.1 Super Admin Dashboard

- [ ] Build Super Admin login page (`/superadmin/login`)

### 10.2 Client Management Interface

- [ ] Create client listing page with search and filters
- [ ] Build new client onboarding form
- [ ] Implement client details and edit pages
- [ ] Add client status management (activate/suspend)
- [ ] Create client deletion with confirmation

**Dependencies**: Complete Phase 9 and Backend Phase 3

---

## Phase 11: Frontend Client Admin Panel

### 11.1 Admin Dashboard

- [ ] Create admin dashboard with tenant statistics
- [ ] Build category, user, and document summaries
- [ ] Add recent activity feeds
- [ ] Implement quick action shortcuts

### 11.2 Category Management

- [ ] Build category listing and creation forms
- [ ] Create category edit and delete functionality
- [ ] Add category assignment interfaces

### 11.3 User Management

- [ ] Create user listing with role and category filters
- [ ] Build user creation form with category assignment
- [ ] Implement user edit functionality
- [ ] Add user role management

### 11.4 Document Management

- [ ] Build document listing with category filters
- [ ] Create file upload interface with S3 integration
- [ ] Implement document status tracking
- [ ] Add document metadata viewing
- [ ] Create document deletion functionality

### 11.5 RAG Table Viewer

- [ ] Build RAG chunks table display
- [ ] Show chunk_text and metadata (no vector data)
- [ ] Add filtering by category and document
- [ ] Implement search within chunks
- [ ] Create chunk metadata inspection

**Dependencies**: Complete Phase 10 and Backend Phase 5

---

## Phase 12: Frontend Client User Interface

### 12.1 Chat Interface

- [ ] Build main chat interface with query input
- [ ] Implement streaming response display
- [ ] Create citations sidebar with document references
- [ ] Add query history navigation
- [ ] Implement chat session management

### 12.2 Document Browser

- [ ] Create read-only document listing for user categories
- [ ] Build document metadata viewer
- [ ] Implement document preview functionality
- [ ] Add document search and filtering
- [ ] Create user-specific RAG table viewer

### 12.3 User Profile & History

- [ ] Build user profile management page
- [ ] Create chat history with pagination
- [ ] Implement detailed chat view with citations
- [ ] Add search functionality for chat history
- [ ] Create user preferences settings

---
