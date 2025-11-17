#!/usr/bin/env python3
"""
File Watcher Service for Hot-Reload
Monitors data files and broadcasts changes via SSE
"""

import asyncio
import logging
import os
import time
from pathlib import Path
from typing import Dict, List, Set

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

logger = logging.getLogger(__name__)


class DataFileWatcher(FileSystemEventHandler):
    """
    Monitors data files for changes and broadcasts events to connected SSE clients

    Features:
    - Debouncing: Groups rapid changes into single event (1 second window)
    - Event mapping: Maps filenames to semantic event types
    - Client management: Maintains list of connected SSE queues
    """

    # Map filenames to event types
    EVENT_MAP = {
        "entity_network.json": "entity_network_updated",
        "timeline_events.json": "timeline_updated",
        "master_document_index.json": "entities_updated",
        "unified_document_index.json": "documents_updated",
        "cases_index.json": "cases_updated",
        "victims_index.json": "victims_updated",
        "entity_name_mappings.json": "entity_mappings_updated",
        "entity_filter_list.json": "entity_filter_updated",
    }

    def __init__(self, enable_hot_reload: bool = True):
        """
        Initialize file watcher

        Args:
            enable_hot_reload: Whether hot-reload is enabled (default: True in dev)
        """
        super().__init__()
        self.clients: List[asyncio.Queue] = []
        self.enabled = enable_hot_reload
        self.debounce_timers: Dict[str, float] = {}
        self.debounce_delay = 1.0  # 1 second debounce
        self.pending_events: Set[str] = set()

        logger.info(f"File watcher initialized (enabled: {self.enabled})")

    def on_modified(self, event):
        """
        Handle file modification events

        Args:
            event: Watchdog file system event
        """
        if not self.enabled or event.is_directory:
            return

        # Only monitor JSON files
        if not event.src_path.endswith('.json'):
            return

        filename = os.path.basename(event.src_path)

        # Check if this file is in our watch list
        if filename not in self.EVENT_MAP:
            return

        # Debounce rapid changes
        current_time = time.time()
        last_event_time = self.debounce_timers.get(filename, 0)

        if current_time - last_event_time < self.debounce_delay:
            # Still within debounce window, mark as pending
            self.pending_events.add(filename)
            logger.debug(f"Debouncing change to {filename}")
            return

        # Update timer and broadcast
        self.debounce_timers[filename] = current_time
        event_type = self.EVENT_MAP[filename]

        logger.info(f"File changed: {filename} → {event_type}")
        self.broadcast(event_type, filename)

    def broadcast(self, event_type: str, filename: str):
        """
        Broadcast event to all connected SSE clients

        Args:
            event_type: Type of event (e.g., "entity_network_updated")
            filename: Name of file that changed
        """
        if not self.clients:
            logger.debug(f"No clients connected, skipping broadcast of {event_type}")
            return

        event_data = {
            "event": event_type,
            "data": {
                "filename": filename,
                "timestamp": time.time(),
            }
        }

        # Send to all connected clients
        disconnected_clients = []
        for queue in self.clients:
            try:
                queue.put_nowait(event_data)
                logger.debug(f"Broadcasted {event_type} to client")
            except asyncio.QueueFull:
                logger.warning(f"Client queue full, marking for disconnect")
                disconnected_clients.append(queue)

        # Clean up disconnected clients
        for queue in disconnected_clients:
            self.clients.remove(queue)

        logger.info(f"Broadcasted {event_type} to {len(self.clients)} clients")

    def add_client(self, queue: asyncio.Queue):
        """
        Add new SSE client

        Args:
            queue: Asyncio queue for sending events to client
        """
        self.clients.append(queue)
        logger.info(f"Client connected (total: {len(self.clients)})")

    def remove_client(self, queue: asyncio.Queue):
        """
        Remove disconnected SSE client

        Args:
            queue: Client queue to remove
        """
        if queue in self.clients:
            self.clients.remove(queue)
            logger.info(f"Client disconnected (remaining: {len(self.clients)})")

    def get_client_count(self) -> int:
        """Get number of connected clients"""
        return len(self.clients)

    def enable(self):
        """Enable hot-reload"""
        self.enabled = True
        logger.info("Hot-reload enabled")

    def disable(self):
        """Disable hot-reload"""
        self.enabled = False
        logger.info("Hot-reload disabled")


class FileWatcherService:
    """
    Service to manage file watching with proper lifecycle
    """

    def __init__(self, watch_dirs: List[Path], enable_hot_reload: bool = True):
        """
        Initialize file watcher service

        Args:
            watch_dirs: List of directories to watch
            enable_hot_reload: Whether to enable hot-reload (default: True)
        """
        self.watch_dirs = watch_dirs
        self.event_handler = DataFileWatcher(enable_hot_reload=enable_hot_reload)
        self.observer = Observer()
        self.started = False

        logger.info(f"File watcher service created for {len(watch_dirs)} directories")

    def start(self):
        """Start watching directories"""
        if self.started:
            logger.warning("File watcher already started")
            return

        for watch_dir in self.watch_dirs:
            if not watch_dir.exists():
                logger.warning(f"Watch directory does not exist: {watch_dir}")
                continue

            self.observer.schedule(
                self.event_handler,
                str(watch_dir),
                recursive=False  # Don't watch subdirectories
            )
            logger.info(f"Watching directory: {watch_dir}")

        self.observer.start()
        self.started = True
        logger.info("File watcher service started")

    def stop(self):
        """Stop watching directories"""
        if not self.started:
            return

        self.observer.stop()
        self.observer.join()
        self.started = False
        logger.info("File watcher service stopped")

    def get_event_handler(self) -> DataFileWatcher:
        """Get the event handler for client management"""
        return self.event_handler
