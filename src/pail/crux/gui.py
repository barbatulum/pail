import six


import maya.cmds as cmds
import maya.OpenMayaUI as omui

import shiboken2
import PySide2.QtWidgets as QtWidgets

from . import _log
from . import constants as consts
from .constants import PanelType
from .constants import GraphEditorRetrievingParameters as GeParams


_logger = _log.get_logger(__name__)


def set_show_option(panel, option, state):
    if not panel:
        _logger.warning("You have to ACTIVE a panel")
        return
    cmds.modelEditor(panel, edit=True, **{option: state})


def get_maya_ui_long_name(qt_widget):
    return omui.MQtUtil.fullName(six.integer_types[-1](shiboken2.getCppPointer(qt_widget)[0]))


def get_maya_window():
    ptr = omui.MQtUtil.mainWindow()
    if ptr is not None:
        return shiboken2.wrapInstance(six.integer_types[-1](ptr), QtWidgets.QMainWindow)


def get_panel_camera(modes=("withFocus", "underPointer")):
    """
    Get the camera from the "model" panel "withFocus" or "underPointer"
    """
    panel = None
    camera = None
    for mode in modes:
        panel = cmds.getPanel(**{mode: True})
        panel_type = cmds.getPanel(typeOf=panel)
        camera = None
        if panel_type == PanelType.model_panel:
            camera = cmds.modelEditor(panel, query=True, camera=True)
            break
    return panel, camera


def get_maya_editor_name(panel, panel_type):
    """
    Return the "editor" name of the given panel.
    """
    editor = ""
    if panel:
        editor += consts.EditorNameMapping.get(panel_type, "")

    return editor


def get_panel_info(panel):
    """
    Get the panel info of the given panel
    """
    if not panel:
        return panel, None, None
    panel_type = cmds.getPanel(typeOf=panel)
    editor = ""
    if panel_type in (PanelType.outliner_panel, PanelType.model_panel):
        editor = get_maya_editor_name(panel, panel_type)
    elif panel_type == PanelType.scripted_panel:
        panel_type = getattr(cmds, panel_type)(panel, query=True, type=True)
        editor = get_maya_editor_name(panel, panel_type)

    return panel, panel_type, editor


def get_panel(modes=("withFocus", "underPointer")):
    """
    Get the panel info of the panel "withFocus" or "underPointer".
    """
    panel = ""
    for mode in modes:
        panel = cmds.getPanel(**{mode: True})
        if panel:
            break
    return get_panel_info(panel)


def get_type_of_visible_panels(panel_type):
    """
    Get all visible panels by the given type.
    """
    visible_panels = cmds.getPanel(visiblePanels=1)
    panels = []
    for panel in visible_panels:
        panel_info = get_panel_info(panel)
        if panel_info[1] == panel_type:
            panels.append(panel_info)
    return panels


def get_graph_editor_outliner(panel):
    """
    Get the outliner name of the given graph editor
    """
    return panel + "OutlineEd"


# todo: review this function
def get_a_graph_editor(
    valid_mode=GeParams.valid_mode,
    working_order=GeParams.working_order,
    reverse_visible_order=GeParams.reverse_visible_order
):
    """
    Get a graph editor with fallback order.
    :param valid_mode:
        How to determine whether to active key-graph_editor elements
            visible: any ge counts,  as long as it's visible
            focus: only a ge with focus counts
            pointer: only a ge under pointer counts
            wf_up: must with focus and under pointer
    :param working_order:
        Works on which graph_editor, by the order
            visible
            focus
            pointer
    :param reverse_visible_order:
        How to get the visible graph editor when there are multiples,
        sort by name or reverse_sort by name
    :return:
    """
    has_valid_ge = False
    the_graph_editor = None
    candidates = {}

    visible_ge = [get_panel_info(i) for i in cmds.getPanel(visiblePanels=True)]
    visible_ge = [i for i in visible_ge if i[1] == PanelType.graph_editor]

    if visible_ge:
        candidates = {
            "visible": visible_ge[-1] if reverse_visible_order else visible_ge[
                0],
            "focus": get_panel_info(cmds.getPanel(withFocus=True)),
            "pointer": get_panel_info(cmds.getPanel(underPointer=True)),
        }
        if valid_mode == "visible":
            has_valid_ge = True

        elif valid_mode == "wf_up":
            if (
                candidates["focus"][1] ==
                candidates["pointer"][1] ==
                PanelType.graph_editor
            ) and (
                candidates["focus"][0] ==
                candidates["pointer"][0]
            ):
                has_valid_ge = True
                # If you focus and put mouse upon the graph editor,
                # it must be the one to work on
                the_graph_editor = candidates["focus"]
        # pointer and focus
        elif (candidates.get(valid_mode) and
              candidates.get(valid_mode)[1] == PanelType.graph_editor):
            has_valid_ge = True

    if has_valid_ge and not the_graph_editor:
        for valid_ge_type in working_order:
            panel_info = candidates.get(valid_ge_type)
            if panel_info and panel_info[1] and panel_info[
                1] == PanelType.graph_editor:
                the_graph_editor = panel_info
    return the_graph_editor


def set_ui_element_vis(element='ChannelBoxLayerEditor', visible=True):
    """
    Sow or hide ChannelBoxLayerEditor, AttributeEditor, or ToolSettings.
    A python version of setUIComponentVisibility.
    """
    currently_visible = cmds.workspaceControl(
        element, query=True, visible=True
    )

    if not currently_visible and not visible:
        return

    if currently_visible and not visible:
        kwargs = {"visible": False}
    else:
        kwargs = {"restore": True}

    cmds.workspaceControl(element, edit=True, **kwargs)
