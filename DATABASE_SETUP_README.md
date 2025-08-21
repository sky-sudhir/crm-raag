# Database Setup Guide - CRM RAG Application

This guide explains how to set up the database for the CRM RAG application using the provided SQL files.

## Overview

The application uses a multi-tenant architecture with two schemas:
1. **Public Schema** (`public_schema.sql`) - Contains platform-wide tables and enums
2. **Client/Tenant Schema** (`client_schema.sql`) - Contains tenant-specific tables

## Prerequisites

- PostgreSQL 12 or higher
- `uuid-ossp` extension
- `pgvector` extension (for vector similarity search)

## Installation Steps

### Step 1: Create Database

```sql
-- Connect to PostgreSQL as superuser
CREATE DATABASE crm_rag_db;
\c crm_rag_db;
```

### Step 2: Enable Extensions

```sql
-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgvector";
```

### Step 3: Run Public Schema Script

```bash
# Run the public schema script
psql -d crm_rag_db -f public_schema.sql
```

This will create:
- Enum types for user roles, organization status, RAG types, etc.
- Platform-wide tables (organizations, reserved_subdomains, otp)
- Indexes and triggers
- Initial data (reserved subdomains)

### Step 4: Create Tenant Schemas

For each tenant organization, create a separate schema:

```sql
-- Example: Create schema for tenant "acme_corp"
CREATE SCHEMA IF NOT EXISTS acme_corp;

-- Set search path to the tenant schema
SET search_path TO acme_corp;

-- Run the client schema script (modify the file to use the correct schema name)
-- Or manually execute the CREATE TABLE statements with the correct schema
```

### Step 5: Run Client Schema Script

```bash
# Modify client_schema.sql to use the correct schema name
# Replace 'tenant_schema_name' with 'acme_corp' in the file

# Then run the client schema script
psql -d crm_rag_db -f client_schema.sql
```

## Schema Structure

### Public Schema Tables

| Table | Purpose |
|-------|---------|
| `organizations` | Platform-wide organization registry |
| `reserved_subdomains` | Reserved subdomain names |
| `otp` | One-time passwords for authentication |

### Client Schema Tables

| Table | Purpose |
|-------|---------|
| `users` | Tenant users with roles |
| `categories` | Document categories |
| `user_categories` | User-category associations |
| `knowledge_base` | Uploaded documents |
| `vector_doc` | Vectorized document chunks for RAG |
| `chat_tabs` | Chat conversation tabs |
| `chat_history` | Chat conversation history |
| `chat_tab_history_association` | Chat tab-history associations |
| `audit_logs` | Audit trail |

## Database Relationships

```
organizations (public)
    ↓ (1:1)
tenant_schema.users
    ↓ (1:many)
tenant_schema.knowledge_base
    ↓ (1:many)
tenant_schema.vector_doc

tenant_schema.users
    ↓ (many:many)
tenant_schema.categories
    (via user_categories)

tenant_schema.users
    ↓ (1:many)
tenant_schema.chat_tabs
    ↓ (many:many)
tenant_schema.chat_history
    (via chat_tab_history_association)
```

## Configuration

### Environment Variables

Ensure these environment variables are set in your `.env` file:

```bash
DATABASE_URL=postgresql://username:password@localhost:5432/crm_rag_db
```

### Database Connection

The application automatically:
1. Creates public schema tables on startup
2. Creates tenant-specific tables when organizations are onboarded
3. Manages schema switching based on tenant context

## Testing the Setup

### 1. Verify Public Schema

```sql
\c crm_rag_db
\dt public.*
```

Should show:
- organizations
- reserved_subdomains
- otp

### 2. Verify Enums

```sql
SELECT typname FROM pg_type WHERE typnamespace = 'public'::regnamespace;
```

Should show:
- userrole
- orgstatus
- ragtype
- kbstatus
- auditeventtype

### 3. Test Tenant Schema Creation

```sql
-- Create a test tenant schema
CREATE SCHEMA test_tenant;
SET search_path TO test_tenant;

-- Run client schema creation (modify the SQL file first)
-- Then verify tables were created
\dt test_tenant.*
```

## Troubleshooting

### Common Issues

1. **Extension not found**
   ```sql
   -- Install pgvector extension
   CREATE EXTENSION IF NOT EXISTS "pgvector";
   ```

2. **Permission denied**
   ```sql
   -- Grant necessary permissions
   GRANT ALL PRIVILEGES ON DATABASE crm_rag_db TO your_user;
   GRANT ALL PRIVILEGES ON SCHEMA public TO your_user;
   ```

3. **Schema not found**
   ```sql
   -- Ensure schema exists
   CREATE SCHEMA IF NOT EXISTS tenant_name;
   ```

### Verification Queries

```sql
-- Check if all required extensions are installed
SELECT extname FROM pg_extension WHERE extname IN ('uuid-ossp', 'pgvector');

-- Check if all enum types exist
SELECT typname FROM pg_type WHERE typnamespace = 'public'::regnamespace;

-- Check if public schema tables exist
SELECT tablename FROM pg_tables WHERE schemaname = 'public';

-- Check if tenant schema tables exist
SELECT tablename FROM pg_tables WHERE schemaname = 'your_tenant_schema';
```

## Performance Considerations

1. **Vector Search**: The `vector_doc.embedding` column uses pgvector with IVFFlat index for efficient similarity search
2. **Indexes**: All foreign keys and commonly queried columns are indexed
3. **Partitioning**: Consider partitioning large tables (like `vector_doc`) by date if you expect high volume

## Backup and Recovery

### Backup

```bash
# Full database backup
pg_dump -h localhost -U username -d crm_rag_db > backup.sql

# Schema-specific backup
pg_dump -h localhost -U username -d crm_rag_db --schema=public > public_backup.sql
pg_dump -h localhost -U username -d crm_rag_db --schema=tenant_name > tenant_backup.sql
```

### Recovery

```bash
# Restore full database
psql -h localhost -U username -d crm_rag_db < backup.sql

# Restore specific schema
psql -h localhost -U username -d crm_rag_db < public_backup.sql
psql -h localhost -U username -d crm_rag_db < tenant_backup.sql
```

## Security Notes

1. **Row Level Security**: Consider implementing RLS for multi-tenant data isolation
2. **Connection Pooling**: Use connection pooling (e.g., PgBouncer) for production
3. **Encryption**: Enable SSL connections and consider encrypting sensitive data
4. **Audit**: All user actions are logged in the `audit_logs` table

## Support

If you encounter issues:
1. Check the application logs for detailed error messages
2. Verify database permissions and extensions
3. Ensure all required environment variables are set
4. Check that the database URL format is correct
