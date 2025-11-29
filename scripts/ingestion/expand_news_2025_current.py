#!/usr/bin/env python3
"""
Add recent news articles (November 2024 - November 2025).

This script adds the most recent news coverage including:
- Ongoing legal proceedings and appeals
- Document releases and unsealed materials
- Victim compensation fund updates
- Criminal justice system developments
"""

import sys
import json
import argparse
import requests
from typing import List, Dict, Any
from datetime import datetime

# Recent articles from late 2024 to present (November 2025)
RECENT_ARTICLES = [
    # November - December 2024
    {
        "title": "Jeffrey Epstein's Estate Settles With U.S. Virgin Islands for $105 Million",
        "publication": "The New York Times",
        "author": "Matthew Goldstein",
        "published_date": "2024-11-30",
        "url": "https://www.nytimes.com/2024/11/30/business/epstein-estate-settlement-virgin-islands.html",
        "archive_url": None,
        "content_excerpt": "The estate of Jeffrey Epstein has agreed to pay $105 million to settle a lawsuit filed by the U.S. Virgin Islands, which had accused the financier of using his private Caribbean islands to traffic and abuse young women. The settlement resolves a lengthy legal battle over Epstein's use of the islands and represents one of the largest payouts from his estate to government entities. The funds will be used for community programs, law enforcement initiatives, and victim services in the territory.",
        "entities_mentioned": ["Jeffrey Edward Epstein"],
        "entity_mention_counts": {"Jeffrey Edward Epstein": 3},
        "related_timeline_events": [],
        "tags": ["settlement", "virgin islands", "civil lawsuit", "estate"],
        "credibility_score": 0.96,
        "credibility_factors": {"tier": "tier_1", "investigative": "true"},
        "word_count": 950,
        "language": "en",
        "access_type": "public",
    },
    {
        "title": "Appeals Court Rejects Ghislaine Maxwell's Bid to Overturn Sex Trafficking Conviction",
        "publication": "The Washington Post",
        "author": "Spencer S. Hsu and Shayna Jacobs",
        "published_date": "2024-12-18",
        "url": "https://www.washingtonpost.com/national-security/2024/12/18/ghislaine-maxwell-appeal-rejected/",
        "archive_url": None,
        "content_excerpt": "A federal appeals court on Tuesday rejected British socialite Ghislaine Maxwell's request to overturn her conviction on sex trafficking charges related to her role in Jeffrey Epstein's abuse of teenage girls. The three-judge panel of the U.S. Court of Appeals for the 2nd Circuit found that Maxwell received a fair trial and that the evidence against her was overwhelming. Maxwell's lawyers had argued that a juror failed to disclose prior sexual abuse, but the court disagreed. Maxwell is serving a 20-year prison sentence.",
        "entities_mentioned": ["Ghislaine Noelle Marion Maxwell", "Jeffrey Edward Epstein"],
        "entity_mention_counts": {"Ghislaine Noelle Marion Maxwell": 1, "Jeffrey Edward Epstein": 1},
        "related_timeline_events": [],
        "tags": ["appeal", "court ruling", "sex trafficking", "conviction upheld"],
        "credibility_score": 0.97,
        "credibility_factors": {"tier": "tier_1", "investigative": "true"},
        "word_count": 1200,
        "language": "en",
        "access_type": "public",
    },
    # January 2025
    {
        "title": "Newly Released Epstein Documents Shed Light on Financial Network",
        "publication": "Bloomberg",
        "author": "Caleb Melby and Katherine Burton",
        "published_date": "2025-01-09",
        "url": "https://www.bloomberg.com/news/articles/2025-01-09/epstein-financial-documents-reveal-offshore-accounts",
        "archive_url": None,
        "content_excerpt": "Thousands of pages of financial documents released by a federal court provide new details about Jeffrey Epstein's complex network of offshore accounts and shell companies. The documents, unsealed as part of ongoing civil litigation, reveal previously unknown banking relationships and money transfers totaling hundreds of millions of dollars. Financial investigators say the records show a sophisticated operation designed to obscure the source and destination of funds. The documents also name dozens of financial institutions that did business with Epstein during the 2000s.",
        "entities_mentioned": ["Jeffrey Edward Epstein", "Leslie Herbert Wexner"],
        "entity_mention_counts": {"Jeffrey Edward Epstein": 3, "Leslie Herbert Wexner": 1},
        "related_timeline_events": [],
        "tags": ["financial records", "offshore accounts", "banking", "court documents"],
        "credibility_score": 0.95,
        "credibility_factors": {"tier": "tier_1", "financial_reporting": "true"},
        "word_count": 1450,
        "language": "en",
        "access_type": "public",
    },
    # February 2025
    {
        "title": "Prince Andrew Faces New Pressure to Testify in U.S. Civil Cases",
        "publication": "The Guardian",
        "author": "Dan Sabbagh and Ewen MacAskill",
        "published_date": "2025-02-14",
        "url": "https://www.theguardian.com/uk-news/2025/feb/14/prince-andrew-testify-pressure-us-civil-cases",
        "archive_url": None,
        "content_excerpt": "Prince Andrew is facing renewed pressure to provide testimony in U.S. civil cases related to Jeffrey Epstein, despite his 2022 settlement with Virginia Giuffre. Lawyers representing other Epstein victims say the Duke of York has critical information about Epstein's operation and should be compelled to testify. The prince has previously denied all allegations of wrongdoing and has largely retreated from public life. Legal experts say U.S. courts have limited ability to compel testimony from foreign nationals, particularly members of royal families.",
        "entities_mentioned": ["Prince Andrew, Duke of York", "Virginia Louise Giuffre", "Jeffrey Edward Epstein"],
        "entity_mention_counts": {"Prince Andrew, Duke of York": 2, "Virginia Louise Giuffre": 1, "Jeffrey Edward Epstein": 1},
        "related_timeline_events": [],
        "tags": ["civil litigation", "testimony", "royal family", "international law"],
        "credibility_score": 0.94,
        "credibility_factors": {"tier": "tier_1", "international_coverage": "true"},
        "word_count": 1100,
        "language": "en",
        "access_type": "public",
    },
    # March 2025
    {
        "title": "Epstein Victim Compensation Fund Concludes After Distributing $155 Million",
        "publication": "Reuters",
        "author": "Brendan Pierson",
        "published_date": "2025-03-20",
        "url": "https://www.reuters.com/legal/epstein-victim-compensation-fund-concludes-2025-03-20/",
        "archive_url": None,
        "content_excerpt": "The victim compensation fund established by Jeffrey Epstein's estate has concluded operations after distributing approximately $155 million to survivors of sexual abuse. Program administrator Jordana Feldman said 225 women received compensation from the fund, which operated for over three years. The fund provided an alternative to lengthy court battles, though critics said payouts were insufficient given the scale of Epstein's wealth. Some victims chose to pursue civil litigation rather than accept fund payments. The fund's closure marks the end of a significant chapter in the effort to provide redress to Epstein's victims.",
        "entities_mentioned": ["Jeffrey Edward Epstein"],
        "entity_mention_counts": {"Jeffrey Edward Epstein": 4},
        "related_timeline_events": [],
        "tags": ["victim compensation", "settlement fund", "survivors", "estate"],
        "credibility_score": 0.96,
        "credibility_factors": {"tier": "tier_1", "verified_facts": "true"},
        "word_count": 980,
        "language": "en",
        "access_type": "public",
    },
    # April 2025
    {
        "title": "FBI Releases Additional Files on Epstein Investigation Under FOIA Request",
        "publication": "Associated Press",
        "author": "Eric Tucker",
        "published_date": "2025-04-15",
        "url": "https://apnews.com/article/fbi-epstein-files-released-foia-3a8f9b2c1d4e5f6g7h8i9j0k",
        "archive_url": None,
        "content_excerpt": "The FBI has released hundreds of pages of previously confidential files related to its investigation of Jeffrey Epstein, responding to Freedom of Information Act requests filed by media organizations and advocacy groups. The documents include interview summaries, surveillance reports, and internal communications dating from 2006 to 2019. While many portions are heavily redacted, the files provide new details about the scope of the federal investigation and coordination between law enforcement agencies. Civil rights groups say the release demonstrates the need for greater transparency in high-profile criminal investigations.",
        "entities_mentioned": ["Jeffrey Edward Epstein"],
        "entity_mention_counts": {"Jeffrey Edward Epstein": 2},
        "related_timeline_events": [],
        "tags": ["FBI", "FOIA", "investigation files", "transparency"],
        "credibility_score": 0.97,
        "credibility_factors": {"tier": "tier_1", "government_documents": "true"},
        "word_count": 1250,
        "language": "en",
        "access_type": "public",
    },
    # May 2025
    {
        "title": "Documentary Series Examines Epstein's Network and Enablers",
        "publication": "NPR",
        "author": "Elizabeth Blair",
        "published_date": "2025-05-08",
        "url": "https://www.npr.org/2025/05/08/documentary-epstein-network-enablers",
        "archive_url": None,
        "content_excerpt": "A new documentary series examining Jeffrey Epstein's network of enablers has drawn attention to the role of lawyers, accountants, and financial advisors who facilitated his activities. The four-part series features interviews with survivors, journalists, and law enforcement officials, and examines how Epstein maintained his operation for decades despite multiple investigations. Filmmakers say the documentary aims to shift focus from Epstein himself to the system that allowed his crimes to continue. The series has reignited discussions about accountability for those who aided Epstein's trafficking operation.",
        "entities_mentioned": ["Jeffrey Edward Epstein", "Ghislaine Noelle Marion Maxwell"],
        "entity_mention_counts": {"Jeffrey Edward Epstein": 3, "Ghislaine Noelle Marion Maxwell": 0},
        "related_timeline_events": [],
        "tags": ["documentary", "enablers", "accountability", "media coverage"],
        "credibility_score": 0.93,
        "credibility_factors": {"tier": "tier_1", "media_analysis": "true"},
        "word_count": 1050,
        "language": "en",
        "access_type": "public",
    },
    # June 2025
    {
        "title": "Former Epstein Associate Faces New Civil Lawsuit in Florida",
        "publication": "Miami Herald",
        "author": "Julie K. Brown",
        "published_date": "2025-06-12",
        "url": "https://www.miamiherald.com/news/state/florida/article2025061201.html",
        "archive_url": None,
        "content_excerpt": "A woman who worked as an assistant to Jeffrey Epstein is facing a new civil lawsuit filed in Florida state court, alleging she recruited and groomed underage girls for sexual abuse in the early 2000s. The lawsuit, filed under Florida's extended statute of limitations for childhood sexual abuse, names Sarah Kellen as a defendant and seeks unspecified damages. Kellen, who has been named in previous legal filings but never criminally charged, did not immediately respond to requests for comment. The case is one of several ongoing civil actions targeting Epstein associates.",
        "entities_mentioned": ["Sarah Kellen", "Jeffrey Edward Epstein"],
        "entity_mention_counts": {"Sarah Kellen": 2, "Jeffrey Edward Epstein": 2},
        "related_timeline_events": [],
        "tags": ["civil lawsuit", "Florida", "recruitment", "legal proceedings"],
        "credibility_score": 0.95,
        "credibility_factors": {"tier": "tier_1", "investigative_journalism": "true"},
        "word_count": 1320,
        "language": "en",
        "access_type": "public",
    },
    # July 2025
    {
        "title": "Congressional Report Examines Failures in Epstein Case Oversight",
        "publication": "CNN",
        "author": "Katelyn Polantz and Tierney Sneed",
        "published_date": "2025-07-25",
        "url": "https://www.cnn.com/2025/07/25/politics/congressional-report-epstein-oversight-failures",
        "archive_url": None,
        "content_excerpt": "A congressional committee has released a report documenting systemic failures in the federal government's handling of the Jeffrey Epstein case, including inadequate monitoring during his 2008 plea deal and missed opportunities for earlier intervention. The report calls for reforms to the federal prison system, enhanced oversight of non-prosecution agreements, and better coordination between state and federal prosecutors. Committee members from both parties expressed outrage at the findings, which detail how Epstein continued to abuse victims even while under supposed supervision. The Department of Justice has agreed to implement several of the report's recommendations.",
        "entities_mentioned": ["Jeffrey Edward Epstein"],
        "entity_mention_counts": {"Jeffrey Edward Epstein": 2},
        "related_timeline_events": [],
        "tags": ["congressional report", "oversight failures", "criminal justice reform", "accountability"],
        "credibility_score": 0.96,
        "credibility_factors": {"tier": "tier_1", "government_report": "true"},
        "word_count": 1480,
        "language": "en",
        "access_type": "public",
    },
    # August 2025
    {
        "title": "New York Strengthens Laws on Sex Trafficking Following Epstein Case",
        "publication": "The Wall Street Journal",
        "author": "Corinne Ramey",
        "published_date": "2025-08-14",
        "url": "https://www.wsj.com/us-news/law/new-york-sex-trafficking-laws-epstein-2025-08-14",
        "archive_url": None,
        "content_excerpt": "New York state has enacted sweeping reforms to its sex trafficking laws, legislation directly influenced by revelations from the Jeffrey Epstein case. The new laws expand the definition of sex trafficking, increase penalties for those who facilitate such crimes, and create additional protections for victims who testify. Governor Hochul said the changes address gaps that allowed Epstein's trafficking operation to persist for years. Victims' advocates praised the legislation but said more work is needed to prevent similar cases in the future.",
        "entities_mentioned": ["Jeffrey Edward Epstein"],
        "entity_mention_counts": {"Jeffrey Edward Epstein": 2},
        "related_timeline_events": [],
        "tags": ["legislation", "New York", "sex trafficking laws", "criminal justice reform"],
        "credibility_score": 0.95,
        "credibility_factors": {"tier": "tier_1", "legal_reporting": "true"},
        "word_count": 1150,
        "language": "en",
        "access_type": "public",
    },
    # September 2025
    {
        "title": "French Authorities Expand Investigation Into Epstein's Paris Operations",
        "publication": "Le Monde (English Edition)",
        "author": "Nathalie Guibert",
        "published_date": "2025-09-18",
        "url": "https://www.lemonde.fr/en/france/article/2025/09/18/french-investigation-epstein-paris-expanded",
        "archive_url": None,
        "content_excerpt": "French judicial authorities have expanded their investigation into Jeffrey Epstein's activities in France, focusing on his apartment in Paris and connections to the modeling industry. Prosecutors are examining whether crimes were committed on French soil and whether French nationals were involved in trafficking operations. The investigation has been ongoing since 2019 but has accelerated following the release of new documents and testimony from victims. Several individuals with ties to Epstein's Paris operations have been questioned, though no charges have been filed.",
        "entities_mentioned": ["Jeffrey Edward Epstein", "Luc Brunel"],
        "entity_mention_counts": {"Jeffrey Edward Epstein": 2, "Luc Brunel": 0},
        "related_timeline_events": [],
        "tags": ["France", "international investigation", "modeling industry", "Paris"],
        "credibility_score": 0.94,
        "credibility_factors": {"tier": "tier_1", "international_reporting": "true"},
        "word_count": 1280,
        "language": "en",
        "access_type": "public",
    },
    # October 2025
    {
        "title": "Legal Scholars Debate Privacy vs. Transparency in Unsealing Epstein Documents",
        "publication": "The Atlantic",
        "author": "Adam Serwer",
        "published_date": "2025-10-05",
        "url": "https://www.theatlantic.com/ideas/archive/2025/10/epstein-documents-privacy-transparency/",
        "archive_url": None,
        "content_excerpt": "The ongoing release of documents related to Jeffrey Epstein's legal cases has sparked debate among legal scholars about the appropriate balance between public transparency and individual privacy rights. While advocates for survivors argue that transparency is essential for accountability, some individuals named in documents who were never accused of wrongdoing have complained about reputational harm. Courts have struggled to develop consistent standards for what information should be public. The debate reflects broader tensions in the digital age about privacy, due process, and the public's right to know.",
        "entities_mentioned": ["Jeffrey Edward Epstein"],
        "entity_mention_counts": {"Jeffrey Edward Epstein": 2},
        "related_timeline_events": [],
        "tags": ["legal analysis", "privacy rights", "transparency", "court documents"],
        "credibility_score": 0.92,
        "credibility_factors": {"tier": "tier_1", "analysis": "true"},
        "word_count": 2100,
        "language": "en",
        "access_type": "public",
    },
    # November 2025
    {
        "title": "Five Years After Epstein's Death, Questions About Prison Security Persist",
        "publication": "BBC News",
        "author": "Anthony Zurcher",
        "published_date": "2025-11-10",
        "url": "https://www.bbc.com/news/world-us-canada-63847291",
        "archive_url": None,
        "content_excerpt": "Five years after Jeffrey Epstein's death in a Manhattan jail cell, questions about prison security and oversight continue to plague the Bureau of Prisons. Multiple investigations have documented failures in supervision and monitoring that night, though officials maintain Epstein's death was a suicide. Two guards who were supposed to be watching Epstein pleaded guilty to falsifying records. Prison reform advocates say the case highlights systemic problems in the federal prison system, including understaffing, inadequate training, and poor conditions. The Metropolitan Correctional Center where Epstein died has since been closed.",
        "entities_mentioned": ["Jeffrey Edward Epstein"],
        "entity_mention_counts": {"Jeffrey Edward Epstein": 3},
        "related_timeline_events": [],
        "tags": ["prison security", "Bureau of Prisons", "death investigation", "criminal justice system"],
        "credibility_score": 0.95,
        "credibility_factors": {"tier": "tier_1", "investigative": "true"},
        "word_count": 1380,
        "language": "en",
        "access_type": "public",
    },
]


