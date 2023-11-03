import six


import maya.cmds as cmds
import maya.OpenMayaUI as omui

import shiboken2
import PySide2.QtWidgets as QtWidgets

from .util import warning

def set_show_hide(panel, obj_type, state):
    if not panel:
        warning('You have to ACTIVE a panel')
        return
    if obj_type == 'nurbsCurves':
        cmds.modelEditor(panel, e=1, nurbsCurves=state)
    if obj_type == 'polymeshes':
        cmds.modelEditor(panel, e=1, polymeshes=state)
    if obj_type == 'locators':
        cmds.modelEditor(panel, e=1, locators=state)
    if obj_type == 'camera':
        cmds.modelEditor(panel, e=1, cameras=state)
    if obj_type == 'selectionHiliteDisplay':
        cmds.modelEditor(panel, e=1, selectionHiliteDisplay=state)
    if obj_type == 'wireframeOnShaded':
        cmds.modelEditor(panel, e=1, wireframeOnShaded=state)
    if obj_type == 'imagePlane':
        cmds.modelEditor(panel, e=1, imagePlane=state)
    if obj_type == 'gpuCache':
        cmds.modelEditor(panel, e=1, pluginObjects=('gpuCacheDisplayFilter', state))


def get_maya_ui_long_name(qt_widget):
    return omui.MQtUtil.fullName(six.integer_types[-1](shiboken2.getCppPointer(qt_widget)[0]))


def get_maya_window():
    ptr = omui.MQtUtil.mainWindow()
    if ptr is not None:
        return shiboken2.wrapInstance(six.integer_types[-1](ptr), QtWidgets.QMainWindow)
