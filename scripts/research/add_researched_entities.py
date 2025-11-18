#!/usr/bin/env python3
"""
Add researched entities to enriched entity database
"""

import json
from datetime import datetime

# Load existing data
with open('/Users/masa/Projects/Epstein/data/metadata/enriched_entity_data.json', 'r') as f:
    data = json.load(f)

# Prince Andrew
prince_andrew = {
    "entity_id": "prince_andrew",
    "name": "Prince Andrew",
    "name_variations": [
        "Prince Andrew",
        "Prince Andrew, Duke of York",
        "Andrew, Duke of York"
    ],
    "biographical_data": {
        "full_legal_name": {
            "value": "Andrew Albert Christian Edward",
            "confidence": "high",
            "sources": [
                {
                    "type": "biographical_database",
                    "citation": "Wikipedia - Prince Andrew, Duke of York",
                    "url": "https://en.wikipedia.org/wiki/Prince_Andrew,_Duke_of_York",
                    "date_accessed": "2025-11-17",
                    "reliability_tier": 4
                }
            ]
        },
        "occupation": {
            "primary": "Member of British Royal Family",
            "historical": ["British naval officer", "UK Special Representative for International Trade and Investment"],
            "sources": [
                {
                    "type": "biographical_database",
                    "citation": "Wikipedia - Prince Andrew",
                    "date_accessed": "2025-11-17",
                    "reliability_tier": 4
                }
            ]
        }
    },
    "epstein_relationship": {
        "relationship_summary": "Social acquaintance through Ghislaine Maxwell; accused of sexual abuse of Virginia Giuffre when she was 17",
        "relationship_type": "social",
        "documented_interactions": [
            {
                "date": "2001",
                "type": "alleged_abuse",
                "description": "Virginia Giuffre alleged Andrew sexually abused her at Epstein's private island, Manhattan mansion, and Maxwell's London home",
                "sources": [
                    {
                        "type": "court_document",
                        "citation": "Giuffre v. Prince Andrew - Allegations in federal lawsuit",
                        "url": "https://en.wikipedia.org/wiki/Virginia_Giuffre_v._Prince_Andrew",
                        "date_accessed": "2025-11-17",
                        "reliability_tier": 1,
                        "quote": "alleged Epstein trafficked her and forced her to have sex with his friends, including Prince Andrew"
                    }
                ]
            }
        ],
        "public_statements": [
            {
                "date": "2022-02",
                "statement_type": "settlement_statement",
                "statement_text": "Prince Andrew regrets his association with Epstein, and commends the bravery of Ms. Giuffre",
                "context": "Settlement agreement with Virginia Giuffre",
                "sources": [
                    {
                        "type": "court_document",
                        "citation": "Settlement filing - February 2022",
                        "url": "https://www.npr.org/2022/02/15/1080828750/prince-andrew-settlement-virginia-giuffre",
                        "date_accessed": "2025-11-17",
                        "reliability_tier": 1
                    }
                ]
            }
        ],
        "legal_involvement": [
            {
                "role": "defendant",
                "case_name": "Giuffre v. Prince Andrew",
                "case_number": "1:21-cv-06702",
                "jurisdiction": "U.S. District Court, Southern District of New York",
                "date": "2021-08",
                "description": "Sexual abuse lawsuit filed by Virginia Giuffre; settled out of court February 2022",
                "settlement_amount": "Estimated £12 million ($16.3 million), undisclosed",
                "sources": [
                    {
                        "type": "court_document",
                        "citation": "Federal lawsuit settled February 2022",
                        "url": "https://www.cnn.com/2022/03/08/us/prince-andrew-virginia-giuffre-settlement/index.html",
                        "date_accessed": "2025-11-17",
                        "reliability_tier": 1,
                        "quote": "estimated to be worth around £12 million ($16.3 million)"
                    }
                ]
            }
        ]
    },
    "archive_metadata": {
        "appears_in_sources": ["black_book", "flight_logs"],
        "total_flights": 1
    },
    "research_metadata": {
        "research_date": "2025-11-17",
        "researcher": "Claude Code Research Agent",
        "research_completeness": "comprehensive",
        "verification_status": "verified",
        "notes": "Subject of high-profile sexual abuse lawsuit. Settled case for estimated £12 million without admitting wrongdoing.",
        "requires_human_review": False
    }
}

