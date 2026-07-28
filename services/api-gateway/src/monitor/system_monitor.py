import time

import psutil


class SystemMonitor:
    """
    Collects real-time system health metrics.
    """

    def __init__(self):
        self.boot_time = psutil.boot_time()

    def get_cpu_usage(self) -> float:
        """
        Return CPU usage percentage.
        """
        return psutil.cpu_percent(interval=1)

    def get_memory_usage(self) -> float:
        """
        Return memory usage percentage.
        """
        return psutil.virtual_memory().percent

    def get_disk_usage(self) -> float:
        """
        Return disk usage percentage.
        """
        return psutil.disk_usage("/").percent

    def get_network_usage(self) -> float:
        """
        Return total network traffic (MB).
        """
        network = psutil.net_io_counters()

        total_bytes = network.bytes_sent + network.bytes_recv

        return round(
            total_bytes / (1024 * 1024),
            2,
        )

    def get_uptime(self) -> str:
        """
        Return system uptime.
        """

        uptime_seconds = int(time.time() - self.boot_time)

        days = uptime_seconds // 86400

        hours = (uptime_seconds % 86400) // 3600

        minutes = (uptime_seconds % 3600) // 60

        seconds = uptime_seconds % 60

        return f"{days}d {hours}h {minutes}m {seconds}s"

    def collect(self) -> dict:
        """
        Collect all system metrics.
        """

        return {
            "cpu_usage": self.get_cpu_usage(),
            "memory_usage": self.get_memory_usage(),
            "disk_usage": self.get_disk_usage(),
            "network_usage": self.get_network_usage(),
            "uptime": self.get_uptime(),
        }
