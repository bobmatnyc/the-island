-- Database Schema for Document Classification System
-- Version: 1.0
-- Last Updated: 2025-11-16
--
-- Design Decision: SQLite for embedded database
-- Rationale: Single-file database suitable for desktop research tools.
-- No network overhead, ACID guarantees, full SQL support.
--
-- Trade-offs:
-- - Scalability: Single-user vs. PostgreSQL multi-user
-- - Performance: ~50K reads/sec vs. PostgreSQL ~100K+ reads/sec
-- - Features: Limited full-text search vs. PostgreSQL rich text search
--
-- Extension Point: Can migrate to PostgreSQL if multi-user access needed
-- or dataset exceeds 100GB (SQLite limit: 281TB theoretical, 100GB practical)

-- ============================================================================
-- CORE TABLES
-- ============================================================================

-- Canonical documents registry
CREATE TABLE IF NOT EXISTS documents (
    canonical_id TEXT PRIMARY KEY,
    document_type TEXT NOT NULL,
    document_subtype TEXT,
    title TEXT,
    date TEXT,  -- ISO 8601 format
    date_created TEXT,
    date_modified TEXT,

    -- Classification
    classification_confidence REAL,
    classification_method TEXT,
    classified_at TEXT,

    -- Content
    word_count INTEGER,
    page_count INTEGER,
    language TEXT DEFAULT 'en',

    -- Quality
    ocr_quality TEXT,
    ocr_confidence REAL,
    completeness TEXT,
    redaction_level TEXT,

    -- Processing
    ingested_at TEXT,
    processed_at TEXT,
    last_updated TEXT,

    -- Flags
    manually_reviewed BOOLEAN DEFAULT FALSE,
    has_errors BOOLEAN DEFAULT FALSE,

    -- Full text for search
    content_text TEXT,

    CONSTRAINT valid_confidence CHECK (classification_confidence BETWEEN 0.0 AND 1.0),
    CONSTRAINT valid_ocr_confidence CHECK (ocr_confidence IS NULL OR ocr_confidence BETWEEN 0.0 AND 1.0)
);

-- Indexes for common queries
CREATE INDEX IF NOT EXISTS idx_documents_type ON documents(document_type);
CREATE INDEX IF NOT EXISTS idx_documents_date ON documents(date);
CREATE INDEX IF NOT EXISTS idx_documents_confidence ON documents(classification_confidence);
CREATE INDEX IF NOT EXISTS idx_documents_quality ON documents(ocr_quality, completeness);

-- Full-text search index
CREATE VIRTUAL TABLE IF NOT EXISTS documents_fts USING fts5(
    canonical_id UNINDEXED,
    title,
    content_text,
    content=documents,
    content_rowid=rowid
);

-- ============================================================================
-- CLASSIFICATION DETAILS
-- ============================================================================

CREATE TABLE IF NOT EXISTS document_classifications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    canonical_id TEXT NOT NULL,
    document_type TEXT NOT NULL,
    document_subtype TEXT,
    classification_method TEXT NOT NULL,  -- rule_based, ml_model, manual, hybrid
    confidence REAL NOT NULL,
    model_version TEXT,
    features_detected TEXT,  -- JSON array
    classified_at TEXT NOT NULL,

    FOREIGN KEY (canonical_id) REFERENCES documents(canonical_id) ON DELETE CASCADE,
    CONSTRAINT valid_confidence CHECK (confidence BETWEEN 0.0 AND 1.0)
);

CREATE INDEX IF NOT EXISTS idx_classifications_doc ON document_classifications(canonical_id);
CREATE INDEX IF NOT EXISTS idx_classifications_type ON document_classifications(document_type);

-- Alternative classifications considered
CREATE TABLE IF NOT EXISTS classification_alternatives (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    canonical_id TEXT NOT NULL,
    alternative_type TEXT NOT NULL,
    confidence REAL NOT NULL,
    reason TEXT,

    FOREIGN KEY (canonical_id) REFERENCES documents(canonical_id) ON DELETE CASCADE,
    CONSTRAINT valid_confidence CHECK (confidence BETWEEN 0.0 AND 1.0)
);

CREATE INDEX IF NOT EXISTS idx_alternatives_doc ON classification_alternatives(canonical_id);

-- ============================================================================
-- ENTITY EXTRACTION
-- ============================================================================

