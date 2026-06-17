from fastapi import FastAPI, Request, Form, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import create_engine, String, Text, select
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker, Session

# ==========================================
# 1. DATABASE SETUP
# ==========================================
engine = create_engine("sqlite:///blog_app.db", connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


class BlogPost(Base):
    __tablename__ = "blog_posts"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(100))
    content: Mapped[str] = mapped_column(Text)


Base.metadata.create_all(bind=engine)

# ==========================================
# 2. FASTAPI & JINJA2 SETUP
# ==========================================
app = FastAPI()
templates = Jinja2Templates(directory="frontend")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ==========================================
# 3. ROUTES (HTML PAGES)
# ==========================================

# --- READ (Homepage: list all posts) ---
@app.get("/", response_class=HTMLResponse)
def read_posts(request: Request, db: Session = Depends(get_db)):
    posts = db.scalars(select(BlogPost)).all()
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={"posts": posts},
    )


# --- CREATE ---
@app.get("/create", response_class=HTMLResponse)
def create_post_page(request: Request):
    return templates.TemplateResponse(request=request, name="create.html")


@app.post("/create")
def create_post(
    title: str = Form(...),
    content: str = Form(...),
    db: Session = Depends(get_db),
):
    new_post = BlogPost(title=title, content=content)
    db.add(new_post)
    db.commit()
    return RedirectResponse(url="/", status_code=303)


# --- UPDATE ---
@app.get("/update/{post_id}", response_class=HTMLResponse)
def update_post_page(
    request: Request,
    post_id: int,
    db: Session = Depends(get_db),
):
    post = db.get(BlogPost, post_id)
    return templates.TemplateResponse(
        request=request,
        name="update.html",
        context={"post": post},
    )


@app.post("/update/{post_id}")
def update_post(
    post_id: int,
    title: str = Form(...),
    content: str = Form(...),
    db: Session = Depends(get_db),
):
    post = db.get(BlogPost, post_id)
    if post:
        post.title = title
        post.content = content
        db.commit()
    return RedirectResponse(url="/", status_code=303)

@app.get("/delete-confirm/{post_id}", response_class=HTMLResponse)
def delete_confirm(request: Request, post_id: int, db: Session = Depends(get_db)):
    post = db.get(BlogPost, post_id)
    return templates.TemplateResponse(
        request=request,
        name="delete.html",
        context={"post": post},
    )


# --- DELETE ---
@app.get("/delete/{post_id}")
def delete_post(post_id: int, db: Session = Depends(get_db)):
    post = db.get(BlogPost, post_id)
    if post:
        db.delete(post)
        db.commit()
    return RedirectResponse(url="/", status_code=303)