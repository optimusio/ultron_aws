"""
Ultron Lightweight Agent - System Info Tool

Reports basic host system information (CPU, memory, disk, platform).
Uses psutil for cross-platform metrics.
"""

import logging
import platform
from typing import Any

from .base import BaseTool

logger = logging.getLogger(__name__)

try:
    import psutil

    _PSUTIL_AVAILABLE = True
except ImportError:
    _PSUTIL_AVAILABLE = False
    logger.warning("psutil not installed; system metrics will be limited")


class SystemInfoTool(BaseTool):
    """Report CPU, memory, disk usage, and OS information."""

    name = "system_info"
    description = (
        "Return current system information: CPU usage, memory usage, "
        "disk usage, and OS details."
    )

    def run(self, **kwargs: Any) -> str:  # type: ignore[override]
        """Collect and format system metrics.

        Returns:
            A formatted multi-line string with system statistics.
        """
        lines = []
        lines.append("🖥️  System Information")
        lines.append("=" * 40)

        # OS / platform details
        lines.append(f"OS:         {platform.system()} {platform.release()}")
        lines.append(f"Machine:    {platform.machine()}")
        lines.append(f"Python:     {platform.python_version()}")

        if _PSUTIL_AVAILABLE:
            # CPU
            cpu_pct = psutil.cpu_percent(interval=0.5)
            cpu_count = psutil.cpu_count(logical=True)
            lines.append(f"CPU usage:  {cpu_pct}% ({cpu_count} logical cores)")

            # Memory
            vm = psutil.virtual_memory()
            used_gb = vm.used / (1024 ** 3)
            total_gb = vm.total / (1024 ** 3)
            lines.append(
                f"RAM:        {used_gb:.1f} GB used / {total_gb:.1f} GB total "
                f"({vm.percent}%)"
            )

            # Disk (root partition)
            try:
                disk = psutil.disk_usage("/")
                used_disk = disk.used / (1024 ** 3)
                total_disk = disk.total / (1024 ** 3)
                lines.append(
                    f"Disk (/):   {used_disk:.1f} GB used / {total_disk:.1f} GB "
                    f"total ({disk.percent}%)"
                )
            except Exception:
                pass
        else:
            lines.append("(Install psutil for detailed CPU/memory/disk metrics)")

        return "\n".join(lines)
