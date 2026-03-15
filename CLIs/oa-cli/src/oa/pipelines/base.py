"""Pipeline framework — base class and Metric dataclass."""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from oa.core.config import ProjectConfig


@dataclass
class Metric:
    """A single metric value produced by a pipeline."""
    name: str
    value: float
    unit: str = ""
    breakdown: dict[str, Any] | None = None


class Pipeline(ABC):
    """Base class for data collection pipelines.

    Subclass this and implement `collect()` to create a custom pipeline.

    Example::

        from oa import Pipeline, Metric

        class MyPipeline(Pipeline):
            goal_id = "my_goal"

            def collect(self, date: str, config: ProjectConfig) -> list[Metric]:
                return [Metric("my_metric", 42, unit="count")]
    """

    goal_id: str = ""  # Override in subclass

    @abstractmethod
    def collect(self, date: str, config: "ProjectConfig") -> list[Metric]:
        """Collect metrics for a given date.

        Args:
            date: Date string in YYYY-MM-DD format.
            config: Project configuration with agent list, paths, etc.

        Returns:
            List of Metric values to store.
        """
        ...
