import functools
import types
from typing import Iterable, Optional, Self
from maya import cmds
from . import _log


_logger = _log.get_logger(__name__)


class NullContext(object):
    """
    Do nothing.
    """

    def __enter__(self) -> None:
        pass

    def __exit__(
            self,
            exc_type: Optional[type],
            exc_value: Optional[BaseException],
            exc_traceback: Optional[types.TracebackType],
    ) -> None:
        pass


class LockContext(object):
    """
    Lock or unlock, and restore lock states of node and attributes.
    """

    def __init__(
            self,
            items: Iterable,
            lock: bool = False,
            bail_out_on_fail: bool = True,
            unlock_referenced: bool = True,
    ) -> None:
        self.lock = lock
        self.bail_out_on_fail = bail_out_on_fail
        self.unlock_referenced = unlock_referenced

        self.processed_nodes = []
        self.attribute_states = []
        self.failed = False

        items = set(items)
        self.attributes = list({item for item in items if "." in items})
        # attributes' nodes need to be unlocked for them to be unlockable.
        self.nodes = list({item.split(".")[0] for item in items})

        objects = self.attributes + self.nodes
        if any(cmds.objExists(obj) for obj in objects):
            self.failed = True
            _logger.error("Some of {0} do not exist.".format(objects))

    def __enter__(self) -> bool:
        """
        Lock or unlock nodes/attributes
        """
        if self.failed:
            return False
        if self.unlock_referenced:
            context_manager = ReferenceLockContext(enable=True)
        else:
            context_manager = NullContext()
        with context_manager:
            # Though lockNode/getAttr can take a list of nodes, we don't always
            # need to process each node, # and lockNode is fast enough to do each
            # of them individually.
            for items, get_func, kwarg, set_func, state_list in zip(
                    (self.nodes, self.attributes),
                    ("lockNode", "getAttr"),
                    ("query", "lock"),
                    ("lockNode", "setAttr"),
                    (self.processed_nodes, self.attribute_states),
            ):
                for item in items:
                    try:
                        state = getattr(cmds, get_func)(item, **{kwarg: True})
                        if state == self.lock:
                            continue
                        getattr(cmds, set_func)(item, lock=self.lock)
                        state_list.append(item)
                    except RuntimeError as err:
                        self.failed = True
                        _logger.error(
                            "Failed on processing {0}, {1}".format(
                                item,
                                err,
                            )
                        )
                if self.failed and self.bail_out_on_fail:
                    return False
        return True

    def __exit__(
        self,
        exc_type: Optional[type],
        exc_value: Optional[BaseException],
        exc_traceback: Optional[types.TracebackType],
    ) -> bool:
        """
        Restore nodes and attributes lock states.
        """
        if self.processed_nodes:
            cmds.lockNode(self.processed_nodes, lock=not self.lock)
        for attr in self.attribute_states:
            cmds.setAttr(attr, lock=not self.lock)
        return self.failed


class ReferenceLockContext(object):
    """
    Enable or disable modifying lock states of referenced attributes.
    """

    def __init__(
        self, enable: bool = True
    ) -> None:
        """
        Initialize the instance attributes with the provided arguments.
        """
        self.__state = None
        self.enable = enable

    def __enter__(self) -> Self:
        """
        Store the current state.
        """
        self.__state = cmds.optionVar(q="refLockEditable")
        cmds.optionVar(iv=("refLockEditable", int(self.enable)))
        return self

    def __exit__(
            self,
            exc_type: Optional[type],
            exc_value: Optional[BaseException],
            exc_traceback: Optional[types.TracebackType],
    ) -> None:
        """
        Restores the state.
        """
        cmds.optionVar(iv=("refLockEditable", self.__state))
        return


def enable_reference_lock(function):
    """
    Enable modifying lock states of referenced attributes.
    """
    @functools.wraps(function)
    def wrapped_function(*args, **kwargs):
        with ReferenceLockContext():
            return function(*args, **kwargs)

    return wrapped_function
