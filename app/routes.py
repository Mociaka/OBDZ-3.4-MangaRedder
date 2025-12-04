from flask import render_template, request, redirect, url_for, jsonify
from app import db
from app.models import Manga, Chapter, Page
from app.utils import apply_db_optimizations
from flask import current_app as app

@app.route('/admin/optimize_db')
def optimize_db():
    """Apply database optimizations"""
    success = apply_db_optimizations(app)
    if success:
        return "Database optimizations applied successfully! <a href='/admin'>Back to Admin</a>"
    else:
        return "Error applying optimizations. Check logs. <a href='/admin'>Back to Admin</a>"

@app.route('/')
def index():
    manga_list = Manga.query.order_by(Manga.created_at.desc()).all()
    return render_template('index.html', manga_list=manga_list)


@app.route('/manga/<int:manga_id>')
def manga_detail(manga_id):
    manga = Manga.query.get_or_404(manga_id)
    chapters = Chapter.query.filter_by(manga_id=manga_id).order_by(Chapter.chapter_number).all()
    return render_template('manga_detail.html', manga=manga, chapters=chapters)


@app.route('/reader/<int:chapter_id>')
def reader(chapter_id):
    chapter = Chapter.query.get_or_404(chapter_id)
    pages = Page.query.filter_by(chapter_id=chapter_id).order_by(Page.page_number).all()

    all_chapters = Chapter.query.filter_by(manga_id=chapter.manga_id).order_by(Chapter.chapter_number).all()

    current_index = next((i for i, ch in enumerate(all_chapters) if ch.id == chapter_id), None)
    prev_chapter = all_chapters[current_index - 1] if current_index and current_index > 0 else None
    next_chapter = all_chapters[current_index + 1] if current_index is not None and current_index < len(all_chapters) - 1 else None
    
    return render_template('reader.html', 
                          chapter=chapter, 
                          pages=pages,
                          prev_chapter=prev_chapter,
                          next_chapter=next_chapter)


@app.route('/admin')
def admin():
    manga_list = Manga.query.order_by(Manga.title).all()
    return render_template('admin.html', manga_list=manga_list)


@app.route('/admin/add_manga', methods=['POST'])
def add_manga():
    title = request.form.get('title')
    description = request.form.get('description')
    cover_url = request.form.get('cover_url')
    author = request.form.get('author')
    
    manga = Manga(
        title=title,
        description=description,
        cover_url=cover_url,
        author=author
    )
    
    db.session.add(manga)
    db.session.commit()
    
    return redirect(url_for('admin'))


@app.route('/admin/add_chapter', methods=['POST'])
def add_chapter():
    manga_id = request.form.get('manga_id')
    chapter_number = request.form.get('chapter_number')
    title = request.form.get('title')
    
    chapter = Chapter(
        manga_id=manga_id,
        chapter_number=float(chapter_number),
        title=title
    )
    
    db.session.add(chapter)
    db.session.commit()
    
    return redirect(url_for('admin'))


@app.route('/admin/add_pages', methods=['POST'])
def add_pages():
    chapter_id = request.form.get('chapter_id')
    page_urls = request.form.get('page_urls')
    urls = [url.strip() for url in page_urls.split('\n') if url.strip()]
    
    for i, url in enumerate(urls, start=1):
        page = Page(
            chapter_id=chapter_id,
            page_number=i,
            image_url=url
        )
        db.session.add(page)
    
    db.session.commit()
    
    return redirect(url_for('admin'))


@app.route('/admin/get_chapters/<int:manga_id>')
def get_chapters(manga_id):
    chapters = Chapter.query.filter_by(manga_id=manga_id).order_by(Chapter.chapter_number).all()
    return jsonify([{
        'id': ch.id,
        'chapter_number': ch.chapter_number,
        'title': ch.title
    } for ch in chapters])
