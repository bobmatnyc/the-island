.PHONY: help version bump-patch bump-minor bump-major tag-release validate-version install dev test lint format \
        ocr-status extract-emails classify-docs build-network db-backup db-restore \
        build deploy logs commit push release clean status

# Colors for output
RED := \033[0;31m
GREEN := \033[0;32m
YELLOW := \033[1;33m
BLUE := \033[0;34m
NC := \033[0m # No Color

# Project paths
PROJECT_DIR := /Users/masa/Projects/Epstein
SCRIPTS_DIR := $(PROJECT_DIR)/scripts
DATA_DIR := $(PROJECT_DIR)/data
LOGS_DIR := $(PROJECT_DIR)/logs
VENV := $(PROJECT_DIR)/.venv
PYTHON := $(VENV)/bin/python3
PIP := $(VENV)/bin/pip

# Version file
VERSION_FILE := $(PROJECT_DIR)/VERSION
CURRENT_VERSION := $(shell cat $(VERSION_FILE) 2>/dev/null || echo "0.1.0")

# Database files
DEDUP_DB := $(DATA_DIR)/canonical/deduplication.db
METADATA_DIR := $(DATA_DIR)/metadata

# OCR status
OCR_PID_FILE := $(LOGS_DIR)/ocr_process.pid
OCR_LOG := $(LOGS_DIR)/ocr_house_oversight.log

help:
	@echo "$(BLUE)═══════════════════════════════════════════════════════════════$(NC)"
	@echo "$(BLUE)  Epstein Document Archive - Makefile Commands$(NC)"
	@echo "$(BLUE)═══════════════════════════════════════════════════════════════$(NC)"
	@echo ""
	@echo "$(GREEN)Version Management:$(NC)"
	@echo "  $(YELLOW)make version$(NC)         - Display current version ($(CURRENT_VERSION))"
	@echo "  $(YELLOW)make bump-patch$(NC)      - Increment patch version (X.Y.Z → X.Y.Z+1)"
	@echo "  $(YELLOW)make bump-minor$(NC)      - Increment minor version (X.Y.Z → X.Y+1.0)"
	@echo "  $(YELLOW)make bump-major$(NC)      - Increment major version (X.Y.Z → X+1.0.0)"
	@echo "  $(YELLOW)make tag-release$(NC)     - Create git tag with current version"
	@echo "  $(YELLOW)make validate-version$(NC) - Validate version consistency"
	@echo ""
	@echo "$(GREEN)Development:$(NC)"
	@echo "  $(YELLOW)make install$(NC)        - Install Python dependencies"
	@echo "  $(YELLOW)make dev$(NC)            - Start development server"
	@echo "  $(YELLOW)make test$(NC)           - Run test suite"
	@echo "  $(YELLOW)make lint$(NC)           - Run code linters"
	@echo "  $(YELLOW)make format$(NC)         - Auto-format code"
	@echo "  $(YELLOW)make clean$(NC)          - Clean temporary files"
	@echo ""
	@echo "$(GREEN)Data Processing:$(NC)"
	@echo "  $(YELLOW)make ocr-status$(NC)     - Check OCR processing status"
	@echo "  $(YELLOW)make extract-emails$(NC) - Run email extraction pipeline"
	@echo "  $(YELLOW)make classify-docs$(NC)  - Run document classification"
	@echo "  $(YELLOW)make build-network$(NC)  - Rebuild entity network graph"
	@echo "  $(YELLOW)make status$(NC)         - Show project status summary"
	@echo ""
	@echo "$(GREEN)Database:$(NC)"
	@echo "  $(YELLOW)make db-backup$(NC)      - Backup metadata databases"
	@echo "  $(YELLOW)make db-restore$(NC)     - Restore from backup"
	@echo ""
	@echo "$(GREEN)Git Operations:$(NC)"
	@echo "  $(YELLOW)make commit$(NC)         - Stage and commit changes"
	@echo "  $(YELLOW)make push$(NC)           - Push to remote repository"
	@echo "  $(YELLOW)make release$(NC)        - Complete release workflow"
	@echo ""
	@echo "$(GREEN)Logs & Monitoring:$(NC)"
	@echo "  $(YELLOW)make logs$(NC)           - Tail OCR processing logs"
	@echo "  $(YELLOW)make logs-downloads$(NC) - Tail download logs"
	@echo ""
	@echo "$(BLUE)═══════════════════════════════════════════════════════════════$(NC)"

# ═══════════════════════════════════════════════════════════════
# Version Management
# ═══════════════════════════════════════════════════════════════

version:
	@echo "$(GREEN)Current version:$(NC) $(CURRENT_VERSION)"

bump-patch:
	@echo "$(YELLOW)Bumping patch version...$(NC)"
	@$(PYTHON) $(SCRIPTS_DIR)/bump_version.py patch
	@echo "$(GREEN)Version bumped to $$(cat $(VERSION_FILE))$(NC)"

bump-minor:
	@echo "$(YELLOW)Bumping minor version...$(NC)"
	@$(PYTHON) $(SCRIPTS_DIR)/bump_version.py minor
	@echo "$(GREEN)Version bumped to $$(cat $(VERSION_FILE))$(NC)"

bump-major:
	@echo "$(YELLOW)Bumping major version...$(NC)"
	@$(PYTHON) $(SCRIPTS_DIR)/bump_version.py major
	@echo "$(GREEN)Version bumped to $$(cat $(VERSION_FILE))$(NC)"

tag-release:
	@echo "$(YELLOW)Creating git tag for version $(CURRENT_VERSION)...$(NC)"
	@git tag -a "v$(CURRENT_VERSION)" -m "Release version $(CURRENT_VERSION)"
	@echo "$(GREEN)Tag v$(CURRENT_VERSION) created$(NC)"
	@echo "$(BLUE)Push tags with:$(NC) git push origin v$(CURRENT_VERSION)"

validate-version:
	@echo "$(YELLOW)Validating version consistency...$(NC)"
	@$(PYTHON) $(SCRIPTS_DIR)/validate_version.py

# ═══════════════════════════════════════════════════════════════
# Development
# ═══════════════════════════════════════════════════════════════

install:
	@echo "$(YELLOW)Installing Python dependencies...$(NC)"
	@test -d $(VENV) || python3 -m venv $(VENV)
	@$(PIP) install --upgrade pip
	@$(PIP) install -r requirements.txt
	@echo "$(GREEN)Dependencies installed$(NC)"

dev:
	@echo "$(YELLOW)Starting development server...$(NC)"
	@$(PYTHON) -m uvicorn api.main:app --reload --host 0.0.0.0 --port 8000

test:
	@echo "$(YELLOW)Running tests...$(NC)"
	@if [ -d "tests" ]; then \
		$(PYTHON) -m pytest tests/ -v; \
	else \
		echo "$(RED)No tests directory found$(NC)"; \
		echo "$(BLUE)Create tests/ directory to add tests$(NC)"; \
	fi

lint:
	@echo "$(YELLOW)Running linters...$(NC)"
	@if command -v ruff >/dev/null 2>&1; then \
		ruff check $(SCRIPTS_DIR); \
	else \
		echo "$(YELLOW)ruff not installed, skipping$(NC)"; \
	fi
	@if command -v black >/dev/null 2>&1; then \
		black --check $(SCRIPTS_DIR); \
	else \
		echo "$(YELLOW)black not installed, skipping$(NC)"; \
	fi

format:
	@echo "$(YELLOW)Auto-formatting code...$(NC)"
	@if command -v black >/dev/null 2>&1; then \
		black $(SCRIPTS_DIR); \
		echo "$(GREEN)Code formatted$(NC)"; \
	else \
		echo "$(RED)black not installed$(NC)"; \
		echo "$(BLUE)Install with:$(NC) pip install black"; \
	fi

clean:
	@echo "$(YELLOW)Cleaning temporary files...$(NC)"
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@find . -type f -name "*.pyo" -delete 2>/dev/null || true
	@find . -type f -name "*.log" -size +100M -delete 2>/dev/null || true
	@echo "$(GREEN)Cleanup complete$(NC)"

# ═══════════════════════════════════════════════════════════════
# Data Processing
# ═══════════════════════════════════════════════════════════════

ocr-status:
	@echo "$(YELLOW)Checking OCR processing status...$(NC)"
	@$(PYTHON) $(SCRIPTS_DIR)/extraction/check_ocr_status.py

extract-emails:
	@echo "$(YELLOW)Extracting emails from OCR results...$(NC)"
	@if [ -f "$(SCRIPTS_DIR)/extraction/extract_emails.py" ]; then \
		$(PYTHON) $(SCRIPTS_DIR)/extraction/extract_emails.py; \
	else \
		echo "$(RED)Email extraction script not found$(NC)"; \
		echo "$(BLUE)Create $(SCRIPTS_DIR)/extraction/extract_emails.py$(NC)"; \
	fi

classify-docs:
	@echo "$(YELLOW)Running document classification...$(NC)"
	@$(PYTHON) $(SCRIPTS_DIR)/classification/classify_all_documents.py

build-network:
	@echo "$(YELLOW)Rebuilding entity network...$(NC)"
	@$(PYTHON) $(SCRIPTS_DIR)/analysis/rebuild_flight_network.py
	@echo "$(GREEN)Entity network rebuilt$(NC)"

status:
	@echo "$(BLUE)═══════════════════════════════════════════════════════════════$(NC)"
	@echo "$(BLUE)  Epstein Document Archive - Project Status$(NC)"
	@echo "$(BLUE)═══════════════════════════════════════════════════════════════$(NC)"
	@echo ""
	@echo "$(GREEN)Version:$(NC) $(CURRENT_VERSION)"
	@echo ""
	@echo "$(GREEN)OCR Processing:$(NC)"
	@if [ -f "$(OCR_PID_FILE)" ]; then \
		PID=$$(cat $(OCR_PID_FILE)); \
		if ps -p $$PID > /dev/null 2>&1; then \
			echo "  $(YELLOW)Status:$(NC) Running (PID: $$PID)"; \
		else \
			echo "  $(YELLOW)Status:$(NC) Not running"; \
		fi; \
	else \
		echo "  $(YELLOW)Status:$(NC) Not running"; \
	fi
	@if [ -f "$(OCR_LOG)" ]; then \
		echo "  $(YELLOW)Log size:$(NC) $$(du -h $(OCR_LOG) | cut -f1)"; \
	fi
	@echo ""
	@echo "$(GREEN)Data Statistics:$(NC)"
	@echo "  $(YELLOW)Raw PDFs:$(NC) $$(find $(DATA_DIR)/raw -name "*.pdf" 2>/dev/null | wc -l | xargs)"
	@echo "  $(YELLOW)Markdown files:$(NC) $$(find $(DATA_DIR)/md -name "*.md" 2>/dev/null | wc -l | xargs)"
	@if [ -f "$(METADATA_DIR)/semantic_index.json" ]; then \
		echo "  $(YELLOW)Indexed entities:$(NC) $$(grep -o '"entity"' $(METADATA_DIR)/semantic_index.json 2>/dev/null | wc -l | xargs)"; \
	fi
	@echo ""
	@echo "$(GREEN)Database Files:$(NC)"
	@if [ -f "$(DEDUP_DB)" ]; then \
		echo "  $(YELLOW)Deduplication DB:$(NC) $$(du -h $(DEDUP_DB) | cut -f1)"; \
	fi
	@echo ""
	@echo "$(BLUE)═══════════════════════════════════════════════════════════════$(NC)"

# ═══════════════════════════════════════════════════════════════
# Database Operations
# ═══════════════════════════════════════════════════════════════

db-backup:
	@echo "$(YELLOW)Backing up databases...$(NC)"
	@mkdir -p $(DATA_DIR)/backups
	@TIMESTAMP=$$(date +%Y%m%d_%H%M%S); \
	if [ -f "$(DEDUP_DB)" ]; then \
		cp $(DEDUP_DB) $(DATA_DIR)/backups/deduplication_$$TIMESTAMP.db; \
		echo "$(GREEN)Backed up deduplication.db$(NC)"; \
	fi; \
	if [ -d "$(METADATA_DIR)" ]; then \
		tar -czf $(DATA_DIR)/backups/metadata_$$TIMESTAMP.tar.gz -C $(DATA_DIR) metadata; \
		echo "$(GREEN)Backed up metadata/$(NC)"; \
	fi
	@echo "$(GREEN)Backup complete: $(DATA_DIR)/backups/$(NC)"

db-restore:
	@echo "$(YELLOW)Available backups:$(NC)"
	@ls -lh $(DATA_DIR)/backups/ 2>/dev/null || echo "$(RED)No backups found$(NC)"
	@echo ""
	@echo "$(BLUE)To restore, manually copy desired backup files$(NC)"

# ═══════════════════════════════════════════════════════════════
# Git Operations
# ═══════════════════════════════════════════════════════════════

commit:
	@echo "$(YELLOW)Staging changes...$(NC)"
	@git status --short
	@echo ""
	@echo "$(BLUE)Enter commit type (feat/fix/docs/refactor/chore):$(NC) "; \
	read TYPE; \
	echo "$(BLUE)Enter scope (optional, e.g., 'ocr', 'classification'):$(NC) "; \
	read SCOPE; \
	echo "$(BLUE)Enter commit message:$(NC) "; \
	read MSG; \
	if [ -n "$$SCOPE" ]; then \
		COMMIT_MSG="$$TYPE($$SCOPE): $$MSG"; \
	else \
		COMMIT_MSG="$$TYPE: $$MSG"; \
	fi; \
	git add .; \
	git commit -m "$$COMMIT_MSG" -m "🤖 Generated with [Claude Code](https://claude.ai/code)" -m "Co-Authored-By: Claude <noreply@anthropic.com>"; \
	echo "$(GREEN)Committed: $$COMMIT_MSG$(NC)"

push:
	@echo "$(YELLOW)Pushing to remote...$(NC)"
	@BRANCH=$$(git branch --show-current); \
	git push origin $$BRANCH
	@echo "$(GREEN)Pushed to remote$(NC)"

release: bump-minor tag-release
	@echo "$(YELLOW)Preparing release...$(NC)"
	@NEW_VERSION=$$(cat $(VERSION_FILE)); \
	echo "$(GREEN)Release v$$NEW_VERSION prepared$(NC)"; \
	echo "$(BLUE)Review CHANGELOG.md and run 'make push' to publish$(NC)"

# ═══════════════════════════════════════════════════════════════
# Logs & Monitoring
# ═══════════════════════════════════════════════════════════════

logs:
	@echo "$(YELLOW)Tailing OCR logs (Ctrl+C to exit)...$(NC)"
	@tail -f $(OCR_LOG)

logs-downloads:
	@echo "$(YELLOW)Tailing download logs (Ctrl+C to exit)...$(NC)"
	@tail -f $(LOGS_DIR)/downloads/*.log 2>/dev/null || echo "$(RED)No download logs found$(NC)"

# ═══════════════════════════════════════════════════════════════
# Build & Deploy
# ═══════════════════════════════════════════════════════════════

build:
	@echo "$(YELLOW)Building production assets...$(NC)"
	@echo "$(BLUE)No build step defined yet$(NC)"

deploy:
	@echo "$(YELLOW)Deploying to production...$(NC)"
	@echo "$(RED)Deployment not configured$(NC)"
	@echo "$(BLUE)Configure deployment target in Makefile$(NC)"
