#!/bin/bash
# Quick Biography Lookup Test
# Tests that entity names can find their biographies

python3 -c "
import json

# Load data
with open('data/md/entities/ENTITIES_INDEX.json') as f:
    entities = {e['name'] for e in json.load(f)['entities'] if e.get('name')}

with open('data/metadata/entity_biographies.json') as f:
    bios = set(json.load(f)['entities'].keys())

# Test key entities
tests = ['Maxwell, Ghislaine', 'Epstein, Jeffrey', 'William Clinton', 'Prince Andrew', 'Nadia']
passed = sum(1 for t in tests if t in entities and t in bios)

print(f'✓ Biography Lookup Test: {passed}/{len(tests)} passed')
if passed == len(tests):
    print('✅ All lookups working!')
    exit(0)
else:
    print('❌ Some lookups failing')
    exit(1)
"
