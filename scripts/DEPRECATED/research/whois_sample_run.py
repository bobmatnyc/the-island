#!/usr/bin/env python3
"""
Sample WHOIS run on first 100 entities to demonstrate functionality
"""

import os
import sys

# Set environment variable to limit processing
os.environ["WHOIS_SAMPLE_RUN"] = "100"

# Import and run the main script
sys.path.insert(0, str(__file__).rsplit("/", 1)[0])

# Modify the script to use sample size
import basic_entity_whois

basic_entity_whois.MAX_ENTITIES_TO_PROCESS = 100

# Run
print("=" * 80)
print("SAMPLE WHOIS RUN - FIRST 100 ENTITIES")
print("=" * 80)
print()

basic_entity_whois.enrich_entities()
