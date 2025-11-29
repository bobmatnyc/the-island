#!/usr/bin/env python3
"""
Generate comprehensive documentation index for docs/README.md
"""

from pathlib import Path
from collections import defaultdict
from datetime import datetime
import re


def extract_summary_info(filepath: Path) -> dict:
    """Extract quick summary and category from a file."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read(1000)  # First 1000 chars should have summary

        info = {
            'title': filepath.stem.replace('_', ' ').replace('-', ' ').title(),
            'category': 'Documentation',
            'status': 'Active',
            'summary': 'Documentation file'
        }

        # Extract title
        title_match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
        if title_match:
            info['title'] = title_match.group(1).strip()

        # Extract category
        category_match = re.search(r'\*\*Category\*\*:\s*(.+)', content)
        if category_match:
            info['category'] = category_match.group(1).strip()

        # Extract status
        status_match = re.search(r'\*\*Status\*\*:\s*(.+)', content)
        if status_match:
            info['status'] = status_match.group(1).strip()

        # Extract quick summary
        summary_match = re.search(r'\*\*Quick Summary\*\*:\s*(.+)', content)
        if summary_match:
            info['summary'] = summary_match.group(1).strip()

        return info

    except Exception as e:
        return {
            'title': filepath.stem,
            'category': 'Documentation',
            'status': 'Active',
            'summary': f'Error reading file: {str(e)}'
        }


def categorize_by_directory(docs_dir: Path) -> dict:
    """Organize files by directory structure."""
    structure = defaultdict(list)

    for md_file in docs_dir.rglob('*.md'):
        if md_file.name == 'README.md':
            continue  # Skip README files

        rel_path = md_file.relative_to(docs_dir)
        parent_dir = rel_path.parent if rel_path.parent != Path('.') else Path('root')

        info = extract_summary_info(md_file)
        info['path'] = rel_path
        info['filename'] = md_file.name

        structure[str(parent_dir)].append(info)

    return structure


def generate_index(docs_dir: Path, output_path: Path):
    """Generate the comprehensive documentation index."""

    print("Scanning documentation files...")
    structure = categorize_by_directory(docs_dir)

    # Sort directories
    sorted_dirs = sorted(structure.keys())

    # Build index content
    index = f"""# Documentation Index

**Quick Summary**: Comprehensive index of all project documentation with categories and descriptions.

**Category**: Index
**Status**: Active
**Last Updated**: {datetime.now().strftime('%Y-%m-%d')}

**Key Points**:
- Complete documentation catalog
- Organized by directory and category
- Quick summaries for each document
- {sum(len(files) for files in structure.values())} total documents indexed
- Updated automatically

---

## Overview

This is the master index for all documentation in the Epstein project. Documents are organized by directory structure and categorized by type.

### Documentation Statistics

"""

    # Category counts
    category_counts = defaultdict(int)
    for files in structure.values():
        for file_info in files:
            category_counts[file_info['category']] += 1

    index += "**By Category:**\n"
    for category, count in sorted(category_counts.items(), key=lambda x: -x[1]):
        index += f"- {category}: {count} documents\n"

    index += f"\n**Total Documents**: {sum(category_counts.values())}\n\n"

    index += """---

## Quick Navigation

### Primary Categories

- [Implementation Summaries](#implementation-summaries) - Feature implementation documentation
- [QA Reports](#qa-reports) - Quality assurance and testing reports
- [Linear Tickets](#linear-tickets) - Linear ticket resolutions and tracking
- [Developer Guides](#developer) - Developer documentation and guides
- [Research](#research) - Research reports and analysis
- [Deployment](#deployment) - Deployment and operations documentation
- [Archive](#archive) - Historical and archived documentation

### Quick References

"""

    # Find all quick reference and guide files
    quick_refs = []
    for dir_path, files in structure.items():
        for file_info in files:
            if 'quick' in file_info['filename'].lower() or 'guide' in file_info['filename'].lower():
                quick_refs.append(file_info)

    for ref in sorted(quick_refs, key=lambda x: x['title'])[:20]:
        index += f"- [{ref['title']}]({ref['path']})\n"

    index += "\n---\n\n"

    # Generate directory sections
    index += "## Documentation by Directory\n\n"

    # Directory priority for ordering
    priority_dirs = [
        'root',
        'implementation-summaries',
        'qa-reports',
        'linear-tickets',
        'developer',
        'research',
        'deployment',
        'guides',
        'features',
        'archive'
    ]

    # Process priority directories first
    processed = set()
    for priority_dir in priority_dirs:
        for dir_path in sorted_dirs:
            if priority_dir in dir_path.lower() and dir_path not in processed:
                files = structure[dir_path]
                if files:
                    index += generate_directory_section(dir_path, files, docs_dir)
                    processed.add(dir_path)

    # Process remaining directories
    for dir_path in sorted_dirs:
        if dir_path not in processed:
            files = structure[dir_path]
            if files:
                index += generate_directory_section(dir_path, files, docs_dir)

    # Add search tips
    index += """
---

## Search Tips

### Finding Documentation

1. **Use browser search** (Cmd/Ctrl+F) on this page to find keywords
2. **Check category sections** for grouped documentation
3. **Review Quick References** for rapid lookup guides
4. **Explore subdirectory READMEs** for focused documentation areas

### Common Keywords

- **Implementation**: Feature builds, code changes, file modifications
- **QA**: Testing, verification, quality assurance
- **Quick Reference**: Fast lookup, command reference
- **Guide**: Step-by-step instructions, tutorials
- **Fix**: Bug fixes, issue resolutions
- **Migration**: Data migrations, schema changes
- **Deployment**: Production setup, operations

---

## Maintenance

This index is automatically generated. To regenerate:

```bash
python3 scripts/generate_docs_index.py
```

Last generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""

    # Write index
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(index)

    print(f"\n✓ Documentation index written to: {output_path}")
    print(f"  Total documents indexed: {sum(len(files) for files in structure.values())}")
    print(f"  Total directories: {len(structure)}")


def generate_directory_section(dir_path: str, files: list, docs_dir: Path) -> str:
    """Generate a section for a directory."""

    # Clean directory name for header
    if dir_path == 'root':
        dir_name = 'Root Documentation'
        anchor = 'root-documentation'
    else:
        dir_name = dir_path.replace('_', ' ').replace('-', ' ').title()
        anchor = dir_path.lower().replace('/', '-').replace('_', '-')

    section = f"### {dir_name}\n\n"
    section += f"**Location**: `docs/{dir_path}/`\n"
    section += f"**Documents**: {len(files)}\n\n"

    # Group by category
    by_category = defaultdict(list)
    for file_info in files:
        by_category[file_info['category']].append(file_info)

    # List files by category
    for category in sorted(by_category.keys()):
        if len(by_category) > 1:
            section += f"**{category}**:\n\n"

        category_files = sorted(by_category[category], key=lambda x: x['title'])
        for file_info in category_files[:30]:  # Limit to 30 files per category
            section += f"- **[{file_info['title']}]({file_info['path']})**"
            if file_info['summary'] and len(file_info['summary']) < 100:
                section += f" - {file_info['summary']}"
            section += "\n"

        if len(category_files) > 30:
            section += f"\n  ... and {len(category_files) - 30} more files\n"
        section += "\n"

    return section


def main():
    docs_dir = Path('/Users/masa/Projects/epstein/docs')
    output_path = docs_dir / 'README.md'

    print("=" * 60)
    print("Documentation Index Generator")
    print("=" * 60)

    generate_index(docs_dir, output_path)

    print("=" * 60)
    print("COMPLETE")
    print("=" * 60)


if __name__ == '__main__':
    main()
