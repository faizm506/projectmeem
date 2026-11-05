"""Safe image uploads: prove it is a real image, shrink it and re-encode it (this strips hidden data and scripts)."""
import uuid
from io import BytesIO

from django import forms
from django.core.files.base import ContentFile
from django.core.files.uploadedfile import UploadedFile
from PIL import Image, ImageOps, UnidentifiedImageError

ALLOWED = {"JPEG": "jpg", "PNG": "png", "WEBP": "webp"}
MAX_BYTES = 3 * 1024 * 1024
MAX_PIXELS = 25_000_000
MAX_SIDE = 2000


def sanitize_image(upload, max_side=MAX_SIDE):
    """Returns a clean ContentFile, or raises ValidationError. Existing stored files and empty values pass through."""
    if not isinstance(upload, UploadedFile):
        return upload
    if upload.size > MAX_BYTES:
        raise forms.ValidationError("Please upload an image smaller than 3 MB.")
    try:
        probe = Image.open(upload)
        probe.verify()
        upload.seek(0)
        img = Image.open(upload)
        fmt = img.format
        if fmt not in ALLOWED:
            raise forms.ValidationError("Please upload a JPG, PNG or WebP image.")
        if img.width * img.height > MAX_PIXELS:
            raise forms.ValidationError("That image is too large. Please resize it and try again.")
        img = ImageOps.exif_transpose(img)
        img.thumbnail((max_side, max_side))
        if fmt == "JPEG" and img.mode != "RGB":
            img = img.convert("RGB")
        elif img.mode not in ("RGB", "RGBA"):
            img = img.convert("RGBA")
        buf = BytesIO()
        img.save(buf, format=fmt, **({"quality": 86, "optimize": True} if fmt == "JPEG" else {}))
    except forms.ValidationError:
        raise
    except (UnidentifiedImageError, OSError, ValueError, Image.DecompressionBombError):
        raise forms.ValidationError("That file is not a valid image.")
    return ContentFile(buf.getvalue(), name=f"{uuid.uuid4().hex}.{ALLOWED[fmt]}")
