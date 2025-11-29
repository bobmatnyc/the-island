#!/usr/bin/env python3
"""
Manual News Import - High-Quality Curated Articles
Imports manually curated news articles without web scraping.

Design Decision: Manual Curation Over Web Scraping
Rationale: Many news URLs are behind paywalls or return 404. Manual curation
ensures high-quality articles with accurate metadata and entity linking.

Usage:
    python import_manual_news.py
"""

import logging
import sys

import requests


logging.basicConfig(level=logging.INFO, format="%(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Manually curated tier-1 articles
CURATED_ARTICLES = [
    {
        "title": "Even from jail, sex abuser manipulated the system. His victims were kept in the dark",
        "publication": "Miami Herald",
        "author": "Julie K. Brown",
        "published_date": "2018-11-29",
        "url": "https://www.miamiherald.com/news/local/article222628265.html",
        "content_excerpt": "The Perversion of Justice investigative series exposed how Jeffrey Epstein manipulated the justice system even from jail. Through settlement agreements and a secret non-prosecution deal, Epstein and his legal team kept victims in the dark while avoiding serious federal prosecution. This groundbreaking reporting led to renewed investigations.",
        "entities_mentioned": [
            "Jeffrey Epstein",
            "Alexander Acosta",
            "Alan Dershowitz",
            "Ghislaine Maxwell",
        ],
        "tags": ["investigation", "plea deal", "justice system", "victims"],
        "credibility_score": 0.98,
        "credibility_factors": {"tier": "tier_1", "pulitzer": "finalist"},
        "word_count": 2800,
    },
    {
        "title": "Financier Jeffrey Epstein charged with sex trafficking",
        "publication": "Associated Press",
        "author": "Michael R. Sisak",
        "published_date": "2019-07-06",
        "url": "https://apnews.com/article/jeffrey-epstein-arrested-sex-trafficking-90303d0c6c4a462fa28dedc82fa5ac72",
        "content_excerpt": "Jeffrey Epstein, a wealthy financier, was arrested and charged with sex trafficking dozens of minors in Florida and New York. Federal prosecutors unsealed new charges despite a controversial 2008 plea deal. The arrest came years after investigative reporting by the Miami Herald raised questions about the lenient treatment Epstein received.",
        "entities_mentioned": ["Jeffrey Epstein", "Alexander Acosta"],
        "tags": ["arrest", "sex trafficking", "federal charges"],
        "credibility_score": 0.95,
        "credibility_factors": {"tier": "tier_1"},
        "word_count": 1200,
    },
    {
        "title": "Billionaire Jeffrey Epstein arrested on sex trafficking charges",
        "publication": "Reuters",
        "author": "Karen Freifeld",
        "published_date": "2019-07-06",
        "url": "https://www.reuters.com/article/us-people-jeffrey-epstein-idUSKCN1U10QU",
        "content_excerpt": "Billionaire financier Jeffrey Epstein was charged with sex trafficking dozens of underage girls from 2002 to 2005. The indictment came after years of controversy over a non-prosecution agreement that allowed Epstein to plead guilty to lesser state charges in Florida. Prosecutors said Epstein lured girls as young as 14 to his New York and Florida residences.",
        "entities_mentioned": ["Jeffrey Epstein"],
        "tags": ["arrest", "sex trafficking", "indictment"],
        "credibility_score": 0.92,
        "credibility_factors": {"tier": "tier_1"},
        "word_count": 950,
    },
    {
        "title": "Billionaire Financier Jeffrey Epstein Arrested On Sex Trafficking Charges",
        "publication": "NPR",
        "author": "Brian Naylor",
        "published_date": "2019-07-06",
        "url": "https://www.npr.org/2019/07/06/739161719/billionaire-financier-jeffrey-epstein-arrested-on-sex-trafficking-charges",
        "content_excerpt": "Jeffrey Epstein was arrested Saturday on federal charges of sex trafficking involving dozens of underage girls. The charges date back to at least 2002 and involve girls as young as 14. The arrest follows a Miami Herald investigation that reexamined Epstein's 2008 plea deal and brought new attention to allegations against him.",
        "entities_mentioned": ["Jeffrey Epstein", "Alexander Acosta", "Ghislaine Maxwell"],
        "tags": ["arrest", "sex trafficking"],
        "credibility_score": 0.95,
        "credibility_factors": {"tier": "tier_1"},
        "word_count": 850,
    },
    {
        "title": "Jeffrey Epstein Charged in New York With Sex Trafficking of Minors",
        "publication": "The New York Times",
        "author": "Benjamin Weiser, William K. Rashbaum",
        "published_date": "2019-07-06",
        "url": "https://www.nytimes.com/2019/07/06/nyregion/jeffrey-epstein-arrested-sex-trafficking.html",
        "content_excerpt": "Jeffrey Epstein, the financier who once mingled with presidents and princes, was arrested and charged with sex trafficking of minors. Prosecutors alleged he recruited dozens of girls, some as young as 14, and paid them to engage in sex acts at his mansions in Manhattan and Palm Beach. The indictment marked a dramatic reversal of fortune for Epstein.",
        "entities_mentioned": [
            "Jeffrey Epstein",
            "Bill Clinton",
            "Donald Trump",
            "Prince Andrew, Duke of York",
        ],
        "tags": ["arrest", "sex trafficking", "federal charges"],
        "credibility_score": 0.95,
        "credibility_factors": {"tier": "tier_1"},
        "word_count": 1450,
    },
    {
        "title": "Jeffrey Epstein arrested on charges of sex trafficking of minors",
        "publication": "The Washington Post",
        "author": "Matt Zapotosky, Devlin Barrett",
        "published_date": "2019-07-06",
        "url": "https://www.washingtonpost.com/national/jeffrey-epstein-arrested-reportedly-on-sex-trafficking-charges/2019/07/06/2c7dbac2-9ff2-11e9-b27f-ed2942f73d70_story.html",
        "content_excerpt": "Wealthy financier Jeffrey Epstein was arrested on federal sex-trafficking charges. The arrest came after a Miami Herald investigation uncovered how Epstein had secured a secret plea deal more than a decade ago. Federal prosecutors in New York accused Epstein of sexually exploiting dozens of underage girls.",
        "entities_mentioned": ["Jeffrey Epstein", "Alexander Acosta"],
        "tags": ["arrest", "sex trafficking"],
        "credibility_score": 0.95,
        "credibility_factors": {"tier": "tier_1"},
        "word_count": 1100,
    },
    {
        "title": "Jeffrey Epstein: How he died and what happens next",
        "publication": "BBC News",
        "author": "BBC News staff",
        "published_date": "2019-08-10",
        "url": "https://www.bbc.com/news/world-us-canada-48887131",
        "content_excerpt": "Jeffrey Epstein was found dead in his jail cell in what officials said was an apparent suicide. The 66-year-old financier had been charged with sex trafficking and was awaiting trial. His death raised questions about the circumstances of his detention and sparked numerous conspiracy theories.",
        "entities_mentioned": ["Jeffrey Epstein"],
        "tags": ["death", "investigation", "conspiracy theories"],
        "credibility_score": 0.93,
        "credibility_factors": {"tier": "tier_1"},
        "word_count": 800,
    },
    {
        "title": "Jeffrey Epstein death: what we know and don't know",
        "publication": "The Guardian",
        "author": "Sam Levin",
        "published_date": "2019-08-10",
        "url": "https://www.theguardian.com/us-news/2019/aug/10/jeffrey-epstein-death-what-we-know-so-far",
        "content_excerpt": "Jeffrey Epstein's death by apparent suicide in a Manhattan jail cell has sparked widespread scrutiny of the federal prison system and conspiracy theories about what happened. This analysis examines what is known and unknown about the circumstances of his death.",
        "entities_mentioned": ["Jeffrey Epstein"],
        "tags": ["death", "investigation", "analysis"],
        "credibility_score": 0.92,
        "credibility_factors": {"tier": "tier_1"},
        "word_count": 1200,
    },
    {
        "title": "Who is Ghislaine Maxwell? Jeffrey Epstein's alleged recruiter",
        "publication": "CNN",
        "author": "Artemis Moshtaghian",
        "published_date": "2019-12-02",
        "url": "https://www.cnn.com/2019/12/02/us/ghislaine-maxwell-jeffrey-epstein/index.html",
        "content_excerpt": "Ghislaine Maxwell, the British socialite and longtime associate of Jeffrey Epstein, has been named in multiple lawsuits by women who say she helped recruit them for sexual abuse. This profile examines Maxwell's background, her relationship with Epstein, and the allegations against her.",
        "entities_mentioned": ["Ghislaine Maxwell", "Jeffrey Epstein", "Robert Maxwell"],
        "tags": ["profile", "allegations", "ghislaine maxwell"],
        "credibility_score": 0.90,
        "credibility_factors": {"tier": "tier_1"},
        "word_count": 1500,
    },
    {
        "title": "Ghislaine Maxwell found guilty of sex trafficking minors for Jeffrey Epstein",
        "publication": "NPR",
        "author": "Jaclyn Diaz",
        "published_date": "2021-12-29",
        "url": "https://www.npr.org/2021/12/29/1068952082/ghislaine-maxwell-guilty-verdict",
        "content_excerpt": "Ghislaine Maxwell was found guilty on five of six counts in her sex trafficking trial. Prosecutors said she recruited and groomed underage girls for Jeffrey Epstein to abuse. The verdict came after a three-week trial that featured emotional testimony from four women who said Maxwell played a critical role in their abuse.",
        "entities_mentioned": ["Ghislaine Maxwell", "Jeffrey Epstein"],
        "tags": ["trial", "verdict", "sex trafficking", "ghislaine maxwell"],
        "credibility_score": 0.95,
        "credibility_factors": {"tier": "tier_1"},
        "word_count": 950,
    },
    {
        "title": "Ghislaine Maxwell: Epstein accomplice guilty of sex trafficking",
        "publication": "BBC News",
        "author": "Bernd Debusmann Jr",
        "published_date": "2021-12-29",
        "url": "https://www.bbc.com/news/world-us-canada-59827706",
        "content_excerpt": "Ghislaine Maxwell has been found guilty of recruiting and trafficking young girls to be sexually abused by Jeffrey Epstein. The 60-year-old was convicted on five of six charges after a month-long trial in New York. She faces up to 65 years in prison.",
        "entities_mentioned": ["Ghislaine Maxwell", "Jeffrey Epstein"],
        "tags": ["trial", "verdict", "conviction", "ghislaine maxwell"],
        "credibility_score": 0.93,
        "credibility_factors": {"tier": "tier_1"},
        "word_count": 1100,
    },
]


def get_existing_articles(api_url: str) -> set:
    """Get URLs of articles already in database."""
    try:
        response = requests.get(f"{api_url}/api/news/stats", timeout=10)
        response.raise_for_status()

        # Get all articles to check URLs
        response = requests.get(f"{api_url}/api/news/articles?limit=100", timeout=10)
        response.raise_for_status()

        data = response.json()
        urls = {article["url"] for article in data.get("articles", [])}
        logger.info(f"Found {len(urls)} existing articles")
        return urls
    except Exception as e:
        logger.warning(f"Could not fetch existing articles: {e}")
        return set()


def import_article(api_url: str, article: dict) -> bool:
    """Import single article via API."""
    try:
        # Build API payload
        payload = {
            "title": article["title"],
            "publication": article["publication"],
            "author": article.get("author"),
            "published_date": article["published_date"],
            "url": article["url"],
            "archive_url": article.get("archive_url"),
            "content_excerpt": article["content_excerpt"],
            "word_count": article.get("word_count", 0),
            "entities_mentioned": article.get("entities_mentioned", []),
            "entity_mention_counts": {
                entity: article["content_excerpt"].lower().count(entity.lower())
                for entity in article.get("entities_mentioned", [])
            },
            "credibility_score": article.get("credibility_score", 0.90),
            "credibility_factors": article.get("credibility_factors", {"tier": "tier_1"}),
            "tags": article.get("tags", []),
            "language": "en",
            "access_type": "public",
        }

        response = requests.post(
            f"{api_url}/api/news/articles",
            json=payload,
            timeout=30,
            headers={"Content-Type": "application/json"},
        )

        response.raise_for_status()
        logger.info(f"✓ Imported: {article['title'][:60]}")
        return True

    except requests.HTTPError as e:
        logger.error(f"✗ HTTP error {e.response.status_code}: {article['title'][:60]}")
        logger.error(f"  Response: {e.response.text[:200]}")
        return False
    except Exception as e:
        logger.error(f"✗ Failed: {article['title'][:60]} - {str(e)[:100]}")
        return False


def main():
    api_url = "http://localhost:8081"

    logger.info("=" * 80)
    logger.info("Manual News Import - High-Quality Curated Articles")
    logger.info("=" * 80)

    # Get existing articles
    existing_urls = get_existing_articles(api_url)

    # Filter articles to import
    to_import = [article for article in CURATED_ARTICLES if article["url"] not in existing_urls]

    logger.info(f"\nTotal curated articles: {len(CURATED_ARTICLES)}")
    logger.info(f"Already in database: {len(CURATED_ARTICLES) - len(to_import)}")
    logger.info(f"To import: {len(to_import)}")

    if not to_import:
        logger.info("\n✓ All articles already imported!")
        return 0

    # Import articles
    logger.info("\n" + "=" * 80)
    logger.info("Importing articles...")
    logger.info("=" * 80 + "\n")

    success = 0
    failed = 0

    for article in to_import:
        if import_article(api_url, article):
            success += 1
        else:
            failed += 1

    # Summary
    logger.info("\n" + "=" * 80)
    logger.info("Import Summary")
    logger.info("=" * 80)
    logger.info(f"Success: {success}/{len(to_import)}")
    logger.info(f"Failed: {failed}/{len(to_import)}")
    logger.info(f"Success rate: {(success/max(1, len(to_import)))*100:.1f}%")
    logger.info("=" * 80)

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
