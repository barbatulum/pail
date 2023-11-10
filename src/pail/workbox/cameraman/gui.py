from six import string_types

import maya.cmds as cmds
import maya.api.OpenMaya as om2

from PySide2 import QtCore, QtGui, QtWidgets

from . import function_sets
from . import constants as consts
from ... import crux
from ...crux import _log
from ...crux import contexts
from ...crux import gui as maya_gui

_logger = _log.get_logger(__name__)
class QSingleton(type(QtCore.QObject), type):
    # https://github.com/davidlatwe/sweet/blob/main/src/sweet/gui/models.py#L22
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(QSingleton, cls).__call__(
                *args, **kwargs
            )
        return cls._instances[cls]


class CameramanGUI(QtWidgets.QMainWindow, metaclass=QSingleton):
    def __init__(self, parent=None):
        if parent is None:
            parent = maya_gui.get_maya_window()
        QtWidgets.QMainWindow.__init__(self, parent)

        self.last_active_panel = ""

        self.central_widget = QtWidgets.QWidget(self)
        self.setCentralWidget(self.central_widget)
        self.central_vertical_layout = QtWidgets.QVBoxLayout(
            self.central_widget
            )

        # top_layout
        self.top_layout = QtWidgets.QVBoxLayout()
        self.central_vertical_layout.addLayout(self.top_layout)

        # mid/btm layouts
        self.mid_layout = QtWidgets.QHBoxLayout()
        self.central_vertical_layout.addLayout(self.mid_layout)

        self.btm_layout = QtWidgets.QHBoxLayout()
        self.central_vertical_layout.addLayout(self.btm_layout)

        # Mid layout -> left/right panel layouts
        self.list_ui_qvl = QtWidgets.QVBoxLayout()
        self.mid_layout.addLayout(self.list_ui_qvl)
        self.right_panel_layout = QtWidgets.QVBoxLayout()
        self.mid_layout.addLayout(self.right_panel_layout)
        self.mid_layout.setStretch(0, 1)
        self.mid_layout.setStretch(1, 2)

        # Mid layout -> left panel -> list UIs
        self.list_ui_commands_qhl = QtWidgets.QHBoxLayout()
        self.refresh_qpb = QtWidgets.QPushButton(
            "Refresh", self.central_widget
            )
        self.qlist_order_pqb = QtWidgets.QPushButton(
            "Camera first", self.central_widget
            )
        self.list_ui_commands_qhl.addWidget(self.refresh_qpb)
        self.list_ui_commands_qhl.addWidget(self.qlist_order_pqb)
        self.list_ui_qvl.addLayout(self.list_ui_commands_qhl)

        self.camera_list = ListWidget(self.central_widget)
        self.camera_list.setObjectName(consts.ObjectName.CameraList)
        self.list_ui_qvl.addWidget(self.camera_list)
        self.image_plane_list = ListWidget(self.central_widget)
        self.image_plane_list.setObjectName(consts.ObjectName.ImagePlaneList)
        self.list_ui_qvl.addWidget(self.image_plane_list)

        # Mid layout -> right panel -> function widget
        self.functions_tabs = QtWidgets.QTabWidget(self.central_widget)
        self.right_panel_layout.addWidget(self.functions_tabs)

        self.main_tab_qw = QtWidgets.QWidget()
        self.functions_tabs.addTab(self.main_tab_qw, "Main")
        self.main_tab_qvl = QtWidgets.QVBoxLayout(self.main_tab_qw)

        self.config_tab_qw = QtWidgets.QWidget()
        self.functions_tabs.addTab(self.config_tab_qw, "Config")
        self.config_tab_qvl = QtWidgets.QVBoxLayout(self.config_tab_qw)

        self.functions_tabs.setTabPosition(QtWidgets.QTabWidget.North)
        self.functions_tabs.setTabShape(QtWidgets.QTabWidget.Rounded)
        self.functions_tabs.setDocumentMode(True)
        self.functions_tabs.setMovable(True)
        self.functions_tabs.setCurrentIndex(0)

        self.status_bar = QtWidgets.QStatusBar(self)
        self.setStatusBar(self.status_bar)

        parents = set()

        parents.update(
            function_sets.populate_viewport_options(
                parent_widget=self.central_widget,
                parent_layout=self.top_layout,
            )
        )
        parents.update(
            function_sets.populate_image_plane_attributes(
                parent_widget=self.main_tab_qw,
                parent_layout=self.main_tab_qvl,
            )
        )
        parents.update(
            function_sets.populate_camera_attributes(
                parent_widget=self.main_tab_qw,
                parent_layout=self.main_tab_qvl,
            )
        )
        parents.update(
            function_sets.populate_image_plane_commands(
                parent_widget=self.main_tab_qw,
                parent_layout=self.main_tab_qvl,
            )
        )
        parents.update(
            function_sets.populate_bake(
                parent_widget=self.main_tab_qw,
                parent_layout=self.main_tab_qvl,
            )
        )
        parents.update(
            function_sets.populate_playblast(
                parent_widget=self.central_widget,
                parent_layout=self.right_panel_layout,
            )
        )
        parents.update(
            function_sets.populate_name_preset(
                parent_widget=self.config_tab_qw,
                parent_layout=self.config_tab_qvl
            )
        )
        parents.update(
            function_sets.populate_gui_options(
                parent_widget=self.config_tab_qw,
                parent_layout=self.config_tab_qvl
            )
        )

        for parent in parents:
            for child in parent.children():
                object_name = child.objectName()
                if object_name:
                    setattr(self, object_name, child)

        self.make_pusher(self.main_tab_qvl)
        self.make_pusher(self.config_tab_qvl)

    @staticmethod
    def make_pusher(layout):
        """
        Make a QSpacerItem to push the widgets to the top
        """
        pusher = QtWidgets.QSpacerItem(
            20,
            40,
            QtWidgets.QSizePolicy.Minimum,
            QtWidgets.QSizePolicy.Expanding,
        )
        layout.addItem(pusher)

    @contexts.block_qt_signals
    def toggle_image_plane_attributes(self, lock=True):
        """
        Toggle the lock state of image plane related widgets. For disabling
        the image plane related widgets when no image plane is selected.
        """
        for attribute in dir(self):
            if not attribute.startswith(consts.ObjectName.ImagePlane.base):
                continue
            if hasattr(attribute, "setEnabled"):
                attribute.setEnabled(lock)

    def warning(
        self, message, lasts=3000, pos="topCenter", formation="<hl>{}</hl>"
    ):
        """
        Show a warning message on the status bar and in the viewport.
        """
        cmds.inViewMessage(
            smg=formation.format(message), fade=True, pos=pos
            )

        self.status_bar.showMessage(message, lasts=lasts)

    def get_widget_attribute_mapping(self, prefix=consts.Main.Camera):
        """
        Return a mapping of the widget and the maya attribute name.
        """
        mapping = {}
        for widget_name in dir(self):
            if not widget_name.startswith(prefix):
                continue
            maya_attribute = consts.AttributeMapping.get(widget_name)
            if maya_attribute is None:
                _logger.warning(
                    "Cannot find maya attribute mapping with %s", widget_name
                )
                continue
            widget = getattr(self, widget_name)
            mapping[widget] = maya_attribute
        return mapping

    # todo: WIP
    def connect_attributes(self, key=consts.Main.Camera):
        """
        Connect the widget signal to set the maya attributes.
        """
        widget_attribute_mapping = self.get_widget_attribute_mapping(key)
        if key == consts.Main.Camera:
            object_cmd = self.getcam
        else:
            object_cmd = self.getimageplane

        for widget, attribute in widget_attribute_mapping.items():
            signal = consts.QtAttributeSignal.get(type(widget))
            if signal is None:
                continue
            # self.imageAlphaGain.valueChanged.connect(self.set_alpha_gain)
            # todo
            signal.connect(
                lambda x: cmds.setAttr(object_cmd() + "." + attribute)
            )
    def get_selection_names(self, scene=True, gui=True):
        """
        Get the selection of GUI lists, and/or the actual camera and
        image plane scene nodes.
        """
        selection = {}
        if gui:
            for list_widget in (self.camera_list, self.image_plane_list):
                selection.setdefault("gui", []).extend(
                    list_widget.list_selected_text().values())
        if scene:
            selection["scene"] = crux.convert_nodes(
                crux.get_selection(), "partialPath"
            )
        return selection

    @contexts.block_qt_signals
    def populate_camera_goodies(self, align_scene_selection=True):
        """
        Populate scene camera and image plane nodes to the list widgets.
        """
        selection = self.get_selection_names(scene=align_scene_selection)
        for node_type, list_widget in zip(
            (om2.MFn.kCamera, om2.MFn.kImagePlane),
            (self.camera_list,self.image_plane_list),
        ):
            # Repopulate items
            list_widget.clear()
            scene_nodes = crux.ls(node_type=node_type)
            for node in scene_nodes:
                list_widget.add(node)

            # Restore selection
            list_items = list_widget.list_items()
            for item in list_items:
                item_text = item.text()
                if align_scene_selection:
                    if item_text in selection.get("scene", []):
                        item.setSelected(True)
                elif item_text in selection["gui"]:
                    item.setSelected(True)

    @contexts.block_qt_signals
    def align_gui_widgets_to_scene_node(
        self,
        mode=consts.Main.Camera,
        camera=None,
        image_plane=None,
    ):
        """
        Align the GUI widget values to the scene nodes that are selected in
        the GUI. If no cam/ip nodes are given, use the selected ones in the
        GUI instead.
        """
        if camera is None:
            cameras = self.camera_list.selectedItems()
            if cameras:
                camera = cameras[-1]
        if image_plane is None:
            image_planes = self.image_plane_list.selectedItems()[-1]
            if image_planes:
                image_plane = image_planes[-1]

        if not camera and not image_plane:
            return

        self.blockSignals(True)
        for prefix, scene_node in zip(
            (consts.Main.Camera, consts.Main.ImagePlane),
            (camera, image_plane)
        ):
            widget_attribute_mapping = self.get_widget_attribute_mapping(prefix)
            for widget, attribute in widget_attribute_mapping.items():
                cmd_name = consts.QtSetCommands.get(type(widget))
                if not cmd_name:
                    msg = "Cannot find set command name for {0}".format(
                        type(widget)
                    )
                    _logger.warning(msg)
                    self.warning(msg)
                    continue
                cmd = getattr(widget, cmd_name)
                if not cmd:
                    msg = (
                        "Cannot find set command '{0}' for widget '{1}'"
                    ).format(cmd_name, widget)
                    _logger.warning(msg)
                    self.warning(msg)
                    continue
                attr = "{0}.{1}".format(scene_node, attribute)
                # todo: better error handling.
                try:
                    value = cmds.getAttr(attr)
                    cmd(value)
                except RuntimeError as e:
                    msg = "Failed to set {0}: {1}".format(attr, e)
                    _logger.warning(msg)
                    self.warning(msg)



    # def align_camera_attributes(self):
    # def align_gui_states(self):


