#!/usr/bin/env python3
"""
Relationship Data Integrity Verification Suite

Validates all relationship data across transformed files:
- entity_coappearances.json
- entity_network_full.json
- document_to_entities.json
- entity_to_documents.json

Verification Checks:
1. Bidirectional Consistency: document_to_entities ↔ entity_to_documents match
2. Network Integrity: All edge sources/targets exist as nodes
3. Co-appearance Validity: All entity pairs exist in network
4. Weight Consistency: Edge weights match co-appearance counts
5. No Self-Loops: No entity connected to itself
6. Bidirectional Edges: A→B implies B→A with same weight

Usage:
    python scripts/verification/verify_relationships.py [--verbose]
"""

import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Set, Tuple
from collections import defaultdict

# Color codes for terminal output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'

class RelationshipVerifier:
    def __init__(self, data_dir: Path, verbose: bool = False):
        self.data_dir = data_dir
        self.verbose = verbose
        self.errors = []
        self.warnings = []
        self.stats = {}

    def log(self, message: str, level: str = "INFO"):
        """Log message with color coding"""
        if level == "ERROR":
            print(f"{Colors.RED}✗ {message}{Colors.END}")
            self.errors.append(message)
        elif level == "WARNING":
            print(f"{Colors.YELLOW}⚠ {message}{Colors.END}")
            self.warnings.append(message)
        elif level == "SUCCESS":
            print(f"{Colors.GREEN}✓ {message}{Colors.END}")
        elif level == "INFO":
            if self.verbose:
                print(f"{Colors.BLUE}ℹ {message}{Colors.END}")
        else:
            print(message)

    def load_json(self, filename: str) -> dict:
        """Load and parse JSON file"""
        filepath = self.data_dir / filename
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            self.log(f"Failed to load {filename}: {e}", "ERROR")
            return {}

    def verify_bidirectional_consistency(self, doc_to_ent: dict, ent_to_doc: dict) -> bool:
        """
        Verify that document_to_entities and entity_to_documents are consistent.

        For every document→entity mapping, there must be a corresponding entity→document mapping.
        """
        print(f"\n{Colors.BOLD}1. Bidirectional Consistency Check{Colors.END}")
        print("=" * 60)

        doc_to_ent_data = doc_to_ent.get('document_to_entities', {})
        ent_to_doc_data = ent_to_doc.get('entity_to_documents', {})

        self.log(f"Documents in doc_to_ent: {len(doc_to_ent_data):,}")
        self.log(f"Entities in ent_to_doc: {len(ent_to_doc_data):,}")

        # Build reverse index from entity_to_documents
        expected_doc_to_ent = defaultdict(set)
        for entity, docs in ent_to_doc_data.items():
            entity_lower = entity.lower()
            for doc in docs:
                expected_doc_to_ent[doc].add(entity_lower)

        # Check forward direction: doc→ent matches ent→doc
        missing_in_ent_to_doc = []
        extra_in_doc_to_ent = []

        for doc_id, entities in doc_to_ent_data.items():
            for entity in entities:
                entity_lower = entity.lower()

                # Check if entity exists in ent_to_doc
                if entity_lower not in ent_to_doc_data:
                    missing_in_ent_to_doc.append((doc_id, entity))
                    continue

                # Check if doc exists in entity's document list
                if doc_id not in ent_to_doc_data[entity_lower]:
                    extra_in_doc_to_ent.append((doc_id, entity))

        # Check reverse direction: ent→doc matches doc→ent
        missing_in_doc_to_ent = []
        extra_in_ent_to_doc = []

        for entity, docs in ent_to_doc_data.items():
            for doc_id in docs:
                # Check if doc exists in doc_to_ent
                if doc_id not in doc_to_ent_data:
                    missing_in_doc_to_ent.append((doc_id, entity))
                    continue

                # Check if entity exists in doc's entity list (case-insensitive)
                doc_entities = [e.lower() for e in doc_to_ent_data[doc_id]]
                if entity.lower() not in doc_entities:
                    extra_in_ent_to_doc.append((doc_id, entity))

        # Report findings
        self.stats['bidirectional'] = {
            'missing_in_ent_to_doc': len(missing_in_ent_to_doc),
            'extra_in_doc_to_ent': len(extra_in_doc_to_ent),
            'missing_in_doc_to_ent': len(missing_in_doc_to_ent),
            'extra_in_ent_to_doc': len(extra_in_ent_to_doc)
        }

        if missing_in_ent_to_doc:
            self.log(f"Found {len(missing_in_ent_to_doc):,} doc→entity mappings missing in entity_to_documents", "ERROR")
            if self.verbose and len(missing_in_ent_to_doc) <= 10:
                for doc_id, entity in missing_in_ent_to_doc[:10]:
                    self.log(f"  {doc_id} → {entity}", "INFO")

        if extra_in_doc_to_ent:
            self.log(f"Found {len(extra_in_doc_to_ent):,} doc→entity mappings not in entity_to_documents", "ERROR")
            if self.verbose and len(extra_in_doc_to_ent) <= 10:
                for doc_id, entity in extra_in_doc_to_ent[:10]:
                    self.log(f"  {doc_id} → {entity}", "INFO")

        if missing_in_doc_to_ent:
            self.log(f"Found {len(missing_in_doc_to_ent):,} entity→doc mappings missing in document_to_entities", "ERROR")
            if self.verbose and len(missing_in_doc_to_ent) <= 10:
                for doc_id, entity in missing_in_doc_to_ent[:10]:
                    self.log(f"  {entity} → {doc_id}", "INFO")

        if extra_in_ent_to_doc:
            self.log(f"Found {len(extra_in_ent_to_doc):,} entity→doc mappings not in document_to_entities", "ERROR")
            if self.verbose and len(extra_in_ent_to_doc) <= 10:
                for doc_id, entity in extra_in_ent_to_doc[:10]:
                    self.log(f"  {entity} → {doc_id}", "INFO")

        is_consistent = (
            not missing_in_ent_to_doc and
            not extra_in_doc_to_ent and
            not missing_in_doc_to_ent and
            not extra_in_ent_to_doc
        )

        if is_consistent:
            self.log("Bidirectional consistency verified", "SUCCESS")

        return is_consistent

    def verify_network_integrity(self, network: dict) -> bool:
        """
        Verify that all edge sources/targets exist as nodes in the network.
        """
        print(f"\n{Colors.BOLD}2. Network Integrity Check{Colors.END}")
        print("=" * 60)

        nodes = {node['id']: node for node in network.get('nodes', [])}
        edges = network.get('edges', [])

        self.log(f"Total nodes: {len(nodes):,}")
        self.log(f"Total edges: {len(edges):,}")

        missing_sources = []
        missing_targets = []

        for edge in edges:
            source = edge.get('source')
            target = edge.get('target')

            if source not in nodes:
                missing_sources.append(source)

            if target not in nodes:
                missing_targets.append(target)

        self.stats['network_integrity'] = {
            'total_nodes': len(nodes),
            'total_edges': len(edges),
            'missing_sources': len(set(missing_sources)),
            'missing_targets': len(set(missing_targets))
        }

        if missing_sources:
            unique_missing = set(missing_sources)
            self.log(f"Found {len(unique_missing):,} edges with missing source nodes", "ERROR")
            if self.verbose:
                for source in list(unique_missing)[:10]:
                    self.log(f"  Missing source: {source}", "INFO")

        if missing_targets:
            unique_missing = set(missing_targets)
            self.log(f"Found {len(unique_missing):,} edges with missing target nodes", "ERROR")
            if self.verbose:
                for target in list(unique_missing)[:10]:
                    self.log(f"  Missing target: {target}", "INFO")

        is_valid = not missing_sources and not missing_targets

        if is_valid:
            self.log("Network integrity verified", "SUCCESS")

        return is_valid

    def verify_coappearance_validity(self, coappearances: dict, network: dict) -> bool:
        """
        Verify that all entity pairs in co-appearances exist in the network.
        """
        print(f"\n{Colors.BOLD}3. Co-appearance Validity Check{Colors.END}")
        print("=" * 60)

        nodes = {node['id']: node for node in network.get('nodes', [])}
        coapp_list = coappearances.get('coappearances', [])

        self.log(f"Total co-appearance pairs: {len(coapp_list):,}")

        missing_entities = set()
        invalid_pairs = []

        for coapp in coapp_list:
            entity_a_id = coapp.get('entity_a', {}).get('id')
            entity_b_id = coapp.get('entity_b', {}).get('id')

            if entity_a_id not in nodes:
                missing_entities.add(entity_a_id)
                invalid_pairs.append((entity_a_id, entity_b_id))

            if entity_b_id not in nodes:
                missing_entities.add(entity_b_id)
                invalid_pairs.append((entity_a_id, entity_b_id))

        self.stats['coappearance_validity'] = {
            'total_pairs': len(coapp_list),
            'missing_entities': len(missing_entities),
            'invalid_pairs': len(invalid_pairs)
        }

        if missing_entities:
            self.log(f"Found {len(missing_entities):,} entities in co-appearances missing from network", "ERROR")
            if self.verbose:
                for entity_id in list(missing_entities)[:10]:
                    self.log(f"  Missing entity: {entity_id}", "INFO")

        is_valid = not missing_entities

        if is_valid:
            self.log("Co-appearance validity verified", "SUCCESS")

        return is_valid

    def verify_weight_consistency(self, coappearances: dict, network: dict) -> bool:
        """
        Verify that edge weights in network match co-appearance counts.
        """
        print(f"\n{Colors.BOLD}4. Weight Consistency Check{Colors.END}")
        print("=" * 60)

        # Build co-appearance count map
        coapp_counts = {}
        for coapp in coappearances.get('coappearances', []):
            entity_a_id = coapp.get('entity_a', {}).get('id')
            entity_b_id = coapp.get('entity_b', {}).get('id')
            count = coapp.get('count', 0)

            # Store both directions
            key1 = (entity_a_id, entity_b_id)
            key2 = (entity_b_id, entity_a_id)
            coapp_counts[key1] = count
            coapp_counts[key2] = count

        self.log(f"Co-appearance pairs indexed: {len(coapp_counts):,}")

        # Check network edges
        edges = network.get('edges', [])
        weight_mismatches = []
        missing_coappearances = []

        for edge in edges:
            source = edge.get('source')
            target = edge.get('target')
            weight = edge.get('weight', 0)

            key = (source, target)

            if key not in coapp_counts:
                missing_coappearances.append((source, target, weight))
            elif coapp_counts[key] != weight:
                weight_mismatches.append((source, target, weight, coapp_counts[key]))

        self.stats['weight_consistency'] = {
            'total_edges_checked': len(edges),
            'weight_mismatches': len(weight_mismatches),
            'missing_coappearances': len(missing_coappearances)
        }

        if weight_mismatches:
            self.log(f"Found {len(weight_mismatches):,} edges with mismatched weights", "ERROR")
            if self.verbose:
                for source, target, edge_weight, coapp_count in weight_mismatches[:10]:
                    self.log(f"  {source} → {target}: edge={edge_weight}, coapp={coapp_count}", "INFO")

        if missing_coappearances:
            # This is expected for edges below threshold
            self.log(f"Found {len(missing_coappearances):,} edges without co-appearance records (may be below threshold)", "WARNING")
            if self.verbose:
                for source, target, weight in missing_coappearances[:5]:
                    self.log(f"  {source} → {target}: weight={weight}", "INFO")

        is_consistent = not weight_mismatches

        if is_consistent:
            self.log("Weight consistency verified", "SUCCESS")

        return is_consistent

    def verify_no_self_loops(self, network: dict) -> bool:
        """
        Verify that no entity is connected to itself.
        """
        print(f"\n{Colors.BOLD}5. Self-Loop Check{Colors.END}")
        print("=" * 60)

        edges = network.get('edges', [])
        self_loops = []

        for edge in edges:
            source = edge.get('source')
            target = edge.get('target')

            if source == target:
                self_loops.append((source, edge.get('weight', 0)))

        self.stats['self_loops'] = {
            'total_edges_checked': len(edges),
            'self_loops_found': len(self_loops)
        }

        if self_loops:
            self.log(f"Found {len(self_loops):,} self-loop edges", "ERROR")
            if self.verbose:
                for entity_id, weight in self_loops[:10]:
                    self.log(f"  {entity_id} → {entity_id} (weight={weight})", "INFO")
        else:
            self.log("No self-loops found", "SUCCESS")

        return not self_loops

    def verify_bidirectional_edges(self, network: dict) -> bool:
        """
        Verify that A→B implies B→A with the same weight.
        """
        print(f"\n{Colors.BOLD}6. Bidirectional Edge Check{Colors.END}")
        print("=" * 60)

        edges = network.get('edges', [])

        # Build edge map
        edge_map = {}
        for edge in edges:
            source = edge.get('source')
            target = edge.get('target')
            weight = edge.get('weight', 0)

            key = (source, target)
            edge_map[key] = weight

        self.log(f"Total edges: {len(edges):,}")

        missing_reverse = []
        weight_mismatches = []

        for (source, target), weight in edge_map.items():
            reverse_key = (target, source)

            if reverse_key not in edge_map:
                missing_reverse.append((source, target, weight))
            elif edge_map[reverse_key] != weight:
                weight_mismatches.append((source, target, weight, edge_map[reverse_key]))

        self.stats['bidirectional_edges'] = {
            'total_edges': len(edges),
            'unique_edges': len(edge_map),
            'missing_reverse': len(missing_reverse),
            'weight_mismatches': len(weight_mismatches)
        }

        if missing_reverse:
            self.log(f"Found {len(missing_reverse):,} edges missing reverse edges", "ERROR")
            if self.verbose:
                for source, target, weight in missing_reverse[:10]:
                    self.log(f"  {source} → {target} (weight={weight}) has no reverse", "INFO")

        if weight_mismatches:
            self.log(f"Found {len(weight_mismatches):,} edge pairs with mismatched weights", "ERROR")
            if self.verbose:
                for source, target, weight1, weight2 in weight_mismatches[:10]:
                    self.log(f"  {source} → {target}: {weight1} vs {target} → {source}: {weight2}", "INFO")

        is_valid = not missing_reverse and not weight_mismatches

        if is_valid:
            self.log("Bidirectional edges verified", "SUCCESS")

        return is_valid

    def run_all_checks(self) -> dict:
        """Run all verification checks and return results"""
        print(f"\n{Colors.BOLD}{'='*60}")
        print("RELATIONSHIP DATA INTEGRITY VERIFICATION")
        print(f"{'='*60}{Colors.END}")
        print(f"Started: {datetime.now().isoformat()}\n")

        # Load all data files
        print(f"{Colors.BOLD}Loading data files...{Colors.END}")
        doc_to_ent = self.load_json('document_to_entities.json')
        ent_to_doc = self.load_json('entity_to_documents.json')
        coappearances = self.load_json('entity_coappearances.json')
        network = self.load_json('entity_network_full.json')

        if not all([doc_to_ent, ent_to_doc, coappearances, network]):
            self.log("Failed to load required data files", "ERROR")
            return {'status': 'failed', 'errors': self.errors}

        # Run all checks
        results = {
            'bidirectional_consistency': self.verify_bidirectional_consistency(doc_to_ent, ent_to_doc),
            'network_integrity': self.verify_network_integrity(network),
            'coappearance_validity': self.verify_coappearance_validity(coappearances, network),
            'weight_consistency': self.verify_weight_consistency(coappearances, network),
            'no_self_loops': self.verify_no_self_loops(network),
            'bidirectional_edges': self.verify_bidirectional_edges(network)
        }

        # Summary
        print(f"\n{Colors.BOLD}{'='*60}")
        print("VERIFICATION SUMMARY")
        print(f"{'='*60}{Colors.END}")

        passed = sum(1 for v in results.values() if v)
        total = len(results)

        for check, passed in results.items():
            status = f"{Colors.GREEN}PASSED{Colors.END}" if passed else f"{Colors.RED}FAILED{Colors.END}"
            print(f"{check.replace('_', ' ').title():.<40} {status}")

        print(f"\n{Colors.BOLD}Overall:{Colors.END} {passed}/{total} checks passed")
        print(f"{Colors.BOLD}Errors:{Colors.END} {len(self.errors)}")
        print(f"{Colors.BOLD}Warnings:{Colors.END} {len(self.warnings)}")

        return {
            'status': 'passed' if passed == total else 'failed',
            'checks_passed': passed,
            'checks_total': total,
            'results': results,
            'stats': self.stats,
            'errors': self.errors,
            'warnings': self.warnings,
            'timestamp': datetime.now().isoformat()
        }

def main():
    import argparse

    parser = argparse.ArgumentParser(description='Verify relationship data integrity')
    parser.add_argument('--verbose', '-v', action='store_true', help='Enable verbose output')
    parser.add_argument('--data-dir', type=str, default='data/transformed', help='Data directory path')
    parser.add_argument('--output', '-o', type=str, help='Output JSON report file')

    args = parser.parse_args()

    # Resolve data directory
    if Path(args.data_dir).is_absolute():
        data_dir = Path(args.data_dir)
    else:
        # Relative to script location
        script_dir = Path(__file__).parent
        data_dir = script_dir / '..' / '..' / args.data_dir
        data_dir = data_dir.resolve()

    if not data_dir.exists():
        print(f"{Colors.RED}Error: Data directory not found: {data_dir}{Colors.END}")
        sys.exit(1)

    # Run verification
    verifier = RelationshipVerifier(data_dir, verbose=args.verbose)
    results = verifier.run_all_checks()

    # Save results if output specified
    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2)
        print(f"\n{Colors.GREEN}Results saved to: {output_path}{Colors.END}")

    # Exit with error code if checks failed
    sys.exit(0 if results['status'] == 'passed' else 1)

if __name__ == '__main__':
    main()
