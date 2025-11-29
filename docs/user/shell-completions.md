# Shell Completions for epstein-cli

**Quick Summary**: Shell completions provide tab-completion for the `epstein-cli` command, making it easier to discover and use available commands and options. .

**Category**: User
**Status**: Active
**Last Updated**: 2025-11-24

**Key Points**:
- **Tab completion** for all commands and subcommands
- **Option completion** for flags and arguments
- **Choice completion** for predefined values (document types, shells, etc.)
- **Context-aware suggestions** based on current command
- **Support for bash, zsh, and fish shells**

---

Shell completions provide tab-completion for the `epstein-cli` command, making it easier to discover and use available commands and options.

## Features

- **Tab completion** for all commands and subcommands
- **Option completion** for flags and arguments
- **Choice completion** for predefined values (document types, shells, etc.)
- **Context-aware suggestions** based on current command
- **Support for bash, zsh, and fish shells**

## Quick Installation

### Automatic Installation (Recommended)

Run the installation script which will detect your shell automatically:

```bash
./install-completions.sh
```

Or specify your shell explicitly:

```bash
./install-completions.sh bash   # For bash
./install-completions.sh zsh    # For zsh
./install-completions.sh fish   # For fish
```

### Manual Installation

You can also install completions using the CLI itself:

```bash
# For bash
python3 epstein-cli.py --install-completion bash

# For zsh
python3 epstein-cli.py --install-completion zsh

# For fish
python3 epstein-cli.py --install-completion fish
```

## Shell-Specific Setup

### Bash

**Option 1: User Installation**

1. Add to your `~/.bashrc`:

```bash
source /path/to/epstein/completions/epstein-cli.bash
```

2. Reload your shell:

```bash
source ~/.bashrc
```

**Option 2: System-Wide Installation**

```bash
sudo cp completions/epstein-cli.bash /etc/bash_completion.d/
```

Then start a new shell session.

### Zsh

**Option 1: User Installation**

1. Add to your `~/.zshrc` (before `compinit`):

```zsh
fpath=(/path/to/epstein/completions $fpath)
autoload -U compinit && compinit
```

2. Reload your shell:

```bash
source ~/.zshrc
```

**Option 2: User Completions Directory**

```bash
mkdir -p ~/.zsh/completions
cp completions/_epstein-cli ~/.zsh/completions/
```

Then add to `~/.zshrc`:

```zsh
fpath=(~/.zsh/completions $fpath)
autoload -U compinit && compinit
```

### Fish

**User Installation**

```bash
mkdir -p ~/.config/fish/completions
cp completions/epstein-cli.fish ~/.config/fish/completions/
```

Completions will activate automatically on next shell start.

**System-Wide Installation**

```bash
sudo cp completions/epstein-cli.fish /usr/share/fish/vendor_completions.d/
```

## Usage Examples

Once installed, you can use tab completion:

### Basic Command Completion

```bash
$ epstein-cli [TAB]
search    stats    list    validate    --version    --install-completion

$ epstein-cli s[TAB]
search    stats
```

### Option Completion

```bash
$ epstein-cli search --[TAB]
--entity         --type        --connections    --multiple

$ epstein-cli search --t[TAB]
--type
```

### Document Type Completion

```bash
$ epstein-cli search --type [TAB]
email               court_filing       financial
flight_log          contact_book       investigative
legal_agreement     personal           media
administrative      unknown
```

### List Resource Completion

```bash
$ epstein-cli list [TAB]
entities    types    sources
```

## Troubleshooting

### Completions Not Working

**Bash:**

1. Verify bash-completion is installed:
   ```bash
   # Ubuntu/Debian
   sudo apt-get install bash-completion

   # macOS (Homebrew)
   brew install bash-completion@2
   ```

2. Check if completions are sourced:
   ```bash
   complete -p epstein-cli
   ```
   Should output the completion function.

3. Reload your shell:
   ```bash
   source ~/.bashrc
   ```

**Zsh:**

1. Ensure completions directory is in fpath:
   ```zsh
   echo $fpath
   ```

2. Rebuild completion cache:
   ```zsh
   rm -f ~/.zcompdump
   compinit
   ```

3. Check completion is loaded:
   ```zsh
   which _epstein-cli
   ```

**Fish:**

1. Check completions directory:
   ```bash
   ls ~/.config/fish/completions/epstein-cli.fish
   ```

2. Restart fish:
   ```bash
   exec fish
   ```

### argcomplete Not Installed

If you see an error about argcomplete not being installed:

```bash
pip3 install argcomplete
```

Or install from requirements:

```bash
pip3 install -r server/requirements.txt
```

### Completion Generating Wrong Suggestions

1. Regenerate completions:
   ```bash
   ./install-completions.sh [your-shell]
   ```

2. Clear completion cache (zsh):
   ```zsh
   rm ~/.zcompdump*
   compinit
   ```

## Verification

Test that completions are working:

```bash
# Should show available commands
epstein-cli [TAB][TAB]

# Should show search options
epstein-cli search --[TAB][TAB]

# Should show document types
epstein-cli search --type [TAB][TAB]
```

## Advanced Configuration

### Bash: Customize Completion Behavior

Add to `~/.bashrc`:

```bash
# Case-insensitive completion
bind 'set completion-ignore-case on'

# Show all completions immediately
bind 'set show-all-if-ambiguous on'

# Color completion listings
bind 'set colored-stats on'
```

### Zsh: Enhanced Completion Features

Add to `~/.zshrc`:

```zsh
# Case-insensitive completion
zstyle ':completion:*' matcher-list 'm:{a-zA-Z}={A-Za-z}'

# Menu selection
zstyle ':completion:*' menu select

# Colors in completion
zstyle ':completion:*' list-colors ${(s.:.)LS_COLORS}

# Descriptions
zstyle ':completion:*' verbose yes
zstyle ':completion:*:descriptions' format '%B%d%b'
```

### Fish: Completion Customization

Fish completions are automatically styled based on your theme.

## Uninstallation

To remove completions:

**Bash:**
```bash
# Remove from ~/.bashrc
sed -i '/epstein-cli.bash/d' ~/.bashrc

# Or remove system-wide
sudo rm /etc/bash_completion.d/epstein-cli.bash
```

**Zsh:**
```bash
# Remove from ~/.zshrc
sed -i '/epstein.*completions/d' ~/.zshrc

# Or remove from user completions
rm ~/.zsh/completions/_epstein-cli
```

**Fish:**
```bash
rm ~/.config/fish/completions/epstein-cli.fish
# Or system-wide
sudo rm /usr/share/fish/vendor_completions.d/epstein-cli.fish
```

## Development

### Adding New Completions

When adding new commands or options to `epstein-cli.py`:

1. Update the argument parser in the script
2. Regenerate completions:
   ```bash
   python3 epstein-cli.py --install-completion [shell]
   ```
3. Test the new completions
4. Update this documentation

### Custom Completion Functions

For dynamic completions (e.g., entity names from database), you can extend the CLI with custom completers. See `argcomplete` documentation for details.

## Further Reading

- [argcomplete documentation](https://github.com/kislyuk/argcomplete)
- [Bash completion guide](https://github.com/scop/bash-completion)
- [Zsh completion system](http://zsh.sourceforge.net/Doc/Release/Completion-System.html)
- [Fish completions](https://fishshell.com/docs/current/completions.html)

## Support

If you encounter issues:

1. Check this troubleshooting guide
2. Verify your shell and argcomplete versions
3. Open an issue on GitHub with:
   - Your shell and version (`echo $SHELL`, `bash --version`, etc.)
   - Error messages
   - Output of verification commands
