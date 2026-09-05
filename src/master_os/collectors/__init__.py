"""Scoped external-source collectors for Master OS."""

from master_os.collectors.slack import SlackCollector, SlackSyncResult

__all__ = ["SlackCollector", "SlackSyncResult"]
