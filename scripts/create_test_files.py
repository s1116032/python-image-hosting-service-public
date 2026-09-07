import base64
from pathlib import Path


# 1x1 transparent PNG
PNG_BASE64 = (
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJ"
    "AAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=="
)


def main():
    png_bytes = base64.b64decode(PNG_BASE64)

    valid_path = Path("valid.png")
    valid_path.write_bytes(png_bytes)

    fake_path = Path("fake_image.png")
    fake_path.write_text("This is not a real image.")

    print("Created test files:")
    print(f"- {valid_path.resolve()}")
    print(f"- {fake_path.resolve()}")


if __name__ == "__main__":
    main()
