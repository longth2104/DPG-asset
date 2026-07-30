from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import assets, auth, companies, council_members, requests, settings, upload, users

app = FastAPI(
    title="Đạt Phương Asset Management",
    version="0.1.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

# Wildcard origin + credentials is only safe here because auth is a Bearer
# header, never a cookie — no credentialed browser request actually needs
# this to satisfy the CORS spec. Matches the LMS backend's convention.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(assets.router)
app.include_router(requests.router)
app.include_router(upload.router)
app.include_router(settings.router)
app.include_router(users.router)
app.include_router(companies.router)
app.include_router(council_members.router)


@app.get("/api/health", tags=["health"])
def health():
    return {"status": "ok"}