class ListWidget(QtWidgets.QListWidget):
    """
    ListWidget for camera related items with some custom methods.
    """
    def __init__(self, parent):
        super(ListWidget, self).__init__(parent)
        self.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)

    def add(self, node):
        """ Shortcut to add QtWidgets"""
        handle = crux.convert_node(node, om2.MObjectHandle)
        partial_path = crux.convert_node(node, "partialPath")
        self.addItem(partial_path)
        last = self.item(self.count() - 1)
        last.handle = handle
        return last

    def list_items(self):
        return [self.item(cnt) for cnt in range(self.count())]

    def list_selected_text(self):
        selected_widget = self.selectedItems()
        texts = {}
        for widget in selected_widget:
            if hasattr(widget, "handle"):
                if widget.handle.isValid():
                    texts[widget] = crux.convert_node(
                        widget.handle, "partialPath"
                        )
            else:
                texts[widget] = widget.text()
        return texts

def get_connected_camera_goodies(mobject):
    source_transform = None
    if mobject.hasFn(om2.MFn.kTransform):
        source_transform = mobject
        shapes = crux.get_shapes(mobject)
    else:
        shapes = [mobject]

    if shapes[0].hasFn(om2.MFn.kCamera):
        source_type = om2.MFn.kCamera
        if not shapes:
            return False
        camera_shape = source_shape = shapes[0]
        camera = source_transform
    elif shapes[0].hasFn(om2.MFn.kImagePlane):
        source_type = om2.MFn.kImagePlane
        source_shape = shapes[0]
        connections = crux.list_connections(
            source_shape, "message", source=False, destination=True
        )
        if connections:
            camera, camera_shape = [
                (crux.get_parent(plug.node()), plug.node())
                for src, dst_plugs in connections.values()[0]
                for plug in dst_plugs
            ][0]
        else:
            camera, camera_shape = None, None

    else:
        raise RuntimeError(
            "{0} is not a camera goody".format(
                crux.convert_node(mobject, "partialPath")
            )
        )

    if source_transform is None:
        source_transform = crux.get_parent(shapes[0])

    image_planes = []
    if camera_shape is not None:
        connections = crux.list_connections(
            camera_shape, "imagePlane", source=True, destination=False
        )
        image_planes = [
            (crux.get_parent(dst), dst)
            for src_plug, dst_plugs in connections.values()
            for dst in dst_plugs
        ]

    return_value = (
        (source_type, source_transform, source_shape),
        (camera, camera_shape),
        image_planes,
    )
    return return_value


