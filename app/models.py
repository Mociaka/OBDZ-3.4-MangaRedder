from app import db
from datetime import datetime

class Manga(db.Model):
    __tablename__ = 'manga'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    cover_url = db.Column(db.String(500))
    author = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    chapters = db.relationship('Chapter', backref='manga', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Manga {self.title}>'


class Chapter(db.Model):
    __tablename__ = 'chapters'
    
    id = db.Column(db.Integer, primary_key=True)
    manga_id = db.Column(db.Integer, db.ForeignKey('manga.id'), nullable=False)
    chapter_number = db.Column(db.Float, nullable=False)
    title = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    pages = db.relationship('Page', backref='chapter', lazy=True, cascade='all, delete-orphan', order_by='Page.page_number')
    
    def __repr__(self):
        return f'<Chapter {self.chapter_number} - {self.title}>'


class Page(db.Model):
    __tablename__ = 'pages'
    
    id = db.Column(db.Integer, primary_key=True)
    chapter_id = db.Column(db.Integer, db.ForeignKey('chapters.id'), nullable=False)
    page_number = db.Column(db.Integer, nullable=False)
    image_url = db.Column(db.String(500), nullable=False)
    
    def __repr__(self):
        return f'<Page {self.page_number}>'
