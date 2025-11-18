#!/usr/bin/env python3
"""
Verification script for all bug fixes implemented on 2025-11-17

Tests:
1. Entity network has no duplicate first names
2. Network graph legend is updated with thickness levels
3. Progressive flight loading code is present
4. Document dropdown deduplication code is present
"""

import json
from pathlib import Path

def verify_entity_duplicates():
    """Verify no duplicate first names in entity network"""
    print("\n" + "="*60)
    print("TEST 1: Entity Network Duplicate Names")
    print("="*60)

    network_file = Path("/Users/masa/Projects/Epstein/data/metadata/entity_network.json")

    with open(network_file, 'r') as f:
        data = json.load(f)

    duplicates = []
    for node in data.get('nodes', []):
        name = node.get('name', '')
        parts = name.split()
        if len(parts) == 2 and parts[0] == parts[1]:
            duplicates.append(name)

    if duplicates:
        print(f"❌ FAILED: Found {len(duplicates)} duplicates:")
        for dup in duplicates:
            print(f"  - {dup}")
        return False
    else:
        print(f"✅ PASSED: No duplicate first names found")
        print(f"   Checked {len(data.get('nodes', []))} nodes")
        return True

def verify_progressive_loading():
    """Verify progressive flight loading code exists"""
    print("\n" + "="*60)
    print("TEST 2: Progressive Flight Loading")
    print("="*60)

    app_js = Path("/Users/masa/Projects/Epstein/server/web/app.js")

    with open(app_js, 'r') as f:
        content = f.read()

    checks = {
        'updateFlightLoadingProgress': 'updateFlightLoadingProgress' in content,
        'BATCH_SIZE': 'BATCH_SIZE = 10' in content,
        'BATCH_DELAY': 'BATCH_DELAY = 50' in content,
        'loadNextBatch': 'function loadNextBatch()' in content,
        'cancelFlightLoading': 'window.cancelFlightLoading' in content,
    }

    all_passed = all(checks.values())

    if all_passed:
        print("✅ PASSED: All progressive loading components found:")
        for check, status in checks.items():
            print(f"   ✓ {check}")
        return True
    else:
        print("❌ FAILED: Missing progressive loading components:")
        for check, status in checks.items():
            symbol = "✓" if status else "✗"
            print(f"   {symbol} {check}")
        return False

def verify_document_dropdown_fix():
    """Verify document dropdown deduplication code"""
    print("\n" + "="*60)
    print("TEST 3: Document Dropdown Deduplication")
    print("="*60)

    docs_js = Path("/Users/masa/Projects/Epstein/server/web/documents.js")

    with open(docs_js, 'r') as f:
        content = f.read()

    checks = {
        'Clear innerHTML': 'typeFilter.innerHTML = ' in content,
        'Set deduplication': '...new Set(data.filters.types)' in content,
        'Alphabetical sort': '.sort()' in content,
    }

    all_passed = all(checks.values())

    if all_passed:
        print("✅ PASSED: All dropdown fix components found:")
        for check, status in checks.items():
            print(f"   ✓ {check}")
        return True
    else:
        print("❌ FAILED: Missing dropdown fix components:")
        for check, status in checks.items():
            symbol = "✓" if status else "✗"
            print(f"   {symbol} {check}")
        return False

def verify_network_legend():
    """Verify network graph legend update"""
    print("\n" + "="*60)
    print("TEST 4: Network Graph Legend Enhancement")
    print("="*60)

    index_html = Path("/Users/masa/Projects/Epstein/server/web/index.html")

    with open(index_html, 'r') as f:
        content = f.read()

    checks = {
        '1-4 flights': '1-4 flights' in content,
        '5-9 flights': '5-9 flights' in content,
        '10-49 flights': '10-49 flights' in content,
        '50-99 flights': '50-99 flights' in content,
        '100+ flights': '100+ flights' in content,
        'Connection Type section': 'Connection Type' in content,
        'Flew Together': 'Flew Together' in content,
        'Blue color': '#0969da' in content,
    }

    all_passed = all(checks.values())

    if all_passed:
        print("✅ PASSED: All legend components found:")
        for check, status in checks.items():
            print(f"   ✓ {check}")
        return True
    else:
        print("❌ FAILED: Missing legend components:")
        for check, status in checks.items():
            symbol = "✓" if status else "✗"
            print(f"   {symbol} {check}")
        return False

def verify_edge_styling():
    """Verify network graph edge styling code"""
    print("\n" + "="*60)
    print("TEST 5: Network Graph Edge Styling")
    print("="*60)

    app_js = Path("/Users/masa/Projects/Epstein/server/web/app.js")

    with open(app_js, 'r') as f:
        content = f.read()

    checks = {
        'CONNECTION_TYPES': 'const CONNECTION_TYPES = {' in content,
        'getEdgeThickness': 'function getEdgeThickness(weight)' in content,
        'getEdgeColor': 'function getEdgeColor(edge)' in content,
        'Flew Together type': 'FLEW_TOGETHER' in content,
        'Blue color code': '#0969da' in content,
        'Thickness tiers': 'if (weight >= 100) return 8' in content,
    }

    all_passed = all(checks.values())

    if all_passed:
        print("✅ PASSED: All edge styling components found:")
        for check, status in checks.items():
            print(f"   ✓ {check}")
        return True
    else:
        print("❌ FAILED: Missing edge styling components:")
        for check, status in checks.items():
            symbol = "✓" if status else "✗"
            print(f"   {symbol} {check}")
        return False

def main():
    print("\n" + "="*60)
    print("EPSTEIN DOCUMENT ARCHIVE - BUG FIX VERIFICATION")
    print("="*60)
    print("Date: 2025-11-17")
    print("Session: Multiple bug fixes and UX improvements")

    results = []

    results.append(("Entity Duplicates", verify_entity_duplicates()))
    results.append(("Progressive Loading", verify_progressive_loading()))
    results.append(("Document Dropdown", verify_document_dropdown_fix()))
    results.append(("Network Legend", verify_network_legend()))
    results.append(("Edge Styling", verify_edge_styling()))

    print("\n" + "="*60)
    print("FINAL RESULTS")
    print("="*60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        symbol = "✅" if result else "❌"
        print(f"{symbol} {test_name}")

    print("\n" + "="*60)
    print(f"SUMMARY: {passed}/{total} tests passed ({int(passed/total*100)}%)")
    print("="*60)

    if passed == total:
        print("\n🎉 ALL TESTS PASSED! Ready for deployment.\n")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Review implementation.\n")
        return 1

if __name__ == "__main__":
    exit(main())