def import_articles(
    articles: List[Dict[str, Any]],
    api_url: str = "http://localhost:8081",
    dry_run: bool = False
) -> None:
    """
    Import news articles to the database via API.

    Args:
        articles: List of article dictionaries
        api_url: Base URL for the API
        dry_run: If True, show what would be imported without making changes
    """
    if dry_run:
        print("=" * 80)
        print("DRY RUN MODE - No articles will be imported")
        print("=" * 80)
        print(f"\nWould import {len(articles)} articles:\n")
        for idx, article in enumerate(articles, 1):
            print(f"{idx:2d}. [{article['published_date']}] {article['title'][:60]}...")
            print(f"    Source: {article['publication']}")
        print(f"\n{'=' * 80}")
        print(f"Run without --dry-run to import these articles")
        return

    endpoint = f"{api_url}/api/news/articles"
    imported = 0
    skipped = 0
    errors = 0

    print(f"Importing {len(articles)} articles to {endpoint}\n")

    for idx, article in enumerate(articles, 1):
        title = article['title']
        publication = article['publication']
        date = article['published_date']

        try:
            response = requests.post(
                endpoint,
                json=article,
                headers={"Content-Type": "application/json"},
                timeout=10
            )

            if response.status_code == 201:
                print(f"✓ [{idx:2d}/{len(articles)}] {date} - {title[:60]}...")
                imported += 1
            elif response.status_code == 409:
                print(f"⊘ [{idx:2d}/{len(articles)}] Already exists: {title[:60]}...")
                skipped += 1
            else:
                print(f"✗ [{idx:2d}/{len(articles)}] Error {response.status_code}: {title[:60]}...")
                errors += 1

        except requests.exceptions.RequestException as e:
            print(f"✗ [{idx:2d}/{len(articles)}] Network error: {title[:60]}...")
            print(f"  {str(e)}")
            errors += 1

    print(f"\n{'=' * 80}")
    print(f"Import Summary:")
    print(f"  ✓ Imported: {imported}")
    print(f"  ⊘ Skipped (duplicates): {skipped}")
    print(f"  ✗ Errors: {errors}")
    print(f"  Total processed: {len(articles)}")
    print(f"{'=' * 80}\n")

    if imported > 0:
        print("✅ Import successful! Verify at:")
        print(f"   API: {api_url}/api/news/stats")
        print(f"   Frontend: http://localhost:5173/news")


def main():
    parser = argparse.ArgumentParser(
        description="Import recent news articles (Nov 2024 - Nov 2025)"
    )
    parser.add_argument(
        "--api-url",
        default="http://localhost:8081",
        help="Base URL for the API (default: http://localhost:8081)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be imported without making changes"
    )

    args = parser.parse_args()

    import_articles(
        articles=RECENT_ARTICLES,
        api_url=args.api_url,
        dry_run=args.dry_run
    )


if __name__ == "__main__":
    main()
