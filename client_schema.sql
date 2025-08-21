-- =====================================================
-- CLIENT/TENANT SCHEMA - CRM RAG Application
-- =====================================================
-- This schema contains tenant-specific tables
-- Replace 'tenant_schema_name' with the actual tenant schema name
-- Usage: CREATE SCHEMA tenant_schema_name; then run this script

-- =====================================================
-- SCHEMA CREATION
-- =====================================================
-- Uncomment and modify the line below to create a specific tenant schema
-- CREATE SCHEMA IF NOT EXISTS tenant_schema_name;

-- =====================================================
-- TABLES
-- =====================================================

-- Users table
CREATE TABLE IF NOT EXISTS users (
    id VARCHAR(36) PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    role public.userrole DEFAULT 'ROLE_USER',
    is_owner BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Categories table
CREATE TABLE IF NOT EXISTS categories (
    id VARCHAR(36) PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- User-Categories association table
CREATE TABLE IF NOT EXISTS user_categories (
    user_id VARCHAR(36) NOT NULL,
    category_id VARCHAR(36) NOT NULL,
    PRIMARY KEY (user_id, category_id),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE CASCADE
);

-- Knowledge Base table
CREATE TABLE IF NOT EXISTS knowledge_base (
    id VARCHAR(36) PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id VARCHAR(36) NOT NULL,
    category_id VARCHAR(36) NOT NULL,
    file_name TEXT NOT NULL,
    json TEXT,
    status public.kbstatus DEFAULT 'UPLOADED',
    s3_url TEXT,
    mime VARCHAR(255),
    file_size INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE CASCADE
);

-- Vector Documents table (for RAG)
CREATE TABLE IF NOT EXISTS vector_doc (
    id VARCHAR(36) PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id VARCHAR(36) NOT NULL,
    category_id VARCHAR(36) NOT NULL,
    file_id VARCHAR(36) NOT NULL,
    chunk_id INTEGER NOT NULL,
    chunk_text TEXT NOT NULL,
    chunk_hash VARCHAR(64),
    embedding vector(768) NOT NULL,
    doc_metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE CASCADE,
    FOREIGN KEY (file_id) REFERENCES knowledge_base(id) ON DELETE CASCADE
);

-- Chat Tabs table
CREATE TABLE IF NOT EXISTS chat_tabs (
    id VARCHAR(36) PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id VARCHAR(36) NOT NULL,
    name TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Chat History table
CREATE TABLE IF NOT EXISTS chat_history (
    id VARCHAR(36) PRIMARY KEY DEFAULT uuid_generate_v4(),
    question TEXT NOT NULL,
    answer TEXT,
    citation JSONB,
    latency INTEGER,
    token_prompt INTEGER,
    token_completion INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Chat Tab - Chat History association table
CREATE TABLE IF NOT EXISTS chat_tab_history_association (
    chat_tab_id VARCHAR(36) NOT NULL,
    chat_history_id VARCHAR(36) NOT NULL,
    PRIMARY KEY (chat_tab_id, chat_history_id),
    FOREIGN KEY (chat_tab_id) REFERENCES chat_tabs(id) ON DELETE CASCADE,
    FOREIGN KEY (chat_history_id) REFERENCES chat_history(id) ON DELETE CASCADE
);

-- Audit Logs table
CREATE TABLE IF NOT EXISTS audit_logs (
    id VARCHAR(36) PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id VARCHAR(36) NOT NULL,
    event_type public.auditeventtype NOT NULL,
    details JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- =====================================================
-- INDEXES
-- =====================================================

-- Users indexes
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);
CREATE INDEX IF NOT EXISTS idx_users_is_owner ON users(is_owner);

-- Categories indexes
CREATE INDEX IF NOT EXISTS idx_categories_name ON categories(name);

-- User-Categories indexes
CREATE INDEX IF NOT EXISTS idx_user_categories_user_id ON user_categories(user_id);
CREATE INDEX IF NOT EXISTS idx_user_categories_category_id ON user_categories(category_id);

-- Knowledge Base indexes
CREATE INDEX IF NOT EXISTS idx_knowledge_base_user_id ON knowledge_base(user_id);
CREATE INDEX IF NOT EXISTS idx_knowledge_base_category_id ON knowledge_base(category_id);
CREATE INDEX IF NOT EXISTS idx_knowledge_base_status ON knowledge_base(status);
CREATE INDEX IF NOT EXISTS idx_knowledge_base_created_at ON knowledge_base(created_at);

-- Vector Documents indexes
CREATE INDEX IF NOT EXISTS idx_vector_doc_user_id ON vector_doc(user_id);
CREATE INDEX IF NOT EXISTS idx_vector_doc_category_id ON vector_doc(category_id);
CREATE INDEX IF NOT EXISTS idx_vector_doc_file_id ON vector_doc(file_id);
CREATE INDEX IF NOT EXISTS idx_vector_doc_chunk_id ON vector_doc(chunk_id);
CREATE INDEX IF NOT EXISTS idx_vector_doc_embedding ON vector_doc USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

-- Chat Tabs indexes
CREATE INDEX IF NOT EXISTS idx_chat_tabs_user_id ON chat_tabs(user_id);

-- Chat History indexes
CREATE INDEX IF NOT EXISTS idx_chat_history_created_at ON chat_history(created_at);

-- Chat Tab - Chat History association indexes
CREATE INDEX IF NOT EXISTS idx_chat_tab_history_chat_tab_id ON chat_tab_history_association(chat_tab_id);
CREATE INDEX IF NOT EXISTS idx_chat_tab_history_chat_history_id ON chat_tab_history_association(chat_history_id);

-- Audit Logs indexes
CREATE INDEX IF NOT EXISTS idx_audit_logs_user_id ON audit_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_event_type ON audit_logs(event_type);
CREATE INDEX IF NOT EXISTS idx_audit_logs_created_at ON audit_logs(created_at);

-- =====================================================
-- TRIGGERS
-- =====================================================

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Triggers for all tables with updated_at columns
CREATE TRIGGER update_users_updated_at 
    BEFORE UPDATE ON users 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_categories_updated_at 
    BEFORE UPDATE ON categories 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_knowledge_base_updated_at 
    BEFORE UPDATE ON knowledge_base 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_vector_doc_updated_at 
    BEFORE UPDATE ON vector_doc 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_chat_tabs_updated_at 
    BEFORE UPDATE ON chat_tabs 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_chat_history_updated_at 
    BEFORE UPDATE ON chat_history 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_audit_logs_updated_at 
    BEFORE UPDATE ON audit_logs 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- =====================================================
-- CONSTRAINTS
-- =====================================================

-- Ensure chunk_id is non-negative
ALTER TABLE vector_doc ADD CONSTRAINT chk_chunk_id_positive CHECK (chunk_id >= 0);

-- Ensure file_size is positive
ALTER TABLE knowledge_base ADD CONSTRAINT chk_file_size_positive CHECK (file_size > 0);

-- Ensure latency is non-negative
ALTER TABLE chat_history ADD CONSTRAINT chk_latency_positive CHECK (latency >= 0);

-- Ensure token counts are non-negative
ALTER TABLE chat_history ADD CONSTRAINT chk_token_prompt_positive CHECK (token_prompt >= 0);
ALTER TABLE chat_history ADD CONSTRAINT chk_token_completion_positive CHECK (token_completion >= 0);

-- =====================================================
-- COMMENTS
-- =====================================================

COMMENT ON TABLE users IS 'Tenant users with authentication and role information';
COMMENT ON TABLE categories IS 'Document categories for organizing knowledge base';
COMMENT ON TABLE user_categories IS 'Many-to-many relationship between users and categories';
COMMENT ON TABLE knowledge_base IS 'Stores uploaded documents and their metadata';
COMMENT ON TABLE vector_doc IS 'Vectorized document chunks for RAG retrieval';
COMMENT ON TABLE chat_tabs IS 'Chat conversation tabs for users';
COMMENT ON TABLE chat_history IS 'Chat conversation history and responses';
COMMENT ON TABLE chat_tab_history_association IS 'Association between chat tabs and chat history';
COMMENT ON TABLE audit_logs IS 'Audit trail of user actions and system events';

COMMENT ON COLUMN users.is_owner IS 'Whether the user is the organization owner';
COMMENT ON COLUMN users.role IS 'User role within the tenant organization';
COMMENT ON COLUMN vector_doc.embedding IS '768-dimensional vector embedding for semantic search';
COMMENT ON COLUMN vector_doc.chunk_hash IS 'SHA-256 hash to prevent duplicate chunks';
COMMENT ON COLUMN vector_doc.doc_metadata IS 'Additional metadata for the document chunk';
COMMENT ON COLUMN knowledge_base.status IS 'Current processing status of the document';
COMMENT ON COLUMN chat_history.citation IS 'Source citations for the generated response';
COMMENT ON COLUMN chat_history.latency IS 'Response generation time in milliseconds';
COMMENT ON COLUMN audit_logs.details IS 'Additional details about the audit event';

-- =====================================================
-- SAMPLE DATA (Optional)
-- =====================================================

-- Insert a default admin user (modify as needed)
-- INSERT INTO users (id, name, email, password, role, is_owner) VALUES
--     ('admin-user-id', 'Admin User', 'admin@tenant.com', 'hashed_password', 'ROLE_ADMIN', true);

-- Insert a default category
-- INSERT INTO categories (id, name) VALUES
--     ('default-category-id', 'General');

-- =====================================================
-- USAGE NOTES
-- =====================================================
-- 1. This schema should be created for each tenant
-- 2. Replace 'tenant_schema_name' with the actual tenant schema name
-- 3. Ensure the pgvector extension is enabled in the database
-- 4. The vector_doc.embedding column uses pgvector for similarity search
-- 5. All foreign key relationships maintain referential integrity
-- 6. Timestamps are automatically updated via triggers
-- 7. Indexes are optimized for common query patterns
