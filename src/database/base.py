"""Abstract database interface."""

from abc import ABC, abstractmethod
from typing import List, Optional

from ..models import MOVReport


class DatabaseProvider(ABC):
    """Abstract database provider."""

    @abstractmethod
    def save_report(self, report: MOVReport) -> str:
        """Save report and return ID."""
        pass

    @abstractmethod
    def get_report(self, report_id: str) -> Optional[MOVReport]:
        """Retrieve report by ID."""
        pass

    @abstractmethod
    def list_reports(
        self,
        limit: int = 100,
        offset: int = 0,
        filter_dict: Optional[dict] = None
    ) -> List[MOVReport]:
        """List reports with pagination and filters."""
        pass

    @abstractmethod
    def delete_report(self, report_id: str) -> bool:
        """Delete report."""
        pass

    @abstractmethod
    def search_reports(self, query: str) -> List[MOVReport]:
        """Full-text search."""
        pass
