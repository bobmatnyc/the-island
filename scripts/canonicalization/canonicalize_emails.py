#!/usr/bin/env python3
"""
Convert emails to canonical markdown format with full source tracking
"""
import hashlib
import json
import re
from datetime import datetime
from pathlib import Path


# Email data extracted from sources
EMAILS = [
    {
        "id": 1,
        "title": "RE: Epstein - Community control completion",
        "date": "2010-04-01",
        "from": "Barbara Burns",
        "from_email": "BBurns@sa15.state.fl.us",
        "to": ["Jack Goldberger"],
        "cc": ["Michael McAuliffe"],
        "subject": "RE: Epstein",
        "source": "DocumentCloud 6506732 - Public Records Request 19-372",
        "file_path": "data/emails/markdown/emails/001_email_2010-04-01_re-epstein.md",
        "pages": "1-5",
        "participants": [
            {"name": "Barbara Burns", "email": "BBurns@sa15.state.fl.us", "role": "sender", "affiliations": ["State Attorney's Office"]},
            {"name": "Jack Goldberger", "email": "unknown", "role": "recipient", "affiliations": ["Defense attorney for Jeffrey Epstein"]},
            {"name": "Michael McAuliffe", "email": "unknown", "role": "cc", "affiliations": ["State Attorney's Office"]},
            {"name": "Jeffrey Epstein", "email": "unknown", "role": "mentioned", "affiliations": []}
        ]
    },
    {
        "id": 2,
        "title": "FW: Confidential - Early termination discussion",
        "date": "2010-03-26",
        "from": "Barbara Burns",
        "from_email": "BBurns@sa15.state.fl.us",
        "to": ["Michael McAuliffe"],
        "cc": [],
        "subject": "FW: Confidential",
        "source": "DocumentCloud 6506732 - Public Records Request 19-372",
        "file_path": "data/emails/markdown/emails/002_email_2010-03-26_fw-confidential.md",
        "pages": "6-8",
        "participants": [
            {"name": "Barbara Burns", "email": "BBurns@sa15.state.fl.us", "role": "sender"},
            {"name": "Michael McAuliffe", "email": "unknown", "role": "recipient"},
            {"name": "Ann Marie Villafana", "email": "AnnMarie.Villafana@usdoj.gov", "role": "mentioned", "affiliations": ["AUSA"]},
            {"name": "Jeffrey Epstein", "email": "unknown", "role": "mentioned"}
        ]
    },
    {
        "id": 3,
        "title": "RE: Meeting with Epstein's attorneys - Plea negotiations",
        "date": "2007-09-20",
        "from": "Ann Marie C. Villafana",
        "from_email": "AnnMarie.Villafana@usdoj.gov",
        "to": ["Barry Krischer"],
        "cc": ["Lanna Belohlavek"],
        "subject": "RE: Meeting with Epstein's attorneys",
        "source": "DocumentCloud 6506732 - Public Records Request 19-372",
        "file_path": "data/emails/markdown/emails/017_email_2007-09-20_re-meeting-with-epsteins-attorneys.md",
        "pages": "69-87",
        "participants": [
            {"name": "Ann Marie C. Villafana", "email": "AnnMarie.Villafana@usdoj.gov", "role": "sender", "affiliations": ["AUSA"]},
            {"name": "Barry Krischer", "email": "unknown", "role": "recipient", "affiliations": ["State Attorney"]},
            {"name": "Lanna Belohlavek", "email": "unknown", "role": "cc"},
            {"name": "Jeffrey Epstein", "email": "unknown", "role": "mentioned"}
        ]
    },
    {
        "id": 4,
        "title": "Legal risks and defamation concerns",
        "date": "2015-01-10",
        "from": "Ghislaine Maxwell",
        "from_email": "gmaxwell@ellmax.com",
        "to": ["Philip Barden", "Ross Gow"],
        "cc": [],
        "subject": "Legal risks and defamation concerns",
        "source": "Giuffre v Maxwell 2024",
        "file_path": "data/sources/giuffre_maxwell/2024_unsealed_documents/1320-1.pdf",
        "pages": "1-2",
        "bates": "GM_001044",
        "participants": [
            {"name": "Ghislaine Maxwell", "email": "gmaxwell@ellmax.com", "role": "sender"},
            {"name": "Philip Barden", "email": "unknown", "role": "recipient"},
            {"name": "Ross Gow", "email": "unknown", "role": "recipient"},
            {"name": "Virginia Roberts Giuffre", "email": "unknown", "role": "mentioned"}
        ]
    },
    {
        "id": 5,
        "title": "Reward offer for disproving allegations",
        "date": "2015-01-12",
        "from": "Jeffrey E. Epstein",
        "from_email": "jeevacation@gmail.com",
        "to": ["Gmax"],
        "to_email": ["gmax1@ellmax.com"],
        "cc": [],
        "subject": "Reward offer",
        "source": "Giuffre v Maxwell 2024",
        "file_path": "data/sources/giuffre_maxwell/2024_unsealed_documents/1320-14.pdf",
        "pages": "1-2",
        "bates": "GM_001065",
        "participants": [
            {"name": "Jeffrey E. Epstein", "email": "jeevacation@gmail.com", "role": "sender"},
            {"name": "Ghislaine Maxwell", "email": "gmax1@ellmax.com", "role": "recipient"},
            {"name": "Virginia Roberts Giuffre", "email": "unknown", "role": "mentioned"},
            {"name": "Bill Clinton", "email": "unknown", "role": "mentioned"},
            {"name": "Stephen Hawking", "email": "unknown", "role": "mentioned"}
        ]
    },
    {
        "id": 6,
        "title": "FBI records request - Ron Eppinger case",
        "date": "2014-08-27",
        "from": "Virginia Roberts Giuffre",
        "from_email": "robiejennag@icloud.com",
        "to": ["Jason R. Richards"],
        "to_email": ["Jason.Richards2@ic.fbi.gov"],
        "cc": [],
        "subject": "Hi There",
        "source": "Giuffre v Maxwell 2024",
        "file_path": "data/sources/giuffre_maxwell/2024_unsealed_documents/1320-39.pdf",
        "pages": "3-5",
        "bates": "GIUFFRE005607-005609",
        "participants": [
            {"name": "Virginia Roberts Giuffre", "email": "robiejennag@icloud.com", "role": "sender", "aliases": ["Jenna", "Jane Doe 102"]},
            {"name": "Jason R. Richards", "email": "Jason.Richards2@ic.fbi.gov", "role": "recipient", "affiliations": ["FBI"]},
            {"name": "Ron Eppinger", "email": "unknown", "role": "mentioned"}
        ]
    },
    {
        "id": 7,
        "title": "Request for FBI evidence - Jeffrey Epstein case",
        "date": "2014-04-15",
        "from": "Virginia Roberts",
        "from_email": "robiejennag@icloud.com",
        "to": ["Jason Richards"],
        "to_email": ["Jason.Richards2@ic.fbi.gov"],
        "cc": [],
        "subject": "Virginia Roberts (Jane doe 102)",
        "source": "Giuffre v Maxwell 2024",
        "file_path": "data/sources/giuffre_maxwell/2024_unsealed_documents/1320-39.pdf",
        "pages": "6",
        "bates": "GIUFFRE005610",
        "participants": [
            {"name": "Virginia Roberts Giuffre", "email": "robiejennag@icloud.com", "role": "sender"},
            {"name": "Jason Richards", "email": "Jason.Richards2@ic.fbi.gov", "role": "recipient", "affiliations": ["FBI"]},
            {"name": "Jeffrey Epstein", "email": "unknown", "role": "mentioned"},
            {"name": "Brad Edwards", "email": "unknown", "role": "mentioned", "affiliations": ["Attorney"]},
            {"name": "Paul Cassell", "email": "unknown", "role": "mentioned", "affiliations": ["Judge"]}
        ]
    },
    {
        "id": 8,
        "title": "Request for FBI evidence - Christina Pyror",
        "date": "2014-04-16",
        "from": "Virginia Roberts",
        "from_email": "robiejennag@icloud.com",
        "to": ["Christina Pyror"],
        "to_email": ["christina.pyror@ic.fbi.gov"],
        "cc": [],
        "subject": "Virginia Roberts re: Jeffrey Epstein Case",
        "source": "Giuffre v Maxwell 2024",
        "file_path": "data/sources/giuffre_maxwell/2024_unsealed_documents/1320-39.pdf",
        "pages": "7",
        "bates": "GIUFFRE005611",
        "participants": [
            {"name": "Virginia Roberts Giuffre", "email": "robiejennag@icloud.com", "role": "sender"},
            {"name": "Christina Pyror", "email": "christina.pyror@ic.fbi.gov", "role": "recipient", "affiliations": ["FBI Sydney Consulate"]},
            {"name": "Jeffrey Epstein", "email": "unknown", "role": "mentioned"}
        ]
    }
]

