-- Schema for Autonomous Vision AI Invoice Processing System
-- Used by PostgreSQL in docker-compose setup

CREATE TABLE IF NOT EXISTS invoices (
    id SERIAL PRIMARY KEY,
    invoice_number VARCHAR(100) UNIQUE NOT NULL,
    vendor_name VARCHAR(255) NOT NULL,
    vendor_vat_id VARCHAR(100),
    invoice_date DATE NOT NULL,
    due_date DATE,
    currency VARCHAR(10) DEFAULT 'USD',
    subtotal NUMERIC(12, 2) NOT NULL,
    tax_amount NUMERIC(12, 2) DEFAULT 0.00,
    total_amount NUMERIC(12, 2) NOT NULL,
    status VARCHAR(50) DEFAULT 'pending', -- 'auto_approved', 'approved_by_human', 'rejected', 'flagged'
    requires_approval BOOLEAN DEFAULT FALSE,
    flag_reason TEXT,
    approval_notes TEXT,
    ai_confidence NUMERIC(4, 2),
    raw_extraction JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS invoice_items (
    id SERIAL PRIMARY KEY,
    invoice_id INT REFERENCES invoices(id) ON DELETE CASCADE,
    description TEXT NOT NULL,
    quantity NUMERIC(10, 2) NOT NULL DEFAULT 1,
    unit_price NUMERIC(12, 2) NOT NULL,
    total_price NUMERIC(12, 2) NOT NULL
);

CREATE TABLE IF NOT EXISTS audit_logs (
    id SERIAL PRIMARY KEY,
    workflow_execution_id VARCHAR(100),
    invoice_number VARCHAR(100),
    event_type VARCHAR(50) NOT NULL, -- 'RECEIVED', 'VALIDATED', 'FLAGGED', 'APPROVED', 'FAILED'
    details JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Indexing for fast lookups and deduplication checks
CREATE INDEX IF NOT EXISTS idx_invoices_vendor_number ON invoices(vendor_name, invoice_number);
CREATE INDEX IF NOT EXISTS idx_invoices_status ON invoices(status);
