# Testing Shell Completions

**Quick Summary**: This guide covers how to test shell completions for the epstein-cli tool. .

**Category**: Developer
**Status**: Active
**Last Updated**: 2025-11-24

**Key Points**:
- Prerequisites
- Manual Testing
- Bash Testing
- Zsh Testing

---

This guide covers how to test shell completions for the epstein-cli tool.

## Prerequisites

1. **argcomplete installed**:
   ```bash
   pip install argcomplete
   ```

2. **Completions generated**:
   ```bash
   ./install-completions.sh
   ```

## Manual Testing

### Bash Testing

1. **Load completions in current shell**:
   ```bash
   source completions/epstein-cli.bash
   ```

2. **Test basic completion**:
   ```bash
   epstein-cli [TAB][TAB]
   # Expected: search  stats  list  validate  --version  --install-completion
   ```

3. **Test subcommand completion**:
   ```bash
   epstein-cli search --[TAB][TAB]
   # Expected: --entity  --type  --connections  --multiple
   ```

4. **Test option value completion**:
   ```bash
   epstein-cli search --type [TAB][TAB]
   # Expected: email  court_filing  financial  flight_log  ...
   ```

5. **Test partial matching**:
   ```bash
   epstein-cli s[TAB]
   # Expected: search  stats
   ```

### Zsh Testing

1. **Load completions**:
   ```zsh
   # Add to current session
   fpath=(/path/to/epstein/completions $fpath)
   autoload -U compinit && compinit
   ```

2. **Test completion**:
   ```zsh
   epstein-cli [TAB]
   # Should show menu with options
   ```

3. **Test with menu selection**:
   ```zsh
   # Enable menu selection if not already
   zstyle ':completion:*' menu select

   epstein-cli search --[TAB]
   # Should show menu of options
   ```

4. **Verify completion cache**:
   ```zsh
   # Force recompile
   rm ~/.zcompdump*
   compinit
   ```

### Fish Testing

1. **Copy completion file**:
   ```fish
   mkdir -p ~/.config/fish/completions
   cp completions/epstein-cli.fish ~/.config/fish/completions/
   ```

2. **Reload fish**:
   ```fish
   exec fish
   ```

3. **Test completion**:
   ```fish
   epstein-cli [TAB]
   # Should show completions
   ```

4. **Test option completion**:
   ```fish
   epstein-cli search --[TAB]
   # Should show available flags
   ```

## Automated Testing

### Completion Script Validation

```bash
# Test bash completion loads without errors
bash -c "source completions/epstein-cli.bash && echo 'Bash completion OK'"

# Test zsh completion loads
zsh -c "fpath=(completions \$fpath) && autoload -U compinit && compinit && echo 'Zsh completion OK'"

# Test fish completion syntax
fish -c "source completions/epstein-cli.fish && echo 'Fish completion OK'"
```

### Programmatic Testing

Create `test-completions.sh`:

```bash
#!/bin/bash
# Test completion generation and loading

set -e

echo "Testing completion generation..."

# Test bash generation
python3 epstein-cli.py --install-completion bash > /dev/null
if [ -f completions/epstein-cli.bash ]; then
    echo "✓ Bash completion file created"
else
    echo "✗ Bash completion file not found"
    exit 1
fi

# Test zsh generation
python3 epstein-cli.py --install-completion zsh > /dev/null
if [ -f completions/_epstein-cli ]; then
    echo "✓ Zsh completion file created"
else
    echo "✗ Zsh completion file not found"
    exit 1
fi

# Test fish generation
python3 epstein-cli.py --install-completion fish > /dev/null
if [ -f completions/epstein-cli.fish ]; then
    echo "✓ Fish completion file created"
else
    echo "✗ Fish completion file not found"
    exit 1
fi

# Test bash completion syntax
bash -n completions/epstein-cli.bash
echo "✓ Bash completion syntax valid"

# Test bash completion loads
bash -c "source completions/epstein-cli.bash" 2>/dev/null
echo "✓ Bash completion loads successfully"

echo ""
echo "All tests passed!"
```

## Common Issues and Solutions

### Issue: Completions not appearing

**Bash:**
```bash
# Check if completion is registered
complete -p epstein-cli

# If not, source the completion file
source completions/epstein-cli.bash

# Verify registration
complete -p epstein-cli
# Should output: complete -o nospace -o default -o bashdefault -F _epstein_cli_completion epstein-cli
```

**Zsh:**
```zsh
# Check fpath
echo $fpath
# Should include completions directory

# Rebuild completion cache
rm -f ~/.zcompdump*
compinit

# Check if completion function exists
which _epstein-cli
```

**Fish:**
```fish
# Check completion directory
ls ~/.config/fish/completions/epstein-cli.fish

# Restart fish
exec fish

# Debug completion
complete -C "epstein-cli " | head
```

