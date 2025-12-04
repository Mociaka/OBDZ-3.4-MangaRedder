import os
from app import db
from sqlalchemy import text

def apply_db_optimizations(app):
    """Apply database optimizations from SQL script"""
    script_path = os.path.join(app.root_path, 'db_optimizations.sql')
    
    try:
        with open(script_path, 'r') as f:
            sql_script = f.read()
            
        with app.app_context():
            # Split script by semicolons to execute statements individually if needed, 
            # but SQLAlchemy's execute can often handle blocks. 
            # For safety with PL/PGSQL, we might need to be careful, but let's try executing as one block first
            # or split by specific delimiters if simple split fails.
            # Given the $$ syntax, simple splitting might break functions.
            # Let's try executing the whole thing.
            db.session.execute(text(sql_script))
            db.session.commit()
            print("Database optimizations applied successfully.")
            return True
    except Exception as e:
        print(f"Error applying DB optimizations: {e}")
        db.session.rollback()
        return False
