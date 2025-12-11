-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Trigger for Manga table
DROP TRIGGER IF EXISTS update_manga_updated_at ON manga;
CREATE TRIGGER update_manga_updated_at
    BEFORE UPDATE ON manga
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Trigger for Chapters table
DROP TRIGGER IF EXISTS update_chapters_updated_at ON chapters;
CREATE TRIGGER update_chapters_updated_at
    BEFORE UPDATE ON chapters
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- View for Manga Statistics
CREATE OR REPLACE VIEW manga_stats AS
SELECT 
    m.id,
    m.title,
    COUNT(DISTINCT c.id) as total_chapters,
    COUNT(DISTINCT p.id) as total_pages,
    MAX(c.created_at) as last_chapter_date
FROM manga m
LEFT JOIN chapters c ON m.id = c.manga_id
LEFT JOIN pages p ON c.id = p.chapter_id
GROUP BY m.id, m.title;

-- Full Text Search Index
CREATE INDEX IF NOT EXISTS idx_manga_title_search ON manga USING gin(to_tsvector('english', title));
CREATE INDEX IF NOT EXISTS idx_manga_description_search ON manga USING gin(to_tsvector('english', COALESCE(description, '')));

-- Audit Logs Table
CREATE TABLE IF NOT EXISTS audit_logs (
    id SERIAL PRIMARY KEY,
    table_name VARCHAR(50),
    operation VARCHAR(10),
    record_id INTEGER,
    old_data JSONB,
    new_data JSONB,
    changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Function to log changes
CREATE OR REPLACE FUNCTION log_manga_changes()
RETURNS TRIGGER AS $$
BEGIN
    IF (TG_OP = 'DELETE') THEN
        INSERT INTO audit_logs (table_name, operation, record_id, old_data)
        VALUES ('manga', 'DELETE', OLD.id, row_to_json(OLD));
        RETURN OLD;
    ELSIF (TG_OP = 'UPDATE') THEN
        INSERT INTO audit_logs (table_name, operation, record_id, old_data, new_data)
        VALUES ('manga', 'UPDATE', NEW.id, row_to_json(OLD), row_to_json(NEW));
        RETURN NEW;
    ELSIF (TG_OP = 'INSERT') THEN
        INSERT INTO audit_logs (table_name, operation, record_id, new_data)
        VALUES ('manga', 'INSERT', NEW.id, row_to_json(NEW));
        RETURN NEW;
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

-- Trigger for audit
DROP TRIGGER IF EXISTS audit_manga_changes ON manga;
CREATE TRIGGER audit_manga_changes
AFTER INSERT OR UPDATE OR DELETE ON manga
FOR EACH ROW EXECUTE FUNCTION log_manga_changes();

-- Add page_count to chapters if not exists
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='chapters' AND column_name='page_count') THEN
        ALTER TABLE chapters ADD COLUMN page_count INTEGER DEFAULT 0;
    END IF;
END $$;

-- Function to update page count
CREATE OR REPLACE FUNCTION update_chapter_page_count()
RETURNS TRIGGER AS $$
BEGIN
    IF (TG_OP = 'INSERT') THEN
        UPDATE chapters SET page_count = page_count + 1 WHERE id = NEW.chapter_id;
        RETURN NEW;
    ELSIF (TG_OP = 'DELETE') THEN
        UPDATE chapters SET page_count = page_count - 1 WHERE id = OLD.chapter_id;
        RETURN OLD;
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

-- Trigger for page count
DROP TRIGGER IF EXISTS update_page_count_trigger ON pages;
CREATE TRIGGER update_page_count_trigger
AFTER INSERT OR DELETE ON pages
FOR EACH ROW EXECUTE FUNCTION update_chapter_page_count();

-- Function to validate chapter number
CREATE OR REPLACE FUNCTION validate_chapter_number()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.chapter_number < 0 THEN
        RAISE EXCEPTION 'Chapter number must be non-negative';
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger for validation
DROP TRIGGER IF EXISTS check_chapter_number_trigger ON chapters;
CREATE TRIGGER check_chapter_number_trigger
BEFORE INSERT OR UPDATE ON chapters
FOR EACH ROW EXECUTE FUNCTION validate_chapter_number();
