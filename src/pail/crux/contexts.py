import functools
import types
from typing import Iterable, Optional
from typing_extensions import Self

from maya import cmds
import maya.api.OpenMaya as om2

from . import _log
from . import constants as consts

_logger = _log.get_logger(__name__)


class NullContext(object):
    """
    Do nothing.
    """

    def __enter__(self):
        pass

    def __exit__(
        self,
        exc_type: Optional[type],
        exc_value: Optional[BaseException],
        exc_traceback: Optional[types.TracebackType],
    ):
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
    ):
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
            _logger.error("Some of %s do not exist.", objects)

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
            # need to process each node, # and lockNode is fast enough to do
            # each
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
                            "Failed on processing %s, %s",
                            item,
                            err,
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
    ):
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
    ):
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


class RedrawContext(object):
    """
    Enable or disable redraw state, and restore it on exiting.
    """

    def __init__(self, enter_state: bool = False, exit_state: bool = True):
        """
        Initialize the instance attributes with the provided arguments.
        """
        self.enter_state = not enter_state
        self.exit_state = not exit_state

    def __enter__(self):
        """
        Set the enter state.
        """
        cmds.refresh(suspend=self.enter_state)
        return self

    def __exit__(
        self,
        exc_type: Optional[type],
        exc_value: Optional[BaseException],
        exc_traceback: Optional[types.TracebackType],
    ):
        """
        Set the exit state.
        """
        cmds.refresh(suspend=self.exit_state)


class NamespaceContext(object):
    """
    Enter the given namespace.
    """

    def __init__(self, namespace=":"):
        self.namespace = namespace
        self.init_namespace = None

    def __enter__(self) -> Self:
        self.init_namespace = cmds.namespaceInfo(currentNamespace=True)

        cmds.namespace(set=":")
        if self.namespace and self.namespace != ":":
            namespace_exists = cmds.namespace(ex=self.namespace)
            name_occupied = cmds.objExists(self.namespace)

            if name_occupied and not namespace_exists:
                raise ValueError(
                    "Name '{0}' is occupied but not a namespace.".format(
                        self.namespace
                    )
                )

            if not namespace_exists:
                cmds.namespace(addNamespace=self.namespace)
                cmds.namespace(set=self.namespace)

        return self

    def __exit__(
        self,
        exc_type: Optional[type],
        exc_value: Optional[BaseException],
        exc_traceback: Optional[types.TracebackType],
    ):
        try:
            cmds.namespace(set=self.init_namespace)
        except RuntimeError as err:
            if str(err).startswith(consts.Om2Error.NO_MATCHING_NAMESPACE):
                cmds.namespace(set=":")
                _logger.critical(
                    "Initial namespace '%s' is gone.",
                    self.init_namespace,
                )
            raise


class SelectContext(object):
    """
    Clear selection, select given nodes, and restore selection on exiting.
    """

    def __init__(self, nodes=None):
        """
        Initialize the instance attributes with the provided arguments.
        """
        self.selected = []
        self.selecting_nodes = nodes if nodes else None

    def __enter__(self):
        """
        Store selection, and then select given nodes or clear selection.
        """
        self.selected = om2.MGlobal.getActiveSelectionList()

        if self.selecting_nodes is not None:
            cmds.select(self.selecting_nodes, replace=True)
        else:
            cmds.select(cl=True)

        return self

    def __exit__(
        self,
        exc_type: Optional[type],
        exc_value: Optional[BaseException],
        exc_traceback: Optional[types.TracebackType],
    ):
        """Restore selection."""
        om2.MGlobal.setActiveSelectionList(self.selected)
