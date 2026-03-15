"""OA Dashboard Server — coming in a future release.

This will be a pure Python HTTP server that serves:
- API endpoints (JSON) reading from SQLite
- Pre-built React dashboard (static files)

For now, use `oa status` for a terminal view.
"""
from __future__ import annotations


def serve(port: int = 3456, db_path: str = "data/monitor.db") -> None:
    """Start the OA dashboard server. (Placeholder)"""
    print(f"Dashboard server coming soon. Would serve on port {port}.")
    print(f"For now, use: oa status")