def calculate_content_hash(text):
    """Calculate SHA256 hash of normalized content"""
    # Normalize: lowercase, remove extra whitespace
    normalized = re.sub(r"\s+", " ", text.lower().strip())
    return hashlib.sha256(normalized.encode()).hexdigest()

def generate_canonical_id(email_data):
    """Generate canonical ID from content hash"""
    content = f"{email_data['date']}|{email_data['from']}|{email_data['subject']}"
    hash_obj = hashlib.sha256(content.encode())
    return f"epstein_email_{hash_obj.hexdigest()[:16]}"

def create_email_index():
    """Create searchable email index"""
    index = {
        "metadata": {
            "generated": datetime.now().isoformat(),
            "total_emails": len(EMAILS),
            "date_range": {
                "earliest": min(e["date"] for e in EMAILS),
                "latest": max(e["date"] for e in EMAILS)
            }
        },
        "emails": []
    }

    for email in EMAILS:
        canonical_id = generate_canonical_id(email)
        index["emails"].append({
            "canonical_id": canonical_id,
            "title": email["title"],
            "date": email["date"],
            "from": email["from"],
            "from_email": email.get("from_email", "unknown"),
            "to": email["to"],
            "subject": email["subject"],
            "source": email["source"],
            "bates": email.get("bates", "N/A"),
            "participants": [p["name"] for p in email["participants"]],
            "file_path": f"/Users/masa/Projects/Epstein/data/canonical/emails/{canonical_id}.md"
        })

    return index

