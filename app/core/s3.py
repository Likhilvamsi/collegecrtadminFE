import boto3
import uuid
from fastapi import UploadFile
from app.core.config import settings

s3_client = boto3.client(
    "s3",
    aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
    aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
    region_name=settings.AWS_REGION,
)

async def upload_file_to_s3(
    file: UploadFile,
    folder: str,
):
    # Read file bytes
    file_bytes = await file.read()

    key = f"{folder}/{uuid.uuid4()}_{file.filename}"

    # Upload to S3 (INLINE VIEW)
    s3_client.put_object(
        Bucket=settings.AWS_S3_BUCKET,
        Key=key,
        Body=file_bytes,
        ContentType=file.content_type,
        ContentDisposition="inline",  # 👈 IMPORTANT
    )

    file_url = (
        f"https://{settings.AWS_S3_BUCKET}.s3."
        f"{settings.AWS_REGION}.amazonaws.com/{key}"
    )

    return {
        "file_url": file_url,
        "file_size": len(file_bytes),
        "content_type": file.content_type,
        "s3_key": key,
    }
