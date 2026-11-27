
from pathlib import Path
import logging
import zipfile

import requests


GTFS_URL = (
    "https://www.wienerlinien.at/"
    "ogd_realtime/doku/ogd/gtfs/gtfs.zip"
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_DATA_DIR = PROJECT_ROOT / "data" / "raw"
ZIP_PATH = RAW_DATA_DIR / "wiener_linien_gtfs.zip"
EXTRACT_DIR = RAW_DATA_DIR / "gtfs"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

logger = logging.getLogger(__name__)


def download_gtfs():
    """Download the official Wiener Linien GTFS dataset."""

    RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)

    logger.info("Downloading Wiener Linien GTFS dataset...")

    temp_path = ZIP_PATH.with_suffix(".tmp")

    try:
        with requests.get(
            GTFS_URL, stream=True, timeout=(15, 120)
        ) as response:
            response.raise_for_status()

            total_size = int(
                response.headers.get("Content-Length", 0)
            )
            downloaded = 0

            if total_size:
                logger.info(
                    "Total dataset size: %.2f MB",
                    total_size / (1024 * 1024)
                )

            with temp_path.open("wb") as file:
                for chunk in response.iter_content(chunk_size=65536):
                    if chunk:
                        file.write(chunk)
                        downloaded += len(chunk)

                        downloaded_mb = downloaded / (1024 * 1024)

                        if total_size:
                            percentage = downloaded / total_size * 100

                            print(
                                f"\rDownloaded: {downloaded_mb:.2f} MB "
                                f"({percentage:.1f}%)",
                                end="",
                                flush=True
                            )
                        else:
                            print(
                                f"\rDownloaded: {downloaded_mb:.2f} MB",
                                end="",
                                flush=True
                            )

            print()

        if not zipfile.is_zipfile(temp_path):
            raise ValueError(
                "Downloaded file is not a valid ZIP archive."
            )

        temp_path.replace(ZIP_PATH)

    finally:
        temp_path.unlink(missing_ok=True)

    logger.info("Dataset downloaded successfully: %s", ZIP_PATH)


def extract_gtfs():
    """Extract the downloaded GTFS archive."""

    EXTRACT_DIR.mkdir(parents=True, exist_ok=True)

    logger.info("Extracting GTFS files...")

    with zipfile.ZipFile(ZIP_PATH, "r") as archive:

        for member in archive.infolist():
            target = (EXTRACT_DIR / member.filename).resolve()

            if not target.is_relative_to(EXTRACT_DIR.resolve()):
                raise ValueError("Unsafe ZIP archive path.")

        archive.extractall(EXTRACT_DIR)

    logger.info("Extraction completed successfully.")

    for file in sorted(EXTRACT_DIR.iterdir()):
        if file.is_file():
            logger.info("Extracted: %s", file.name)


def main():
    download_gtfs()
    extract_gtfs()

    logger.info("GTFS ingestion completed.")


if __name__ == "__main__":
    main()