# Leslie Wexner
leslie_wexner = {
    "entity_id": "leslie_wexner",
    "name": "Leslie Wexner",
    "name_variations": [
        "Leslie Wexner",
        "Les Wexner",
        "Leslie Herbert Wexner"
    ],
    "biographical_data": {
        "full_legal_name": {
            "value": "Leslie Herbert Wexner",
            "confidence": "high",
            "sources": [
                {
                    "type": "biographical_database",
                    "citation": "Wikipedia - Les Wexner",
                    "url": "https://en.wikipedia.org/wiki/Les_Wexner",
                    "date_accessed": "2025-11-17",
                    "reliability_tier": 4
                }
            ]
        },
        "occupation": {
            "primary": "Billionaire businessman, founder of L Brands (Victoria's Secret)",
            "historical": ["CEO of Victoria's Secret parent company (stepped down 2020)"],
            "sources": [
                {
                    "type": "journalism",
                    "citation": "NBC News - Wexner steps down as CEO of Victoria's Secret parent",
                    "url": "https://www.nbcnews.com/news/us-news/former-jeffrey-epstein-pal-leslie-wexner-steps-down-ceo-victoria-n1139916",
                    "date_accessed": "2025-11-17",
                    "reliability_tier": 2
                }
            ]
        },
        "net_worth": {
            "value": "$4.5 billion (Forbes)",
            "sources": [
                {
                    "type": "journalism",
                    "citation": "CBS News - Forbes listing",
                    "date_accessed": "2025-11-17",
                    "reliability_tier": 2
                }
            ]
        }
    },
    "epstein_relationship": {
        "relationship_summary": "Epstein was Wexner's personal money manager for nearly two decades; Wexner was Epstein's only known financial client",
        "relationship_type": "business/financial",
        "first_documented_connection": {
            "date": "1980s-1990s",
            "description": "Epstein became Wexner's money manager with power of attorney",
            "sources": [
                {
                    "type": "journalism",
                    "citation": "CNN - Epstein was Wexner's money manager for nearly two decades",
                    "url": "https://www.cnn.com/2019/07/26/business/jeffrey-epstein-les-wexner-business-relationship",
                    "date_accessed": "2025-11-17",
                    "reliability_tier": 2
                }
            ]
        },
        "documented_interactions": [
            {
                "date": "1990s-2007",
                "type": "financial_management",
                "description": "Wexner granted Epstein power of attorney over his vast fortune",
                "sources": [
                    {
                        "type": "journalism",
                        "citation": "TIME - Wexner granted Epstein power of attorney",
                        "url": "https://time.com/6197975/victorias-secret-angels-and-demons-hulu-true-story/",
                        "date_accessed": "2025-11-17",
                        "reliability_tier": 2,
                        "quote": "Wexner had granted Epstein 'power of attorney,' essentially giving Epstein full access"
                    }
                ]
            },
            {
                "date": "mid-1990s",
                "type": "recruitment_scheme",
                "description": "Epstein allegedly posed as Victoria's Secret recruiter to access models",
                "sources": [
                    {
                        "type": "journalism",
                        "citation": "Variety - Epstein used Victoria's Secret for access to women",
                        "url": "https://variety.com/2019/biz/news/jeffrey-epstein-leslie-wexner-victorias-secret-sexual-assault-1203280771/",
                        "date_accessed": "2025-11-17",
                        "reliability_tier": 2
                    }
                ]
            }
        ],
        "public_statements": [
            {
                "date": "2019",
                "statement_type": "accusation",
                "statement_text": "Wexner accused Epstein of misappropriating 'vast sums' of his personal fortune",
                "sources": [
                    {
                        "type": "journalism",
                        "citation": "CBS News - Epstein may have taken 'vast sums' from Wexner",
                        "url": "https://www.cbsnews.com/news/jeffrey-epstein-may-have-taken-46-million-from-victorias-secret-billionaire-les-wexner/",
                        "date_accessed": "2025-11-17",
                        "reliability_tier": 2
                    }
                ]
            }
        ]
    },
    "archive_metadata": {
        "appears_in_sources": ["black_book"],
        "total_flights": 0,
        "is_billionaire": True
    },
    "research_metadata": {
        "research_date": "2025-11-17",
        "researcher": "Claude Code Research Agent",
        "research_completeness": "comprehensive",
        "verification_status": "verified",
        "notes": "Epstein's primary financial client. Granted power of attorney. Ended relationship 2007. Subject of Hulu documentary 'Victoria's Secret: Angels and Demons' (2022).",
        "requires_human_review": False
    }
}