CREATE TABLE IF NOT EXISTS document_entities (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    canonical_id TEXT NOT NULL,
    entity_type TEXT NOT NULL,  -- person, organization, location, date, case, financial
    entity_name TEXT NOT NULL,
    entity_role TEXT,  -- Context-specific role
    mentions INTEGER DEFAULT 1,
    confidence REAL,
    first_mention_offset INTEGER,  -- Character offset of first mention

    FOREIGN KEY (canonical_id) REFERENCES documents(canonical_id) ON DELETE CASCADE,
    CONSTRAINT valid_confidence CHECK (confidence IS NULL OR confidence BETWEEN 0.0 AND 1.0)
);

CREATE INDEX IF NOT EXISTS idx_entities_doc ON document_entities(canonical_id);
CREATE INDEX IF NOT EXISTS idx_entities_type ON document_entities(entity_type);
CREATE INDEX IF NOT EXISTS idx_entities_name ON document_entities(entity_name);
CREATE INDEX IF NOT EXISTS idx_entities_role ON document_entities(entity_role);

-- Entity attributes (flexible key-value for entity-specific data)
CREATE TABLE IF NOT EXISTS entity_attributes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    entity_id INTEGER NOT NULL,
    attribute_name TEXT NOT NULL,
    attribute_value TEXT,

    FOREIGN KEY (entity_id) REFERENCES document_entities(id) ON DELETE CASCADE,
    UNIQUE(entity_id, attribute_name)
);

CREATE INDEX IF NOT EXISTS idx_attributes_entity ON entity_attributes(entity_id);

-- ============================================================================
-- PARTICIPANTS (Universal across all document types)
-- ============================================================================

