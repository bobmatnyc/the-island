# epstein-cli Quick Reference

**Quick Summary**: Quick reference guide for rapid lookup of key information.

**Category**: Quick Reference
**Status**: Active
**Last Updated**: 2025-11-24

**Key Points**:
- `email` - Email communications
- `court_filing` - Court documents and filings
- `financial` - Financial records and statements
- `flight_log` - Flight log entries
- `contact_book` - Contact book entries

---

Quick reference for the unified CLI tool with shell completions.

## Installation

```bash
# One-time setup
./install-completions.sh

# Activate in your current shell
source ~/.bashrc   # bash
source ~/.zshrc    # zsh
exec fish          # fish
```

## Common Commands

### Search

```bash
# Search by entity name
epstein-cli search --entity "Clinton"
epstein-cli search -e "Maxwell"

# Search by document type
epstein-cli search --type email
epstein-cli search -t court_filing

# Find entity connections
epstein-cli search --connections "Ghislaine"
epstein-cli search -c "Epstein"

# Multi-entity search (documents mentioning ALL entities)
epstein-cli search --multiple "Clinton" "Epstein" "Maxwell"
epstein-cli search -m "Trump" "Epstein"
```

### Statistics

```bash
# Basic statistics
epstein-cli stats

# Detailed statistics with breakdowns
epstein-cli stats --detailed
```

### List Resources

```bash
# List entities
epstein-cli list entities
epstein-cli list entities --limit 100

# List document types
epstein-cli list types

# List data sources
epstein-cli list sources
```

### Validation

```bash
# Full validation
epstein-cli validate

# Quick validation only
epstein-cli validate --quick
```

## Document Types

Available values for `--type`:

- `email` - Email communications
- `court_filing` - Court documents and filings
- `financial` - Financial records and statements
- `flight_log` - Flight log entries
- `contact_book` - Contact book entries
- `investigative` - Investigative reports
- `legal_agreement` - Legal agreements and contracts
- `personal` - Personal correspondence
- `media` - Media articles and coverage
- `administrative` - Administrative documents
- `unknown` - Unclassified documents

## Options Reference

### Global Options

```bash
--version              Show version information
--install-completion   Install shell completions (bash/zsh/fish)
```

### Search Options

```bash
--entity, -e NAME      Search by entity name (case-insensitive)
--type, -t TYPE        Search by document type
--connections, -c NAME Show entity network connections
--multiple, -m NAMES   Search for multiple entities together
```

### Stats Options

```bash
--detailed            Show detailed statistics breakdown
```

### List Options

```bash
--limit NUMBER        Limit number of results (default: 50)
```

### Validate Options

```bash
--quick              Run quick validation only
```

## Tab Completion Examples

Once completions are installed:

```bash
# Press TAB to see all commands
epstein-cli [TAB]
→ search  stats  list  validate

# Press TAB to see search options
epstein-cli search --[TAB]
→ --entity  --type  --connections  --multiple

# Press TAB to see document types
epstein-cli search --type [TAB]
→ email  court_filing  financial  flight_log  ...

# Press TAB to see list resources
epstein-cli list [TAB]
→ entities  types  sources
```

## Common Workflows

### Investigate an Entity

```bash
# 1. Search for documents
epstein-cli search --entity "Clinton"

# 2. View connections
epstein-cli search --connections "Clinton"

# 3. Find co-mentions
epstein-cli search --multiple "Clinton" "Epstein"
```

### Explore Document Types

```bash
# 1. List available types
epstein-cli list types

# 2. Search by type
epstein-cli search --type email

# 3. View statistics
epstein-cli stats --detailed
```

### Data Quality Check

```bash
# 1. Quick validation
epstein-cli validate --quick

# 2. Full validation
epstein-cli validate

# 3. Check statistics
epstein-cli stats --detailed
```

## Output Format

All commands output human-readable formatted text:

```
========================================================================
SEARCH RESULTS (15 documents)
========================================================================

1. document_name.pdf
   Entity: Clinton, Bill
   Type: email | Entities: 12

2. another_document.pdf
   Entity: Clinton, Bill
   Type: court_filing | Entities: 8

...
```

## Tips

1. **Use Tab Completion**: Press TAB frequently to discover options
2. **Case Insensitive**: Entity searches are case-insensitive
3. **Partial Matching**: Entity names support partial matching
4. **Multiple Results**: Commands may return many results; use grep to filter
5. **Combine with Tools**: Pipe output to `grep`, `less`, or save to file

## Examples with Unix Tools

```bash
# Save search results
epstein-cli search --entity "Maxwell" > maxwell_results.txt

# Count results
epstein-cli search --type email | grep -c "^[0-9]"

# Filter by specific text
epstein-cli search --entity "Clinton" | grep -i "foundation"

# Page through results
epstein-cli list entities | less
```

## Troubleshooting

**Completions not working?**
```bash
# Reload shell configuration
source ~/.bashrc   # bash
source ~/.zshrc    # zsh
exec fish          # fish
```

**Command not found?**
```bash
# Use full path
python3 /path/to/epstein/epstein-cli.py search --entity "Clinton"

# Or add to PATH
export PATH="/path/to/epstein:$PATH"
```

**Import errors?**
```bash
# Ensure you're in the project directory
cd /path/to/epstein

# Or use full path
python3 /path/to/epstein/epstein-cli.py --help
```

## Getting Help

```bash
# General help
epstein-cli --help

# Command-specific help
epstein-cli search --help
epstein-cli stats --help
epstein-cli list --help
epstein-cli validate --help
```

## See Also

- [Full Shell Completions Guide](shell-completions.md)
- [Search Guide](searching.md)
- [Developer Setup](../developer/setup.md)
- [API Documentation](../developer/api/)
