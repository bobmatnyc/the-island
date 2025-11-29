#!/usr/bin/env python3
"""
Add executive summaries to documentation files.

This script processes markdown files and adds standardized executive summaries
at the top of each file if they don't already have one.
"""

import os
import re
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Optional

# Summary template
SUMMARY_TEMPLATE = """# {title}

**Quick Summary**: {quick_summary}

**Category**: {category}
**Status**: {status}
**Last Updated**: {last_updated}

**Key Points**:
{key_points}

---

"""


def has_summary(content: str) -> bool:
    """Check if content already has an executive summary."""
    # Look for "Quick Summary" marker within first 500 chars
    return "**Quick Summary**:" in content[:500] or "Quick Summary:" in content[:500]


def extract_title(content: str, filename: str) -> str:
    """Extract or generate title from content."""
    # Look for first # heading
    match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
    if match:
        return match.group(1).strip()

    # Generate from filename
    title = filename.replace('.md', '').replace('_', ' ').replace('-', ' ')
    return title.title()


def categorize_file(filepath: Path) -> Tuple[str, str]:
    """Determine category and status based on file path and content."""
    path_str = str(filepath)

    # Category mapping
    if '/archive/' in path_str:
        return 'Archive', 'Historical'
    elif '/implementation-summaries/' in path_str or '/implementation/' in path_str:
        return 'Implementation', 'Complete'
    elif '/qa-reports/' in path_str or '/qa/' in path_str:
        return 'QA', 'Complete'
    elif '/linear-tickets/' in path_str:
        return 'Ticket', 'Complete'
    elif '/guides/' in path_str or 'GUIDE' in filepath.name.upper():
        return 'Guide', 'Active'
    elif 'QUICK' in filepath.name.upper() or 'QUICKSTART' in filepath.name.upper():
        return 'Quick Reference', 'Active'
    elif '/research/' in path_str:
        return 'Research', 'Complete'
    elif '/deployment/' in path_str:
        return 'Deployment', 'Active'
    elif '/developer/' in path_str:
        return 'Developer', 'Active'
    elif '/user/' in path_str:
        return 'User', 'Active'
    elif 'README' in filepath.name:
        return 'Index', 'Active'
    else:
        return 'Documentation', 'Active'


def extract_key_points(content: str, max_points: int = 5) -> List[str]:
    """Extract key points from content."""
    points = []

    # Look for bullet points in first section
    lines = content.split('\n')
    in_list = False
    for line in lines[:100]:  # Check first 100 lines
        stripped = line.strip()
        if stripped.startswith('- ') or stripped.startswith('* '):
            point = stripped[2:].strip()
            if len(point) > 10 and len(point) < 150:  # Reasonable length
                points.append(point)
                if len(points) >= max_points:
                    break

    # If no bullet points found, look for headings
    if not points:
        for line in lines[:50]:
            if line.startswith('##'):
                heading = line.replace('#', '').strip()
                if heading and len(heading) < 100:
                    points.append(heading)
                    if len(points) >= max_points:
                        break

    # Default points if nothing found
    if not points:
        points = [
            "Detailed documentation and reference information",
            "See content below for complete details"
        ]

    return points[:max_points]


def generate_quick_summary(content: str, category: str, filename: str) -> str:
    """Generate a quick 1-2 sentence summary."""

    # Category-specific templates
    if category == 'Implementation':
        return f"Implementation summary documenting changes, files modified, and testing results."
    elif category == 'QA':
        return f"Quality assurance report with test results, issues found, and recommendations."
    elif category == 'Ticket':
        return f"Linear ticket documentation tracking implementation status and deliverables."
    elif category == 'Archive':
        return f"Historical documentation archived for reference purposes."
    elif category == 'Guide':
        return f"Step-by-step guide and instructions for developers or users."
    elif category == 'Quick Reference':
        return f"Quick reference guide for rapid lookup of key information."
    elif category == 'Research':
        return f"Research analysis and findings documentation."

    # Try to extract first paragraph
    lines = content.split('\n')
    for i, line in enumerate(lines[:20]):
        stripped = line.strip()
        if stripped and not stripped.startswith('#') and len(stripped) > 30:
            # Found first paragraph
            sentences = stripped.split('.')
            if len(sentences) >= 2:
                return f"{sentences[0]}. {sentences[1]}."
            return stripped[:200] + "..."

    return "Documentation and reference information for the Epstein project."


