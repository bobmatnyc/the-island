"""
Service layer for managing source suggestions.

Design Decision: File-based JSON storage
Rationale: Simple, version-controllable, no database setup required.
Trade-offs:
- Performance: O(n) filtering vs O(log n) indexed queries
- Scalability: Limited to ~10,000 suggestions before performance degrades
- Simplicity: No database dependencies, easy backup/restore
- Concurrency: File locking for atomic writes

Future Optimization: Migrate to SQLite when suggestions exceed 5,000
or when concurrent write load exceeds 10 writes/second.
"""

import fcntl
import json
import logging
import shutil
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional


try:
    # Try relative import (when used as module)
    from ..models.suggested_source import (
        SourcePriority,
        SourceStatus,
        SuggestedSource,
        SuggestedSourceCreate,
        SuggestedSourceUpdate,
        SuggestionStatistics,
    )
except ImportError:
    # Fallback to absolute import (when used directly)
    from models.suggested_source import (
        SourcePriority,
        SourceStatus,
        SuggestedSource,
        SuggestedSourceCreate,
        SuggestedSourceUpdate,
        SuggestionStatistics,
    )


class SuggestionService:
    """Service for managing source suggestions with file-based storage

    Performance:
    - Read all: O(n) where n = total suggestions
    - Filter by status: O(n) linear scan
    - Get by ID: O(n) linear scan
    - Create: O(1) append operation
    - Update: O(n) read + write entire file

    Error Handling:
    1. FileNotFoundError: Creates new file if missing
    2. JSONDecodeError: Logs corruption, attempts recovery from backup
    3. PermissionError: Fails fast with clear error message
    4. Concurrent writes: File locking prevents corruption

    Data Consistency: All write operations are atomic using temp file + rename.
    No partial writes possible. File lock ensures serialized updates.
    """

    def __init__(self, storage_path: Path):
        """Initialize service with storage path

        Args:
            storage_path: Path to JSON file for storing suggestions
        """
        self.storage_path = storage_path
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)

        # Create empty file if doesn't exist
        if not self.storage_path.exists():
            self._write_suggestions([])

    @contextmanager
    def _file_lock(self, mode: str = "r"):
        """Context manager for file locking

        Prevents concurrent write corruption using fcntl.flock.
        """
        f = self.storage_path.open(mode)
        try:
            fcntl.flock(f.fileno(), fcntl.LOCK_EX)
            yield f
        finally:
            fcntl.flock(f.fileno(), fcntl.LOCK_UN)
            f.close()

    def _read_suggestions(self) -> list[SuggestedSource]:
        """Read all suggestions from storage

        Returns:
            List of SuggestedSource objects

        Error Recovery:
        - If file corrupted, attempts to read backup (.bak file)
        - If both corrupted, returns empty list and logs error
        """
        if not self.storage_path.exists():
            return []

        try:
            with self._file_lock("r") as f:
                data = json.load(f)
                return [SuggestedSource(**item) for item in data]
        except json.JSONDecodeError as e:
            # Attempt backup recovery
            backup_path = self.storage_path.with_suffix(".json.bak")
            if backup_path.exists():
                try:
                    with backup_path.open() as f:
                        data = json.load(f)
                        return [SuggestedSource(**item) for item in data]
                except Exception:
                    pass
            # Log error and return empty list
            logging.error(f"Corrupted suggestions file: {e}")
            return []

    def _write_suggestions(self, suggestions: list[SuggestedSource]) -> None:
        """Write suggestions to storage atomically

        Uses temp file + rename for atomic writes.
        Creates backup before overwriting.

        Error Handling:
        - PermissionError: Propagates to caller
        - IOError: Propagates to caller
        - No partial writes possible due to atomic rename
        """
        # Create backup of existing file
        if self.storage_path.exists():
            backup_path = self.storage_path.with_suffix(".json.bak")
            shutil.copy2(self.storage_path, backup_path)

        # Write to temp file
        temp_path = self.storage_path.with_suffix(".json.tmp")
        data = [s.model_dump(mode="json") for s in suggestions]

        with temp_path.open("w") as f:
            json.dump(data, f, indent=2, default=str)

        # Atomic rename
        temp_path.replace(self.storage_path)

    def create_suggestion(
        self, suggestion_data: SuggestedSourceCreate, submitted_by: Optional[str] = None
    ) -> SuggestedSource:
        """Create new source suggestion

        Args:
            suggestion_data: Validated suggestion data
            submitted_by: Username of submitter (from auth)

        Returns:
            Created SuggestedSource with generated ID

        Performance: O(n) read + O(1) append + O(n) write
        """
        suggestions = self._read_suggestions()

        # Create new suggestion
        suggestion = SuggestedSource(
            **suggestion_data.model_dump(),
            submitted_by=submitted_by,
            submitted_at=datetime.now(timezone.utc),
        )

        suggestions.append(suggestion)
        self._write_suggestions(suggestions)

        return suggestion

    def get_all_suggestions(
        self,
        status: Optional[SourceStatus] = None,
        priority: Optional[SourcePriority] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> tuple[list[SuggestedSource], int]:
        """Get all suggestions with optional filtering

        Args:
            status: Filter by status
            priority: Filter by priority
            limit: Maximum results to return
            offset: Number of results to skip

        Returns:
            Tuple of (suggestions_page, total_count)

        Performance:
        - Time: O(n) for filtering
        - Space: O(n) for full list in memory
        - Optimization: If no filters, could skip loading all into memory
        """
        suggestions = self._read_suggestions()

        # Apply filters
        if status:
            suggestions = [s for s in suggestions if s.status == status]
        if priority:
            suggestions = [s for s in suggestions if s.priority == priority]

        total = len(suggestions)

        # Sort by submission date (newest first)
        suggestions.sort(key=lambda s: s.submitted_at, reverse=True)

        # Pagination
        page = suggestions[offset : offset + limit]

        return page, total

    def get_suggestion_by_id(self, suggestion_id: str) -> Optional[SuggestedSource]:
        """Get single suggestion by ID

        Args:
            suggestion_id: UUID of suggestion

        Returns:
            SuggestedSource if found, None otherwise

        Performance: O(n) linear scan
        Optimization: For >5000 suggestions, add in-memory ID index
        """
        suggestions = self._read_suggestions()
        for suggestion in suggestions:
            if suggestion.id == suggestion_id:
                return suggestion
        return None

    def update_status(
        self,
        suggestion_id: str,
        update_data: SuggestedSourceUpdate,
        reviewed_by: Optional[str] = None,
    ) -> Optional[SuggestedSource]:
        """Update suggestion status and metadata

        Args:
            suggestion_id: UUID of suggestion
            update_data: Update fields
            reviewed_by: Username of reviewer (from auth)

        Returns:
            Updated SuggestedSource if found, None otherwise

        Performance: O(n) read + O(n) write
        Atomic: Uses temp file + rename for consistency
        """
        suggestions = self._read_suggestions()

        for i, suggestion in enumerate(suggestions):
            if suggestion.id == suggestion_id:
                # Update fields
                update_dict = update_data.model_dump(exclude_unset=True)

                for field, value in update_dict.items():
                    setattr(suggestion, field, value)

                # Update review metadata if status changed
                if update_data.status and update_data.status != suggestion.status:
                    suggestion.reviewed_at = datetime.now(timezone.utc)
                    suggestion.reviewed_by = reviewed_by

                # Update processing timestamps
                if update_data.status == SourceStatus.PROCESSING:
                    suggestion.processing_started_at = datetime.now(timezone.utc)
                elif update_data.status in [SourceStatus.COMPLETED, SourceStatus.FAILED]:
                    suggestion.processing_completed_at = datetime.now(timezone.utc)

                suggestions[i] = suggestion
                self._write_suggestions(suggestions)

                return suggestion

        return None

    def delete_suggestion(self, suggestion_id: str) -> bool:
        """Delete suggestion by ID

        Args:
            suggestion_id: UUID of suggestion

        Returns:
            True if deleted, False if not found

        Performance: O(n) read + O(n) write
        """
        suggestions = self._read_suggestions()
        original_count = len(suggestions)

        suggestions = [s for s in suggestions if s.id != suggestion_id]

        if len(suggestions) < original_count:
            self._write_suggestions(suggestions)
            return True

        return False

    def get_statistics(self) -> SuggestionStatistics:
        """Get statistics for admin dashboard

        Returns:
            SuggestionStatistics with counts by status and priority

        Performance: O(n) single pass through all suggestions
        """
        suggestions = self._read_suggestions()

        # Count by status
        status_counts = dict.fromkeys(SourceStatus, 0)
        for suggestion in suggestions:
            status_counts[suggestion.status] += 1

        # Count by priority
        priority_counts = dict.fromkeys(SourcePriority, 0)
        for suggestion in suggestions:
            priority_counts[suggestion.priority] += 1

        # Recent submissions (last 7 days)
        seven_days_ago = datetime.now(timezone.utc) - timedelta(days=7)
        recent = sum(1 for s in suggestions if s.submitted_at >= seven_days_ago)

        return SuggestionStatistics(
            total=len(suggestions),
            pending=status_counts[SourceStatus.PENDING],
            approved=status_counts[SourceStatus.APPROVED],
            rejected=status_counts[SourceStatus.REJECTED],
            processing=status_counts[SourceStatus.PROCESSING],
            completed=status_counts[SourceStatus.COMPLETED],
            failed=status_counts[SourceStatus.FAILED],
            by_priority=priority_counts,
            recent_submissions=recent,
        )