### Issue: Wrong suggestions appearing

1. **Regenerate completions**:
   ```bash
   python3 epstein-cli.py --install-completion [shell]
   ```

2. **Clear cache**:
   ```bash
   # Bash: no cache

   # Zsh: clear completion cache
   rm ~/.zcompdump*

   # Fish: clear completion cache
   rm ~/.cache/fish/generated_completions/epstein-cli.fish
   ```

3. **Reload shell**:
   ```bash
   exec $SHELL
   ```

### Issue: Completions work for some options but not others

This usually means the argparse configuration is incomplete. Check:

1. All choices are properly defined in parser
2. Subparsers are correctly configured
3. argcomplete.autocomplete() is called before parse_args()

## Integration Testing

Test real-world usage scenarios:

```bash
# Scenario 1: Search workflow
epstein-cli search --entity "Cl[TAB]"
# Should complete partial entity names

# Scenario 2: Type selection
epstein-cli search --type e[TAB]
# Should complete "email"

# Scenario 3: Command discovery
epstein-cli l[TAB]
# Should complete "list"

# Scenario 4: Subcommand options
epstein-cli list [TAB]
# Should show: entities  types  sources
```

## Performance Testing

Test completion speed with timing:

```bash
# Time completion response
time -p bash -c 'source completions/epstein-cli.bash && complete -F _epstein_cli_completion epstein-cli'

# Should complete in < 0.1 seconds
```

## Cross-Platform Testing

### macOS

```bash
# Test with default bash (3.2)
/bin/bash --version

# Test with Homebrew bash (5.x)
/usr/local/bin/bash --version

# Test with zsh (default shell)
zsh --version
```

### Linux

```bash
# Test on Ubuntu/Debian
bash --version

# Test on RHEL/CentOS
bash --version
```

### Windows WSL

```bash
# Test in WSL bash
bash --version

# Test in WSL zsh
zsh --version
```

## Continuous Integration

Add to CI pipeline:

```yaml
# .github/workflows/test-completions.yml
name: Test Shell Completions

on: [push, pull_request]

jobs:
  test-completions:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v2

      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.9'

      - name: Install dependencies
        run: |
          pip install argcomplete

      - name: Generate completions
        run: |
          python3 epstein-cli.py --install-completion bash
          python3 epstein-cli.py --install-completion zsh
          python3 epstein-cli.py --install-completion fish

      - name: Validate bash completion
        run: |
          bash -n completions/epstein-cli.bash
          bash -c "source completions/epstein-cli.bash"

      - name: Check completion files exist
        run: |
          test -f completions/epstein-cli.bash
          test -f completions/_epstein-cli
          test -f completions/epstein-cli.fish
```

## Regression Testing

When modifying the CLI:

1. **Before changes**: Generate baseline completions
   ```bash
   python3 epstein-cli.py --install-completion bash
   cp completions/epstein-cli.bash completions/baseline.bash
   ```

2. **After changes**: Generate new completions
   ```bash
   python3 epstein-cli.py --install-completion bash
   ```

3. **Compare**: Check for expected differences
   ```bash
   diff completions/baseline.bash completions/epstein-cli.bash
   ```

## Best Practices

1. **Test in clean environment**: Use fresh shell session
2. **Test all shells**: Don't assume bash behavior equals zsh behavior
3. **Test partial completion**: Not just full words
4. **Test option values**: Especially choices and dynamic values
5. **Test error cases**: Invalid commands should not complete
6. **Document edge cases**: Note any completion limitations

## Debugging Completions

### Enable argcomplete debug mode

**Bash:**
```bash
export _ARC_DEBUG=1
epstein-cli [TAB]
# Shows debug output
```

**Zsh:**
```zsh
export _ARC_DEBUG=1
epstein-cli [TAB]
```

**Fish:**
```fish
set -x _ARC_DEBUG 1
epstein-cli [TAB]
```

### Trace completion execution

```bash
# Bash: enable trace
set -x
epstein-cli [TAB]
set +x

# Shows exactly what's being executed
```

## Verification Checklist

- [ ] Completions generated for all shells (bash, zsh, fish)
- [ ] Completion files load without errors
- [ ] Basic command completion works
- [ ] Subcommand completion works
- [ ] Option flag completion works
- [ ] Option value completion works (choices)
- [ ] Partial matching works
- [ ] No errors in debug mode
- [ ] Performance is acceptable (< 0.1s)
- [ ] Works on macOS, Linux, Windows WSL
- [ ] Documentation is complete and accurate

## See Also

- [argcomplete documentation](https://github.com/kislyuk/argcomplete)
- [Bash completion guide](https://github.com/scop/bash-completion)
- [Zsh completion system](http://zsh.sourceforge.net/Doc/Release/Completion-System.html)
- [Fish completions](https://fishshell.com/docs/current/completions.html)