def get_camera_goodies_on_selection():
    sel_list = om2.MGlobal.getActiveSelectionList()
    if not sel_list.length():
        return False

    last = sel_list.getDependNode(sel_list.length() - 1)
    shape = None
    if last.hasFn(om2.MFn.kTransform):
        dag_path = om2.MDagPath.getAPathTo(last)
        child_count = dag_path.numberOfShapesDirectlyBelow()
        if not child_count:
            return False
        shape = dag_path.extendToShape(0)

    if shape is None:
        shape = last
    if shape.hasFn(om2.MFn.kCamera):
        widget_name = consts.ObjectName.CameraList
    elif shape.hasFn(om2.MFn.kImagePlane):
        widget_name = consts.ObjectName.ImagePlaneList
    else:
        return False
    transform = shape.transform()
    update_ui(transform, shape, widget_name=widget_name)


def update_ui(transform, shape, widget_name=consts.ObjectName.CameraList):
    """ update the UI by selection changed callback """
    # index = {'camera': 0, 'image_plane': 1}[mode]
    gui = CameramanGUI()
    camera, camera_shape, image_plane, image_plane_shape = (None,) * 4
    if widget_name == consts.ObjectName.CameraList:
        camera = transform
        camera_shape = shape
    else:
        image_plane = transform
        image_plane_shape = shape

    list_widget = getattr(gui, widget_name)
    list_widget.setFocus()

    get_connected_cmd = {
        consts.ObjectName.CameraList: get_connected_cam,
        consts.ObjectName.ImagePlaneList: get_connected_imagePlane,
    }[widget_name]


    fp = main.mobj2(node, 'fullPath')
    if fp in full_path:
        updating_listWidget.set_selected(
            updating_listWidget.item(full_path.index(fp))
            )
    else:
        connected = get_connected_cmd(node)
        if connected:
            connected = connected[0]
        connected_fp = main.mobj2(connected, 'fullPath')
        all_fp = listWidget[1 - index].list_items()[3]
        if not connected_fp in all_fp:
            return
        idx = all_fp.index(connected_fp)
        listWidget[1 - index].set_selected(listWidget[1 - index].item(idx))
        idx = updating_listWidget.list_items()[3].index(fp)
        updating_listWidget.set_selected(updating_listWidget.item(idx))

