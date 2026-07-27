import io
import uuid

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import StreamingResponse
from minio import Minio
from minio.error import S3Error

from app.core.config import settings

router = APIRouter(prefix="/api/upload", tags=["upload"])

MAX_UPLOAD_BYTES = 100 * 1024 * 1024  # 100MB — legal docs/photos, not SCORM-sized bundles


def get_client() -> Minio:
    return Minio(
        settings.MINIO_ENDPOINT,
        access_key=settings.MINIO_ACCESS_KEY,
        secret_key=settings.MINIO_SECRET_KEY,
        secure=settings.MINIO_SECURE,
    )


def ensure_bucket() -> None:
    client = get_client()
    if not client.bucket_exists(settings.MINIO_BUCKET):
        client.make_bucket(settings.MINIO_BUCKET)


def store_object(content: bytes, original_filename: str, content_type: str | None) -> str:
    """Uploads bytes under a random object name (extension preserved) and returns that name."""
    ensure_bucket()
    ext = ("." + original_filename.rsplit(".", 1)[-1]) if "." in original_filename else ""
    object_name = f"{uuid.uuid4()}{ext}"
    get_client().put_object(
        settings.MINIO_BUCKET,
        object_name,
        io.BytesIO(content),
        length=len(content),
        content_type=content_type or "application/octet-stream",
    )
    return object_name


def get_object_bytes(object_name: str) -> bytes:
    """Fetches an object's raw bytes — used by the PDF renderer to embed
    signature images as data URIs rather than having WeasyPrint fetch them
    back over HTTP through the (authenticated) proxy endpoint below."""
    response = get_client().get_object(settings.MINIO_BUCKET, object_name)
    try:
        return response.read()
    finally:
        response.close()
        response.release_conn()


# Sync `def` on purpose: FastAPI runs sync route functions in a worker thread,
# which keeps this endpoint's blocking MinIO I/O off the event loop — matches
# the LMS backend's convention for its equivalent proxy endpoint.
@router.get("/files/{object_name:path}")
def get_file(object_name: str):
    # MinIO's Docker-internal hostname isn't reachable from the browser, so
    # files are proxied through the backend rather than redirected to a
    # presigned MinIO URL.
    try:
        response = get_client().get_object(settings.MINIO_BUCKET, object_name)
    except S3Error:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "File not found")

    return StreamingResponse(
        response.stream(32 * 1024),
        media_type=response.headers.get("content-type", "application/octet-stream"),
    )
