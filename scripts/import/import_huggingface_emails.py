#!/usr/bin/env python3
"""
Import Epstein emails from Hugging Face dataset.

Dataset: tensonaut/EPSTEIN_FILES_20K
URL: https://huggingface.co/datasets/tensonaut/EPSTEIN_FILES_20K

This script downloads the dataset and converts it to the project's email format.
"""

import json
import logging
import re
from datetime import datetime
from pathlib import Path
from typing import Any

from datasets import load_dataset


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("import_huggingface_emails.log"), logging.StreamHandler()],
)
logger = logging.getLogger(__name__)

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent.parent
OUTPUT_DIR = PROJECT_ROOT / "data" / "sources" / "house_oversight_nov2025" / "emails" / "imported"
EMAILS_DIR = OUTPUT_DIR / "emails"
ERROR_LOG = OUTPUT_DIR / "import_errors.log"

# Ensure directories exist
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
EMAILS_DIR.mkdir(parents=True, exist_ok=True)


class EmailImporter:
    """Import and convert Hugging Face email dataset to project format."""

    def __init__(self):
        """Initialize importer with statistics tracking."""
        self.stats = {
            "total_records": 0,
            "successful_imports": 0,
            "parsing_errors": 0,
            "skipped_records": 0,
            "emails_with_sender": 0,
            "emails_with_recipients": 0,
            "unique_email_addresses": set(),
            "date_range": {"earliest": None, "latest": None},
        }
        self.email_index = []
        self.error_log = []

    def extract_email_name(self, email_string: str | None) -> dict[str, str | None]:
        """Extract name and email from string like 'John Doe <john@example.com>'.

        Args:
            email_string: String containing email and optional name

        Returns:
            Dict with 'name' and 'email' keys
        """
        if not email_string or not isinstance(email_string, str):
            return {"name": None, "email": None}

        email_string = email_string.strip()

        # Pattern: Name <email@domain.com>
        match = re.match(r"^(.*?)\s*<([^>]+)>$", email_string)
        if match:
            name = match.group(1).strip().strip("\"'") or None
            email = match.group(2).strip()
            return {"name": name, "email": email}

        # Just email address
        if "@" in email_string:
            return {"name": None, "email": email_string}

        # Just a name or invalid
        return {"name": email_string if email_string else None, "email": None}

    def parse_date(self, date_str: str | None) -> str | None:
        """Parse date string to ISO format.

        Args:
            date_str: Date string in various formats

        Returns:
            ISO format date string or None
        """
        if not date_str or not isinstance(date_str, str):
            return None

        # Try common date formats
        date_formats = [
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d",
            "%m/%d/%Y %H:%M:%S",
            "%m/%d/%Y",
            "%d %b %Y %H:%M:%S",
            "%a, %d %b %Y %H:%M:%S %z",
        ]

        for fmt in date_formats:
            try:
                dt = datetime.strptime(date_str.strip(), fmt)
                return dt.isoformat()
            except ValueError:
                continue

        # If no format matches, log and return None
        logger.debug(f"Could not parse date: {date_str}")
        return None

    def update_date_range(self, date_str: str | None) -> None:
        """Update earliest/latest date statistics.

        Args:
            date_str: ISO format date string
        """
        if not date_str:
            return

        if self.stats["date_range"]["earliest"] is None:
            self.stats["date_range"]["earliest"] = date_str
            self.stats["date_range"]["latest"] = date_str
        else:
            self.stats["date_range"]["earliest"] = min(
                self.stats["date_range"]["earliest"], date_str
            )
            self.stats["date_range"]["latest"] = max(self.stats["date_range"]["latest"], date_str)

    def convert_record(self, record: dict[str, Any], index: int) -> dict[str, Any] | None:
        """Convert Hugging Face record to project email format.

        Args:
            record: Raw record from dataset
            index: Record index for ID generation

        Returns:
            Converted email dict or None if conversion fails
        """
        try:
            # Generate email ID from GUID or index
            guid = record.get("guid", "").strip()
            email_id = guid if guid else f"hf_{index:06d}"

            # Parse sender
            sender_raw = record.get("sender", "") or record.get("from", "")
            sender = self.extract_email_name(sender_raw)
            if sender["email"]:
                self.stats["emails_with_sender"] += 1
                self.stats["unique_email_addresses"].add(sender["email"])

            # Parse recipients (assuming comma-separated)
            recipients = []
            recipients_raw = record.get("recipients", "") or record.get("to", "")
            if recipients_raw and isinstance(recipients_raw, str):
                for recipient_str in recipients_raw.split(","):
                    recipient = self.extract_email_name(recipient_str)
                    if recipient["email"]:
                        recipients.append(recipient)
                        self.stats["unique_email_addresses"].add(recipient["email"])
                if recipients:
                    self.stats["emails_with_recipients"] += 1

            # Parse date
            date_raw = record.get("timestamp") or record.get("date")
            date = self.parse_date(date_raw)
            if date:
                self.update_date_range(date)

            # Extract subject and body
            subject = (record.get("subject", "") or "").strip() or None
            body = (record.get("body", "") or record.get("text", "") or "").strip() or None

            # Build email object
            email = {
                "email_id": email_id,
                "source": "huggingface:tensonaut/EPSTEIN_FILES_20K",
                "sender": sender,
                "recipients": recipients,
                "subject": subject,
                "date": date,
                "body": body,
                "metadata": {
                    "message_flags": record.get("message_flags"),
                    "guid": guid or None,
                    "import_date": datetime.now().isoformat(),
                    "huggingface_index": index,
                },
            }

            return email

        except Exception as e:
            error_msg = f"Error converting record {index}: {e!s}"
            logger.error(error_msg)
            self.error_log.append(
                {
                    "index": index,
                    "error": str(e),
                    "record": str(record)[:200],  # Truncate for logging
                }
            )
            return None

    def save_email(self, email: dict[str, Any]) -> bool:
        """Save individual email to JSON file.

        Args:
            email: Email dict to save

        Returns:
            True if saved successfully
        """
        try:
            email_id = email["email_id"]
            # Sanitize filename
            safe_id = re.sub(r"[^\w\-]", "_", email_id)
            file_path = EMAILS_DIR / f"{safe_id}.json"

            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(email, f, indent=2, ensure_ascii=False)

            # Add to index
            self.email_index.append(
                {
                    "email_id": email_id,
                    "file": f"emails/{safe_id}.json",
                    "subject": email.get("subject"),
                    "date": email.get("date"),
                    "sender": email.get("sender", {}).get("email"),
                }
            )

            return True

        except Exception as e:
            logger.error(f"Error saving email {email.get('email_id')}: {e}")
            return False

    def save_metadata(self) -> None:
        """Save import metadata and index files."""
        # Convert set to list for JSON serialization
        unique_emails_list = sorted(self.stats["unique_email_addresses"])

        metadata = {
            "import_date": datetime.now().isoformat(),
            "source_dataset": "huggingface:tensonaut/EPSTEIN_FILES_20K",
            "statistics": {
                "total_records": self.stats["total_records"],
                "successful_imports": self.stats["successful_imports"],
                "parsing_errors": self.stats["parsing_errors"],
                "skipped_records": self.stats["skipped_records"],
                "emails_with_sender": self.stats["emails_with_sender"],
                "emails_with_recipients": self.stats["emails_with_recipients"],
                "unique_email_addresses_count": len(unique_emails_list),
                "date_range": self.stats["date_range"],
            },
            "unique_email_addresses": unique_emails_list,
        }

        # Save metadata
        metadata_path = OUTPUT_DIR / "import_metadata.json"
        with open(metadata_path, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
        logger.info(f"Saved metadata to {metadata_path}")

        # Save email index
        index_path = OUTPUT_DIR / "email_index.json"
        with open(index_path, "w", encoding="utf-8") as f:
            json.dump(self.email_index, f, indent=2, ensure_ascii=False)
        logger.info(f"Saved email index to {index_path}")

        # Save error log if there are errors
        if self.error_log:
            with open(ERROR_LOG, "w", encoding="utf-8") as f:
                json.dump(self.error_log, f, indent=2, ensure_ascii=False)
            logger.warning(f"Saved {len(self.error_log)} errors to {ERROR_LOG}")

    def run(self) -> None:
        """Execute the import process."""
        logger.info("Starting Hugging Face email dataset import...")
        logger.info(f"Output directory: {OUTPUT_DIR}")

        # Load dataset
        logger.info("Loading dataset from Hugging Face...")
        try:
            dataset = load_dataset("tensonaut/EPSTEIN_FILES_20K", split="train")
            logger.info(f"Loaded {len(dataset)} records from dataset")
        except Exception as e:
            logger.error(f"Failed to load dataset: {e}")
            raise

        # Process records
        self.stats["total_records"] = len(dataset)
        logger.info(f"Processing {self.stats['total_records']} records...")

        for idx, record in enumerate(dataset):
            if idx % 1000 == 0:
                logger.info(f"Processing record {idx}/{self.stats['total_records']}...")

            # Convert record
            email = self.convert_record(record, idx)
            if email is None:
                self.stats["parsing_errors"] += 1
                continue

            # Skip if no meaningful content
            if not email.get("body") and not email.get("subject"):
                self.stats["skipped_records"] += 1
                continue

            # Save email
            if self.save_email(email):
                self.stats["successful_imports"] += 1
            else:
                self.stats["parsing_errors"] += 1

        # Save metadata and index
        self.save_metadata()

        # Print summary
        self.print_summary()

    def print_summary(self) -> None:
        """Print import summary to console."""
        print("\n" + "=" * 60)
        print("IMPORT SUMMARY")
        print("=" * 60)
        print(f"Total records processed: {self.stats['total_records']}")
        print(f"Successfully imported: {self.stats['successful_imports']}")
        print(f"Parsing errors: {self.stats['parsing_errors']}")
        print(f"Skipped (no content): {self.stats['skipped_records']}")
        print(f"\nEmails with sender: {self.stats['emails_with_sender']}")
        print(f"Emails with recipients: {self.stats['emails_with_recipients']}")
        print(f"Unique email addresses: {len(self.stats['unique_email_addresses'])}")
        print("\nDate range:")
        print(f"  Earliest: {self.stats['date_range']['earliest']}")
        print(f"  Latest: {self.stats['date_range']['latest']}")
        print(f"\nOutput directory: {OUTPUT_DIR}")
        print(f"Email files: {EMAILS_DIR}")
        print(f"Index file: {OUTPUT_DIR / 'email_index.json'}")
        print(f"Metadata file: {OUTPUT_DIR / 'import_metadata.json'}")
        if self.error_log:
            print(f"Error log: {ERROR_LOG}")
        print("=" * 60 + "\n")


def main():
    """Main entry point."""
    importer = EmailImporter()
    importer.run()


if __name__ == "__main__":
    main()