CREATE TABLE IF NOT EXISTS document_participants (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    canonical_id TEXT NOT NULL,
    name TEXT NOT NULL,
    role TEXT NOT NULL,  -- author, recipient, witness, attorney, etc.
    email TEXT,
    organization TEXT,
    title TEXT,

    FOREIGN KEY (canonical_id) REFERENCES documents(canonical_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_participants_doc ON document_participants(canonical_id);
CREATE INDEX IF NOT EXISTS idx_participants_name ON document_participants(name);
CREATE INDEX IF NOT EXISTS idx_participants_role ON document_participants(role);
CREATE INDEX IF NOT EXISTS idx_participants_org ON document_participants(organization);

-- ============================================================================
-- COMMUNICATION-SPECIFIC METADATA
-- ============================================================================

CREATE TABLE IF NOT EXISTS communications (
    canonical_id TEXT PRIMARY KEY,
    from_address TEXT,
    subject TEXT,
    message_id TEXT,
    in_reply_to TEXT,

    -- Letter specific
    letterhead TEXT,
    salutation TEXT,
    closing TEXT,

    -- Fax specific
    fax_number TEXT,
    pages_sent INTEGER,
    transmission_time TEXT,

    FOREIGN KEY (canonical_id) REFERENCES documents(canonical_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_communications_from ON communications(from_address);
CREATE INDEX IF NOT EXISTS idx_communications_subject ON communications(subject);
CREATE INDEX IF NOT EXISTS idx_communications_message_id ON communications(message_id);

-- Communication recipients (to, cc, bcc)
CREATE TABLE IF NOT EXISTS communication_recipients (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    canonical_id TEXT NOT NULL,
    recipient_type TEXT NOT NULL,  -- to, cc, bcc
    address TEXT NOT NULL,

    FOREIGN KEY (canonical_id) REFERENCES communications(canonical_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_recipients_doc ON communication_recipients(canonical_id);
CREATE INDEX IF NOT EXISTS idx_recipients_address ON communication_recipients(address);

-- ============================================================================
-- LEGAL DOCUMENT METADATA
-- ============================================================================

CREATE TABLE IF NOT EXISTS legal_documents (
    canonical_id TEXT PRIMARY KEY,
    case_number TEXT,
    case_name TEXT,
    court TEXT,
    court_abbreviation TEXT,

    judge TEXT,
    magistrate TEXT,

    plaintiff TEXT,
    defendant TEXT,

    docket_number TEXT,
    filing_date TEXT,
    filed_by TEXT,

    case_type TEXT,  -- criminal, civil
    jurisdiction TEXT,  -- federal, state
    status TEXT,  -- active, closed, sealed

    FOREIGN KEY (canonical_id) REFERENCES documents(canonical_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_legal_case ON legal_documents(case_number);
CREATE INDEX IF NOT EXISTS idx_legal_court ON legal_documents(court);
CREATE INDEX IF NOT EXISTS idx_legal_date ON legal_documents(filing_date);

-- Legal document attorneys
CREATE TABLE IF NOT EXISTS legal_attorneys (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    canonical_id TEXT NOT NULL,
    name TEXT NOT NULL,
    role TEXT NOT NULL,  -- prosecutor, defense, plaintiff_counsel, etc.
    organization TEXT,
    bar_number TEXT,

    FOREIGN KEY (canonical_id) REFERENCES legal_documents(canonical_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_attorneys_doc ON legal_attorneys(canonical_id);
CREATE INDEX IF NOT EXISTS idx_attorneys_name ON legal_attorneys(name);

-- ============================================================================
-- FINANCIAL DOCUMENT METADATA
-- ============================================================================

CREATE TABLE IF NOT EXISTS financial_documents (
    canonical_id TEXT PRIMARY KEY,
    account_number TEXT,
    routing_number TEXT,

    total_amount REAL,
    currency TEXT DEFAULT 'USD',

    payer TEXT,
    payee TEXT,
    beneficiary TEXT,

    transaction_id TEXT,
    transaction_date TEXT,
    transaction_type TEXT,

    -- Invoice specific
    invoice_number TEXT,
    invoice_date TEXT,
    due_date TEXT,

    -- Bank statement
    statement_period_start TEXT,
    statement_period_end TEXT,
    beginning_balance REAL,
    ending_balance REAL,

    -- SAR specific
    sar_number TEXT,
    filing_institution TEXT,
    suspicious_activity_type TEXT,

    FOREIGN KEY (canonical_id) REFERENCES documents(canonical_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_financial_account ON financial_documents(account_number);
CREATE INDEX IF NOT EXISTS idx_financial_transaction ON financial_documents(transaction_id);
CREATE INDEX IF NOT EXISTS idx_financial_date ON financial_documents(transaction_date);

-- Financial line items (for invoices)
CREATE TABLE IF NOT EXISTS financial_line_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    canonical_id TEXT NOT NULL,
    line_number INTEGER,
    description TEXT,
    quantity REAL,
    rate REAL,
    amount REAL,

    FOREIGN KEY (canonical_id) REFERENCES financial_documents(canonical_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_line_items_doc ON financial_line_items(canonical_id);

-- ============================================================================
-- FLIGHT LOG METADATA
-- ============================================================================

CREATE TABLE IF NOT EXISTS flight_logs (
    canonical_id TEXT PRIMARY KEY,

    -- Aircraft
    tail_number TEXT,
    aircraft_type TEXT,
    aircraft_owner TEXT,

    flight_number TEXT,

    -- Route
    origin TEXT,
    destination TEXT,

    -- Schedule
    departure_date TEXT,
    departure_time TEXT,
    arrival_date TEXT,
    arrival_time TEXT,

    flight_hours REAL,
    fuel_consumed REAL,

    FOREIGN KEY (canonical_id) REFERENCES documents(canonical_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_flights_tail ON flight_logs(tail_number);
CREATE INDEX IF NOT EXISTS idx_flights_date ON flight_logs(departure_date);
CREATE INDEX IF NOT EXISTS idx_flights_route ON flight_logs(origin, destination);

-- Flight stops
CREATE TABLE IF NOT EXISTS flight_stops (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    canonical_id TEXT NOT NULL,
    stop_number INTEGER,
    airport_code TEXT,
    airport_name TEXT,

    FOREIGN KEY (canonical_id) REFERENCES flight_logs(canonical_id) ON DELETE CASCADE
);

-- Flight passengers
CREATE TABLE IF NOT EXISTS flight_passengers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    canonical_id TEXT NOT NULL,
    passenger_name TEXT NOT NULL,
    age INTEGER,
    notes TEXT,

    FOREIGN KEY (canonical_id) REFERENCES flight_logs(canonical_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_flight_passengers_doc ON flight_passengers(canonical_id);
CREATE INDEX IF NOT EXISTS idx_flight_passengers_name ON flight_passengers(passenger_name);

-- Flight crew
CREATE TABLE IF NOT EXISTS flight_crew (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    canonical_id TEXT NOT NULL,
    crew_name TEXT NOT NULL,
    role TEXT,  -- captain, first_officer, flight_attendant

    FOREIGN KEY (canonical_id) REFERENCES flight_logs(canonical_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_flight_crew_doc ON flight_crew(canonical_id);

-- ============================================================================
-- INVESTIGATIVE DOCUMENT METADATA
-- ============================================================================

CREATE TABLE IF NOT EXISTS investigative_documents (
    canonical_id TEXT PRIMARY KEY,
    agency TEXT,
    case_number TEXT,
    report_number TEXT,

    investigator_name TEXT,
    investigator_badge TEXT,
    investigator_agency TEXT,

    subject_name TEXT,
    subject_dob TEXT,

    incident_date TEXT,
    report_date TEXT,

    -- Witness statement
    witness_name TEXT,
    statement_date TEXT,
    sworn BOOLEAN,

    FOREIGN KEY (canonical_id) REFERENCES documents(canonical_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_investigative_agency ON investigative_documents(agency);
CREATE INDEX IF NOT EXISTS idx_investigative_case ON investigative_documents(case_number);
CREATE INDEX IF NOT EXISTS idx_investigative_subject ON investigative_documents(subject_name);

-- Evidence references
CREATE TABLE IF NOT EXISTS evidence_references (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    canonical_id TEXT NOT NULL,
    evidence_number TEXT NOT NULL,
    description TEXT,

    FOREIGN KEY (canonical_id) REFERENCES investigative_documents(canonical_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_evidence_doc ON evidence_references(canonical_id);
CREATE INDEX IF NOT EXISTS idx_evidence_number ON evidence_references(evidence_number);

-- Chain of custody
CREATE TABLE IF NOT EXISTS chain_of_custody (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    canonical_id TEXT NOT NULL,
    step_number INTEGER,
    collected_by TEXT,
    collected_date TEXT,
    transferred_to TEXT,
    transfer_date TEXT,
    notes TEXT,

    FOREIGN KEY (canonical_id) REFERENCES investigative_documents(canonical_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_custody_doc ON chain_of_custody(canonical_id);

-- ============================================================================
-- SOURCE TRACKING
-- ============================================================================

CREATE TABLE IF NOT EXISTS document_sources (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    canonical_id TEXT NOT NULL,
    source_name TEXT NOT NULL,
    collection TEXT,
    url TEXT,
    access_date TEXT,

    -- Source-specific identifiers
    bates_number TEXT,
    pages TEXT,
    page_range TEXT,
    pdf_file TEXT,
    exhibit_number TEXT,

    FOREIGN KEY (canonical_id) REFERENCES documents(canonical_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_sources_doc ON document_sources(canonical_id);
CREATE INDEX IF NOT EXISTS idx_sources_collection ON document_sources(collection);
CREATE INDEX IF NOT EXISTS idx_sources_bates ON document_sources(bates_number);

-- ============================================================================
-- DOCUMENT RELATIONSHIPS
-- ============================================================================

CREATE TABLE IF NOT EXISTS document_relationships (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_canonical_id TEXT NOT NULL,
    target_canonical_id TEXT NOT NULL,
    relationship_type TEXT NOT NULL,  -- reply_to, attachment_of, version_of, cited_in, etc.
    description TEXT,
    confidence REAL,

    FOREIGN KEY (source_canonical_id) REFERENCES documents(canonical_id) ON DELETE CASCADE,
    FOREIGN KEY (target_canonical_id) REFERENCES documents(canonical_id) ON DELETE CASCADE,
    CONSTRAINT valid_confidence CHECK (confidence IS NULL OR confidence BETWEEN 0.0 AND 1.0),
    UNIQUE(source_canonical_id, target_canonical_id, relationship_type)
);

CREATE INDEX IF NOT EXISTS idx_relationships_source ON document_relationships(source_canonical_id);
CREATE INDEX IF NOT EXISTS idx_relationships_target ON document_relationships(target_canonical_id);
CREATE INDEX IF NOT EXISTS idx_relationships_type ON document_relationships(relationship_type);

-- ============================================================================
-- TAGS
-- ============================================================================

CREATE TABLE IF NOT EXISTS document_tags (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    canonical_id TEXT NOT NULL,
    tag TEXT NOT NULL,

    FOREIGN KEY (canonical_id) REFERENCES documents(canonical_id) ON DELETE CASCADE,
    UNIQUE(canonical_id, tag)
);

CREATE INDEX IF NOT EXISTS idx_tags_doc ON document_tags(canonical_id);
CREATE INDEX IF NOT EXISTS idx_tags_tag ON document_tags(tag);

-- ============================================================================
-- PROCESSING LOGS
-- ============================================================================

CREATE TABLE IF NOT EXISTS processing_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    canonical_id TEXT NOT NULL,
    timestamp TEXT NOT NULL,
    step TEXT NOT NULL,
    status TEXT NOT NULL,  -- success, warning, error
    message TEXT,
    details TEXT,  -- JSON

    FOREIGN KEY (canonical_id) REFERENCES documents(canonical_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_logs_doc ON processing_logs(canonical_id);
CREATE INDEX IF NOT EXISTS idx_logs_status ON processing_logs(status);

-- ============================================================================
-- STATISTICS AND ANALYTICS
-- ============================================================================

-- Document type statistics (materialized view updated by triggers)
CREATE TABLE IF NOT EXISTS type_statistics (
    document_type TEXT PRIMARY KEY,
    total_count INTEGER DEFAULT 0,
    avg_confidence REAL,
    high_confidence_count INTEGER DEFAULT 0,  -- confidence >= 0.9
    medium_confidence_count INTEGER DEFAULT 0,  -- confidence 0.7-0.89
    low_confidence_count INTEGER DEFAULT 0,  -- confidence < 0.7
    last_updated TEXT
);

-- Entity statistics
CREATE TABLE IF NOT EXISTS entity_statistics (
    entity_name TEXT PRIMARY KEY,
    entity_type TEXT,
    total_mentions INTEGER DEFAULT 0,
    document_count INTEGER DEFAULT 0,
    first_seen TEXT,
    last_seen TEXT,
    last_updated TEXT
);

CREATE INDEX IF NOT EXISTS idx_entity_stats_type ON entity_statistics(entity_type);

-- ============================================================================
-- VIEWS FOR COMMON QUERIES
-- ============================================================================

-- Complete document view with all metadata
CREATE VIEW IF NOT EXISTS v_documents_complete AS
SELECT
    d.*,
    c.from_address,
    c.subject,
    l.case_number,
    l.case_name,
    l.court,
    f.total_amount,
    f.currency,
    fl.tail_number,
    fl.departure_date,
    i.agency,
    i.report_number
FROM documents d
LEFT JOIN communications c ON d.canonical_id = c.canonical_id
LEFT JOIN legal_documents l ON d.canonical_id = l.canonical_id
LEFT JOIN financial_documents f ON d.canonical_id = f.canonical_id
LEFT JOIN flight_logs fl ON d.canonical_id = fl.canonical_id
LEFT JOIN investigative_documents i ON d.canonical_id = i.canonical_id;

-- Documents needing manual review
CREATE VIEW IF NOT EXISTS v_needs_review AS
SELECT
    canonical_id,
    document_type,
    title,
    date,
    classification_confidence,
    ocr_quality,
    completeness
FROM documents
WHERE
    classification_confidence < 0.7
    OR ocr_quality = 'low'
    OR completeness IN ('partial', 'fragment')
    OR manually_reviewed = FALSE
ORDER BY classification_confidence ASC;

-- Entity co-occurrence (people appearing in same documents)
CREATE VIEW IF NOT EXISTS v_entity_cooccurrence AS
SELECT
    e1.entity_name AS entity1,
    e2.entity_name AS entity2,
    COUNT(DISTINCT e1.canonical_id) AS cooccurrence_count
FROM document_entities e1
JOIN document_entities e2
    ON e1.canonical_id = e2.canonical_id
    AND e1.entity_type = 'person'
    AND e2.entity_type = 'person'
    AND e1.entity_name < e2.entity_name
GROUP BY e1.entity_name, e2.entity_name
HAVING cooccurrence_count > 1
ORDER BY cooccurrence_count DESC;

-- Timeline view
CREATE VIEW IF NOT EXISTS v_timeline AS
SELECT
    date,
    document_type,
    COUNT(*) AS document_count
FROM documents
WHERE date IS NOT NULL
GROUP BY date, document_type
ORDER BY date;
