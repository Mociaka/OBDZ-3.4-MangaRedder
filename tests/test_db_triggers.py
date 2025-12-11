import pytest
import psycopg2
from psycopg2.extras import RealDictCursor
import os

# Configuration
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "manga_db")
DB_USER = os.getenv("DB_USER", "manga_user")
DB_PASSWORD = os.getenv("DB_PASSWORD", "manga_password")

@pytest.fixture(scope="module")
def db_conn():
    """Create a database connection."""
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )
        conn.autocommit = False
        
        # Apply optimizations
        try:
            with conn.cursor() as cur:
                # Read SQL file
                sql_path = os.path.join(os.path.dirname(__file__), '..', 'app', 'db_optimizations.sql')
                with open(sql_path, 'r') as f:
                    sql_content = f.read()
                cur.execute(sql_content)
                conn.commit()
        except Exception as e:
            print(f"Failed to apply optimizations: {e}")
            conn.rollback()
            # We might continue if they were already applied, or fail. 
            # For now let's assume if it fails it might be because of duplicate objects if not handled by IF NOT EXISTS
            # But our SQL uses OR REPLACE and IF NOT EXISTS, so it should be fine.
        
        yield conn
        conn.rollback()
        conn.close()
    except Exception as e:
        pytest.skip(f"Database connection failed: {e}")

@pytest.fixture
def cursor(db_conn):
    """Create a cursor for executing queries."""
    cur = db_conn.cursor(cursor_factory=RealDictCursor)
    yield cur
    db_conn.rollback() # Rollback after each test to keep DB clean

def test_audit_log_trigger(cursor):
    """Test that inserting a manga creates an audit log entry."""
    # Insert a manga
    cursor.execute("""
        INSERT INTO manga (title, description, author)
        VALUES ('Test Manga', 'Description', 'Author')
        RETURNING id;
    """)
    manga_id = cursor.fetchone()['id']
    
    # Check audit log
    cursor.execute("""
        SELECT * FROM audit_logs 
        WHERE table_name = 'manga' AND record_id = %s AND operation = 'INSERT';
    """, (manga_id,))
    log = cursor.fetchone()
    
    assert log is not None
    assert log['operation'] == 'INSERT'
    assert log['new_data']['title'] == 'Test Manga'

def test_page_count_trigger(cursor):
    """Test that inserting pages updates the chapter page count."""
    # Insert manga and chapter
    cursor.execute("INSERT INTO manga (title) VALUES ('Count Manga') RETURNING id;")
    manga_id = cursor.fetchone()['id']
    
    cursor.execute("""
        INSERT INTO chapters (manga_id, chapter_number, title)
        VALUES (%s, 1, 'Chapter 1')
        RETURNING id;
    """, (manga_id,))
    chapter_id = cursor.fetchone()['id']
    
    # Verify initial count is 0
    cursor.execute("SELECT page_count FROM chapters WHERE id = %s;", (chapter_id,))
    assert cursor.fetchone()['page_count'] == 0
    
    # Insert a page
    cursor.execute("""
        INSERT INTO pages (chapter_id, page_number, image_url)
        VALUES (%s, 1, 'http://example.com/1.jpg');
    """, (chapter_id,))
    
    # Verify count is 1
    cursor.execute("SELECT page_count FROM chapters WHERE id = %s;", (chapter_id,))
    assert cursor.fetchone()['page_count'] == 1
    
    # Delete the page
    cursor.execute("DELETE FROM pages WHERE chapter_id = %s AND page_number = 1;", (chapter_id,))
    
    # Verify count is 0
    cursor.execute("SELECT page_count FROM chapters WHERE id = %s;", (chapter_id,))
    assert cursor.fetchone()['page_count'] == 0

def test_chapter_number_validation(cursor):
    """Test that negative chapter numbers are rejected."""
    cursor.execute("INSERT INTO manga (title) VALUES ('Valid Manga') RETURNING id;")
    manga_id = cursor.fetchone()['id']
    
    with pytest.raises(psycopg2.errors.RaiseException) as excinfo:
        cursor.execute("""
            INSERT INTO chapters (manga_id, chapter_number, title)
            VALUES (%s, -1, 'Negative Chapter');
        """, (manga_id,))
    
    assert "Chapter number must be non-negative" in str(excinfo.value)