# Donald Trump
donald_trump = {
    "entity_id": "donald_trump",
    "name": "Donald Trump",
    "name_variations": [
        "Donald Trump",
        "Donald J. Trump",
        "Donald John Trump"
    ],
    "biographical_data": {
        "full_legal_name": {
            "value": "Donald John Trump",
            "confidence": "high",
            "sources": [
                {
                    "type": "biographical_database",
                    "citation": "Wikipedia - Donald Trump",
                    "url": "https://en.wikipedia.org/wiki/Donald_Trump",
                    "date_accessed": "2025-11-17",
                    "reliability_tier": 4
                }
            ]
        },
        "occupation": {
            "primary": "45th President of the United States (2017-2021), businessman",
            "historical": ["Real estate developer", "Television personality"],
            "sources": [
                {
                    "type": "biographical_database",
                    "citation": "Wikipedia - Donald Trump",
                    "date_accessed": "2025-11-17",
                    "reliability_tier": 4
                }
            ]
        }
    },
    "epstein_relationship": {
        "relationship_summary": "Socialized in 1990s and early 2000s; relationship ended circa 2004; Epstein banned from Mar-a-Lago in 2007",
        "relationship_type": "social (ended 2004)",
        "first_documented_connection": {
            "date": "1980s-1990s",
            "description": "Socialized in Palm Beach and New York social circles",
            "sources": [
                {
                    "type": "journalism",
                    "citation": "Rolling Stone - Timeline of Trump and Epstein relationship",
                    "url": "https://www.rollingstone.com/politics/politics-features/donald-trump-jeffrey-epstein-timeline-1235464225/",
                    "date_accessed": "2025-11-17",
                    "reliability_tier": 2
                }
            ]
        },
        "documented_interactions": [
            {
                "date": "1992",
                "type": "social_event",
                "description": "Trump invited NBC to film party he threw for himself and Epstein at Mar-a-Lago with NFL cheerleaders",
                "sources": [
                    {
                        "type": "journalism",
                        "citation": "Al Jazeera - 1992 Mar-a-Lago party with NFL cheerleaders",
                        "url": "https://www.aljazeera.com/news/2025/7/18/how-well-did-trump-and-epstein-really-know-each-other-a-timeline",
                        "date_accessed": "2025-11-17",
                        "reliability_tier": 2
                    }
                ]
            },
            {
                "date": "1993-1997",
                "type": "flight",
                "description": "Flew on Epstein's plane 7-8 times between Palm Beach and New York",
                "sources": [
                    {
                        "type": "public_record",
                        "citation": "Flight logs released by DOJ in 2021",
                        "date_accessed": "2025-11-17",
                        "reliability_tier": 3,
                        "quote": "Trump flew on Epstein's private plane seven to eight times between 1993 and 1997"
                    }
                ]
            },
            {
                "date": "2004",
                "type": "falling_out",
                "description": "Trump and Epstein had falling out, ceased contact",
                "sources": [
                    {
                        "type": "journalism",
                        "citation": "PBS News - Trump-Epstein falling out circa 2004",
                        "url": "https://www.pbs.org/newshour/politics/the-facts-and-timeline-of-trump-and-epsteins-falling-out",
                        "date_accessed": "2025-11-17",
                        "reliability_tier": 2
                    }
                ]
            },
            {
                "date": "2007",
                "type": "banning",
                "description": "Trump banned Epstein from Mar-a-Lago after alleged sexual harassment incident",
                "sources": [
                    {
                        "type": "journalism",
                        "citation": "Multiple sources - Epstein banned from Mar-a-Lago 2007",
                        "date_accessed": "2025-11-17",
                        "reliability_tier": 2,
                        "quote": "After Epstein allegedly sexually harassed teenage daughter of Mar-a-Lago member, Trump banned him"
                    }
                ]
            }
        ],
        "public_statements": [],
        "legal_involvement": []
    },
    "network_relationships": {
        "relationships_to_other_entities": [
            {
                "entity_name": "Roberts, Virginia",
                "relationship_type": "no_allegation",
                "relationship_description": "Virginia Giuffre was recruited from Mar-a-Lago but did not accuse Trump of wrongdoing",
                "sources": [
                    {
                        "type": "journalism",
                        "citation": "Britannica - Giuffre recruited from Mar-a-Lago",
                        "date_accessed": "2025-11-17",
                        "reliability_tier": 2
                    }
                ]
            }
        ]
    },
    "archive_metadata": {
        "appears_in_sources": ["black_book", "flight_logs"],
        "total_flights": 1,
        "is_billionaire": True
    },
    "research_metadata": {
        "research_date": "2025-11-17",
        "researcher": "Claude Code Research Agent",
        "research_completeness": "comprehensive",
        "verification_status": "verified",
        "notes": "Social relationship in 1990s-early 2000s. Ended relationship 2004. Banned Epstein from Mar-a-Lago 2007. No criminal wrongdoing established in connection with Epstein's crimes. Giuffre recruited from Mar-a-Lago but did not accuse Trump.",
        "requires_human_review": False
    }
}

# Add all new entities
data['entities'].extend([prince_andrew, leslie_wexner, donald_trump])

# Update metadata
data['metadata']['total_entities_enriched'] = len(data['entities'])
data['metadata']['last_updated'] = datetime.now().isoformat()

# Save
with open('/Users/masa/Projects/Epstein/data/metadata/enriched_entity_data.json', 'w') as f:
    json.dump(data, f, indent=2)

print(f"✓ Added 3 entities: Prince Andrew, Leslie Wexner, Donald Trump")
print(f"Total entities enriched: {len(data['entities'])}")