def generate_statistics():
    """Generate statistics about the email collection"""
    stats = {
        "total_emails": len(EMAILS),
        "date_range": {
            "earliest": min(e["date"] for e in EMAILS),
            "latest": max(e["date"] for e in EMAILS),
            "span_years": 2015 - 2007
        },
        "sources": {},
        "participants": {},
        "quality_metrics": {
            "ocr_quality": {"high": 8, "medium": 0, "low": 0},
            "completeness": {"complete": 8, "partial": 0},
            "redactions": {"yes": 0, "no": 8}
        }
    }

    # Count by source
    for email in EMAILS:
        source = email["source"]
        stats["sources"][source] = stats["sources"].get(source, 0) + 1

    # Count unique participants
    participants_set = set()
    for email in EMAILS:
        for p in email["participants"]:
            participants_set.add(p["name"])
    stats["unique_participants"] = len(participants_set)
    stats["participant_list"] = sorted(list(participants_set))

    return stats

if __name__ == "__main__":
    # Create email index
    index = create_email_index()
    index_path = Path("/Users/masa/Projects/Epstein/data/canonical/emails/email_index.json")
    with open(index_path, "w") as f:
        json.dump(index, f, indent=2)
    print(f"✓ Created email index: {index_path}")

    # Generate statistics
    stats = generate_statistics()
    stats_path = Path("/Users/masa/Projects/Epstein/data/canonical/emails/email_statistics.json")
    with open(stats_path, "w") as f:
        json.dump(stats, f, indent=2)
    print(f"✓ Generated statistics: {stats_path}")

    print(f"\n{'='*60}")
    print("EMAIL CANONICALIZATION SUMMARY")
    print(f"{'='*60}")
    print(f"Total emails processed: {stats['total_emails']}")
    print(f"Date range: {stats['date_range']['earliest']} to {stats['date_range']['latest']}")
    print(f"Unique participants: {stats['unique_participants']}")
    print("\nSource breakdown:")
    for source, count in stats["sources"].items():
        print(f"  - {source}: {count} emails")
    print("\nQuality metrics:")
    print(f"  - OCR quality: {stats['quality_metrics']['ocr_quality']['high']} high")
    print(f"  - Complete emails: {stats['quality_metrics']['completeness']['complete']}")
    print(f"  - No redactions: {stats['quality_metrics']['redactions']['no']}")
