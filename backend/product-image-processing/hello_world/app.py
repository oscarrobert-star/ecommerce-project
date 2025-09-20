import boto3
import os
import io
import urllib.parse
from PIL import Image, ImageOps

# Initialize the S3 client
s3_client = boto3.client("s3")

# Define sizes for product images (square ratio, web best practices)
SIZES = {
    "thumbnail": (150, 150),
    "medium": (800, 800),
    "large": (1200, 1200),
}

def lambda_handler(event, context):
    """
    Lambda triggered by S3 upload events.
    Resizes and optimizes product images for web usage (JPEG + WebP).
    """

    source_bucket = event["Records"][0]["s3"]["bucket"]["name"]
    object_key = urllib.parse.unquote_plus(event["Records"][0]["s3"]["object"]["key"], encoding="utf-8")
    print(f"Processing image: {object_key} from bucket: {source_bucket}")

    try:
        destination_bucket = os.environ["DESTINATION_BUCKET"]

        # Download the image
        image_obj = s3_client.get_object(Bucket=source_bucket, Key=object_key)
        image_data = image_obj["Body"].read()

        img = Image.open(io.BytesIO(image_data))

        # Ensure RGB mode (avoid issues with PNG with alpha, GIF, etc.)
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")

        # Iterate over defined sizes
        for size_name, dimensions in SIZES.items():
            temp_img = img.copy()

            # Resize with aspect ratio, fit within box
            temp_img.thumbnail(dimensions, Image.Resampling.LANCZOS)

            # ─── Save as Optimized JPEG ───
            jpeg_buffer = io.BytesIO()
            temp_img.save(jpeg_buffer, "JPEG", optimize=True, quality=85)  # quality ~ good balance
            jpeg_buffer.seek(0)

            file_name, _ = os.path.splitext(object_key)
            jpeg_key = f"{file_name}-{size_name}.jpg"

            s3_client.put_object(
                Bucket=destination_bucket,
                Key=jpeg_key,
                Body=jpeg_buffer,
                ContentType="image/jpeg",
            )
            print(f"Uploaded JPEG: {jpeg_key}")

            # ─── Save as WebP ───
            webp_buffer = io.BytesIO()
            temp_img.save(webp_buffer, "WEBP", quality=80, method=6)  # high compression, good quality
            webp_buffer.seek(0)

            webp_key = f"{file_name}-{size_name}.webp"

            s3_client.put_object(
                Bucket=destination_bucket,
                Key=webp_key,
                Body=webp_buffer,
                ContentType="image/webp",
            )
            print(f"Uploaded WebP: {webp_key}")

        return {
            "statusCode": 200,
            "body": f"Resized + optimized images (JPEG + WebP) uploaded for {object_key}"
        }

    except Exception as e:
        print(f"Error processing {object_key}: {e}")
        return {
            "statusCode": 500,
            "body": f"Error processing image {object_key}: {str(e)}"
        }
