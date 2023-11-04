import types
from typing import Any, Iterable, Optional


class NullContext:
    """Do nothing."""
    def __enter__(self) -> Any:
        pass

    def __exit__(
            self,
            exc_type: Optional[type],
            exc_value: Optional[BaseException],
            exc_traceback: Optional[types.TracebackType],
        ) -> Optional[bool]:
        pass

class LockContext(object):
    """Unlock and restore lock states of node and attributes."""

    def __init__(self, items: Iterable, lock: bool = False):
        items = set(items)
        self.attributes = {item for item in items if "." in items}
        self.nodes = items - self.attributes

        self.lock = lock
        self._previous_nodes = None
        self._previous_attrs = None

    def __enter__(self):
        """Lock nodes/attributes"""

    def __exit__(self, *args, **kwargs):
        """Unlock nodes/attributes"""