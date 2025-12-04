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
