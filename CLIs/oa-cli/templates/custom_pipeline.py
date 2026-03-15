"""
Example custom pipeline for OA.

This shows how to create your own goal metric. Copy this file to your
project's pipelines/ directory, edit the logic, and register it in config.yaml.

Usage:
    1. Copy to pipelines/content_quality.py
    2. Edit the collect() method with your logic
    3. Add to config.yaml:
       - id: content_quality
         name: Content Quality
         builtin: false
         pipeline: pipelines/content_quality.py
         metrics:
           - name: approval_rate
             unit: "%"
             healthy: 90
             warning: 70
    4. Run: oa collect
"""
from oa import Pipeline, Metric


class ContentQuality(Pipeline):
    """Example: track content approval rates."""

    goal_id = "content_quality"

    def collect(self, date: str, config) -> list[Metric]:
        """Collect metrics for a given date.

        Replace this with your actual logic — read files, APIs, databases,
        whatever produces your metric values.

        Args:
            date: Date string like "2026-03-15"
            config: ProjectConfig with agent list, paths, etc.

        Returns:
            List of Metric objects to store in the database.
        """
        # Example: count approved vs total posts
        # Replace with your real data source
        approved = 8
        total = 10
        rate = approved / total * 100 if total > 0 else 0

        return [
            Metric(
                name="approval_rate",
                value=rate,
                unit="%",
                breakdown={
                    "approved": approved,
                    "total": total,
                    "date": date,
                },
            ),
        ]
