from pathlib import Path
from uuid import uuid4
import aiofiles
from fastapi import HTTPException, UploadFile

UPLOADS = Path("var/uploads")
MAX_BYTES = 5 * 1024 * 1024

async def save_image(file: UploadFile) -> str:
    try:
        data = await file.read(MAX_BYTES + 1)
        if len(data) > MAX_BYTES:
            raise HTTPException(413, "La imagen supera los 5 MB")
        signatures = {"image/png": (b"\x89PNG\r\n\x1a\n", ".png"), "image/jpeg": (b"\xff\xd8\xff", ".jpg")}
        expected = signatures.get(file.content_type)
        if expected is None or not data.startswith(expected[0]):
            raise HTTPException(415, "Necesito una imagen JPEG o PNG válida")
        filename = f"{uuid4().hex}{expected[1]}"
        UPLOADS.mkdir(parents=True, exist_ok=True)
        async with aiofiles.open(UPLOADS / filename, "wb") as stream:
            await stream.write(data)
        return filename
    finally:
        await file.close()
