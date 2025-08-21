-- =====================================================
-- PUBLIC SCHEMA - CRM RAG Application
-- =====================================================
-- This schema contains platform-wide tables and enums
-- that are shared across all tenants

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgvector";

-- =====================================================
-- ENUM TYPES
-- =====================================================

-- User role enum
DO $$ 
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'userrole') THEN
        CREATE TYPE public.userrole AS ENUM ('ROLE_USER', 'ROLE_ADMIN');
    END IF;
END $$;

-- Organization status enum
DO $$ 
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'orgstatus') THEN
        CREATE TYPE public.orgstatus AS ENUM ('ACTIVE', 'INACTIVE');
    END IF;
END $$;

-- RAG type enum
DO $$ 
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'ragtype') THEN
        CREATE TYPE public.ragtype AS ENUM ('BASIC', 'ADV', 'CUS');
    END IF;
END $$;

-- Knowledge base status enum
DO $$ 
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'kbstatus') THEN
        CREATE TYPE public.kbstatus AS ENUM ('UPLOADED', 'INGESTING', 'COMPLETED', 'FAILED', 'DELETED');
    END IF;
END $$;

-- Audit event type enum
DO $$ 
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'auditeventtype') THEN
        CREATE TYPE public.auditeventtype AS ENUM ('ERROR', 'QUERY', 'UPLOAD', 'EMBEDDING_CREATE', 'API_CALL');
    END IF;
END $$;

-- =====================================================
-- TABLES
-- =====================================================

-- Organizations table (platform-wide)
CREATE TABLE IF NOT EXISTS public.organizations (
    id VARCHAR(36) PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(100) UNIQUE NOT NULL,
    name VARCHAR(100) UNIQUE NOT NULL,
    schema_name VARCHAR(100) UNIQUE NOT NULL,
    subdomain VARCHAR(100) UNIQUE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    status public.orgstatus DEFAULT 'ACTIVE',
    rag_type public.ragtype DEFAULT 'BASIC'
);

-- Reserved subdomains table
CREATE TABLE IF NOT EXISTS public.reserved_subdomains (
    id VARCHAR(36) PRIMARY KEY DEFAULT uuid_generate_v4(),
    subdomain VARCHAR(100) UNIQUE NOT NULL,
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- OTP table for authentication
CREATE TABLE IF NOT EXISTS public.otp (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    otp INTEGER NOT NULL,
    expires_at TIMESTAMP NOT NULL DEFAULT (NOW() + INTERVAL '5 minutes'),
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- =====================================================
-- INDEXES
-- =====================================================

-- Organizations indexes
CREATE INDEX IF NOT EXISTS idx_organizations_email ON public.organizations(email);
CREATE INDEX IF NOT EXISTS idx_organizations_subdomain ON public.organizations(subdomain);
CREATE INDEX IF NOT EXISTS idx_organizations_schema_name ON public.organizations(schema_name);

-- Reserved subdomains indexes
CREATE INDEX IF NOT EXISTS idx_reserved_subdomains_subdomain ON public.reserved_subdomains(subdomain);

-- OTP indexes
CREATE INDEX IF NOT EXISTS idx_otp_email ON public.otp(email);
CREATE INDEX IF NOT EXISTS idx_otp_expires_at ON public.otp(expires_at);

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

-- Trigger for organizations table
CREATE TRIGGER update_organizations_updated_at 
    BEFORE UPDATE ON public.organizations 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Trigger for OTP table
CREATE TRIGGER update_otp_updated_at 
    BEFORE UPDATE ON public.otp 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- =====================================================
-- INITIAL DATA
-- =====================================================

-- Insert some reserved subdomains
INSERT INTO public.reserved_subdomains (subdomain, description) VALUES
    ('api', 'Reserved for API endpoints'),
    ('docs', 'Reserved for documentation'),
    ('admin', 'Reserved for admin panel'),
    ('www', 'Reserved for main website'),
    ('mail', 'Reserved for email services'),
    ('ftp', 'Reserved for file transfer'),
    ('blog', 'Reserved for blog platform'),
    ('shop', 'Reserved for e-commerce'),
    ('support', 'Reserved for support portal'),
    ('status', 'Reserved for status page')
ON CONFLICT (subdomain) DO NOTHING;

-- =====================================================
-- COMMENTS
-- =====================================================

COMMENT ON SCHEMA public IS 'Public schema containing platform-wide tables and enums';
COMMENT ON TABLE public.organizations IS 'Stores all tenant organizations and their schema information';
COMMENT ON TABLE public.reserved_subdomains IS 'List of subdomain names reserved for platform use';
COMMENT ON TABLE public.otp IS 'One-time passwords for user authentication';

COMMENT ON COLUMN public.organizations.schema_name IS 'Unique schema name for the tenant';
COMMENT ON COLUMN public.organizations.subdomain IS 'Unique subdomain for the tenant';
COMMENT ON COLUMN public.organizations.rag_type IS 'Type of RAG system for the organization';
COMMENT ON COLUMN public.organizations.status IS 'Current status of the organization';