def add_summary_to_file(filepath: Path, dry_run: bool = False) -> Tuple[bool, str]:
    """Add summary to a single file. Returns (success, message)."""
    try:
        # Read content
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        # Check if already has summary
        if has_summary(content):
            return True, "Already has summary"

        # Extract/generate components
        title = extract_title(content, filepath.name)
        category, status = categorize_file(filepath)
        key_points = extract_key_points(content)
        quick_summary = generate_quick_summary(content, category, filepath.name)

        # Format key points
        key_points_str = '\n'.join(f'- {point}' for point in key_points)

        # Generate summary
        summary = SUMMARY_TEMPLATE.format(
            title=title,
            quick_summary=quick_summary,
            category=category,
            status=status,
            last_updated=datetime.now().strftime('%Y-%m-%d'),
            key_points=key_points_str
        )

        # Remove existing title if present at start
        content_lines = content.split('\n')
        if content_lines and content_lines[0].startswith('# '):
            content = '\n'.join(content_lines[1:]).lstrip()

        # Combine
        new_content = summary + content

        # Write back
        if not dry_run:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(new_content)

        return True, "Summary added"

    except Exception as e:
        return False, f"Error: {str(e)}"


def process_directory(docs_dir: Path, dry_run: bool = False) -> Dict:
    """Process all markdown files in directory."""
    results = {
        'total': 0,
        'processed': 0,
        'skipped': 0,
        'errors': 0,
        'files': []
    }

    # Find all .md files
    md_files = list(docs_dir.rglob('*.md'))
    results['total'] = len(md_files)

    print(f"\nFound {len(md_files)} markdown files")
    print(f"Mode: {'DRY RUN' if dry_run else 'LIVE'}\n")

    for i, filepath in enumerate(md_files, 1):
        rel_path = filepath.relative_to(docs_dir)

        success, message = add_summary_to_file(filepath, dry_run)

        if success:
            if "Already has summary" in message:
                results['skipped'] += 1
                status = "SKIP"
            else:
                results['processed'] += 1
                status = "OK"
        else:
            results['errors'] += 1
            status = "ERROR"

        results['files'].append({
            'path': str(rel_path),
            'status': status,
            'message': message
        })

        # Progress report every 50 files
        if i % 50 == 0:
            print(f"Progress: {i}/{len(md_files)} - Processed: {results['processed']}, "
                  f"Skipped: {results['skipped']}, Errors: {results['errors']}")

    return results


def generate_report(results: Dict, output_path: Path):
    """Generate processing report."""
    report = f"""# Documentation Summary Addition Report

**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Summary Statistics

- **Total Files**: {results['total']}
- **Summaries Added**: {results['processed']}
- **Already Had Summaries**: {results['skipped']}
- **Errors**: {results['errors']}

## File Details

"""

    # Group by status
    by_status = {}
    for file_info in results['files']:
        status = file_info['status']
        if status not in by_status:
            by_status[status] = []
        by_status[status].append(file_info)

    for status in ['OK', 'SKIP', 'ERROR']:
        if status in by_status:
            report += f"\n### {status} ({len(by_status[status])} files)\n\n"
            for file_info in by_status[status][:50]:  # Limit to 50 per section
                report += f"- `{file_info['path']}` - {file_info['message']}\n"
            if len(by_status[status]) > 50:
                report += f"\n... and {len(by_status[status]) - 50} more files\n"

    # Write report
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(report)

    print(f"\n✓ Report written to: {output_path}")


def main():
    import argparse

    parser = argparse.ArgumentParser(description='Add executive summaries to documentation files')
    parser.add_argument('--docs-dir', type=Path,
                        default=Path('/Users/masa/Projects/epstein/docs'),
                        help='Documentation directory to process')
    parser.add_argument('--dry-run', action='store_true',
                        help='Run without making changes')
    parser.add_argument('--report', type=Path,
                        default=Path('/Users/masa/Projects/epstein/docs/SUMMARY_ADDITION_REPORT.md'),
                        help='Output report path')

    args = parser.parse_args()

    print("=" * 60)
    print("Documentation Summary Addition Tool")
    print("=" * 60)

    # Process files
    results = process_directory(args.docs_dir, args.dry_run)

    # Generate report
    generate_report(results, args.report)

    # Print summary
    print("\n" + "=" * 60)
    print("PROCESSING COMPLETE")
    print("=" * 60)
    print(f"Total Files:      {results['total']}")
    print(f"Summaries Added:  {results['processed']}")
    print(f"Already Had:      {results['skipped']}")
    print(f"Errors:           {results['errors']}")
    print("=" * 60)

    if args.dry_run:
        print("\n⚠️  DRY RUN - No files were modified")
        print("Run without --dry-run to apply changes")


if __name__ == '__main__':
    main()
