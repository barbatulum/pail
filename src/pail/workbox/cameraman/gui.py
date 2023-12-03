from six import string_types
# todo: save qtsettings as decorator

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
        self.top_layout.setSpacing(3)
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
        # todo: only show refresh_qpb button when the mode is set to not manual update
        self.refresh_qpb = QtWidgets.QPushButton(
            "Refresh", self.central_widget
            )
        self.list_ui_qvl.addWidget(self.refresh_qpb)

        self.camera_list = ListWidget(self.central_widget)
        self.camera_list.setObjectName(consts.ObjectName.CameraList)
        self.list_ui_qvl.addWidget(self.camera_list)

        fixed_size = QtWidgets.QSizePolicy(
            QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed
        )
        # self.toggle_list_order_qpb = QtWidgets.QPushButton(
        #     "⭮", self.central_widget
        # )
        self.link_list_display_qpb = QtWidgets.QPushButton(
            "🡻", self.central_widget
        )

        self.link_list_selection_qpb = QtWidgets.QPushButton(
            "🔗", self.central_widget
        )

        self.camera_goodies_target_qpb = QtWidgets.QPushButton(
            "📺", self.central_widget
        )

        self.link_list_selection_qpb.setCheckable(True)
        self.link_list_selection_qpb.setChecked(True)
        # ⭮⬇⬆ 🡑 🡓 🡙 ⇧ ⇩ ⇳  ⤒ ⤓ ↨⟰ ⟱ ⇡ ⇣ ⮸ 🠉 🠋🠝 🠟 🡩 🡫🡹 🡻⮝ ⮟🡅 🡇
        # ▲  △╳X✖🗙🞮🞭🞬🞫🗙✘❌⏹⧅⧣⍂⍯⎕⏹⬜
        self.list_option_qhl = QtWidgets.QHBoxLayout()
        for btn in (
            self.link_list_selection_qpb,
            # self.toggle_list_order_qpb,
            self.link_list_display_qpb,
            self.camera_goodies_target_qpb,
        ):
            self.list_option_qhl.addWidget(btn)

        self.list_ui_qvl.addLayout(self.list_option_qhl)
        self.list_option_qhl.setContentsMargins(50, 0, 50, 0)

        self.image_plane_list = ListWidget(self.central_widget)
        self.image_plane_list.setObjectName(consts.ObjectName.ImagePlaneList)
        self.list_ui_qvl.addWidget(self.image_plane_list)

        # Mid layout -> right panel -> function widget
        # todo: assign hotkey to switch between tabs
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
            function_sets.populate_basic_tools(
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

        for list_widget in self.camera_list, self.image_plane_list:
            list_widget.itemSelectionChanged.connect(
                self.on_lists_selection_change
            )

            list_widget.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
            list_widget.customContextMenuRequested.connect(
                self.pop_up_list_menu
            )
            list_widget.doubleClicked.connect(
                self.select_node
            )
        # self.toggle_list_order_qpb.clicked.connect(self.switch_list)
        self.link_list_display_qpb.clicked.connect(self.switch_display_update_mode)
        self.camera_goodies_target_qpb.clicked.connect(self.switch_camera_goodies_target)

        self.populate_camera_goodies()
        getattr(
            self, consts.ObjectName.NamePresets.name_presets_field
        ).setText("masterCam slave_cam ortho_{camera}")

    def populate_camera_goodies(self):
        self.populate_primary_list()
        self.populate_secondary_list()
    def select_node(self, sender=None):
        """ Select object when double click on UI listWidgets """
        if sender is None:
            sender = self.sender()
        selected = sender.selectedItems()
        if selected:
            nodes = crux.convert_nodes([sl.transform_handle for sl in selected], "partialPath")
            cmds.select(nodes, replace=True)

    def get_cam_preset_names(self, camera):
        name_presets = getattr(
            self, consts.ObjectName.NamePresets.name_presets_field
        ).text().split()
        name_presets = [n.format(camera=camera) for n in name_presets if n]
        return name_presets

    # def rename(self):
    # def create_image_plane(self, viewport=True):
    #     kwargs = {}
    #     if camera is not None:
    #         kwargs["camera"] = camera
    #     return cmds.imagePlane(**kwargs)

    def pop_up_list_menu(self):
        sender = self.sender()
        cam_mode = sender == self.camera_list

        menu = QtWidgets.QMenu(self)
        if cam_mode:
            menu.addAction("Look Through")

        if cam_mode:
            menu.addAction("New Camera", cmds.camera)
        else:
            menu.addAction("New Image Plane", cmds.camera)
            sub_menu = menu.addMenu("Image Plane ...")
            sub_menu.addAction("New by GUI Selection")
            sub_menu.addAction("New Standalone")

        menu.addSeparator()
        menu.addAction(
            "Select",
            lambda: self.select_node(sender=sender)
        )

        if not cam_mode:
            menu.addAction("Select corresponding camera")

        menu.addAction("Delete")
        menu.addAction("Clear", self.populate_camera_goodies)

        selected_items = sender.selectedItems()
        if cam_mode and selected_items:
            menu.addSeparator()
            # todo: support multiple selection(camera names)
            cam_name = "<...>"
            if len(selected_items) == 1:
                cam_name = selected_items[0].text()
            for name in self.get_cam_preset_names(cam_name):
                menu.addAction("Rename to " + name)

        menu.exec_(QtGui.QCursor(QtCore.Qt.PointingHandCursor).pos())

    def is_selection_linked(self):
        return self.link_list_selection_qpb.isChecked()

    def display_updating_mode(self):
        return {
            "⬜": 0, "🡻": 1, "🡹🡻": 2
        }[self.link_list_display_qpb.text()]

    def camera_goodies_target(self):
        return {
            "📺": 0, "◯": 1, "∞∞": 2
        }[self.camera_goodies_target_qpb.text()]

    def switch_camera_goodies_target(self):
        self.camera_goodies_target_qpb.setText(
            {
                "📺": "◯", "◯": "∞∞", "∞∞": "📺"
            }[self.camera_goodies_target_qpb.text()]
        )
    def switch_display_update_mode(self):
        self.link_list_display_qpb.setText(
            {
                "🡻": "🡹🡻", "🡹🡻": "⬜", "⬜":"🡻"
            }[self.link_list_display_qpb.text()]
        )
        mode = self.display_updating_mode()
        self.link_list_selection_qpb.setStyleSheet("")
        if mode == 0:
            self.populate_primary_list()
            self.populate_secondary_list()
            self.link_list_selection_qpb.setChecked(False)
        elif mode == 2:
            self.link_list_selection_qpb.setChecked(True)
            self.link_list_selection_qpb.setStyleSheet(
                "QPushButton { background-color: black}"
            )
        else:
            self.link_list_selection_qpb.setChecked(True)

        self.link_list_selection_qpb.setEnabled(mode == 1)

        return mode

    def is_selection_reverse_updating(self):
        return self.link_list_display_qpb.text() == "🡹🡻"


    def switch_selection_update_mode(self):
        self.link_list_display_qpb.setText(
            {"🡻": "🡹🡻", "🡹🡻": "🡻"}[self.link_list_display_qpb.text()]
        )
        return self.reverse_update()


    def get_primary_list_idx(self):
        """
        Return what the top list is by OpenMaya constants.
        """
        cam_idx = self.list_ui_qvl.indexOf(self.camera_list)
        ip_idx = self.list_ui_qvl.indexOf(self.image_plane_list)
        idx = om2.MFn.kCamera if cam_idx < ip_idx else om2.MFn.kImagePlane
        return idx

    @contexts.block_qt_signals
    def switch_list(self):
        orig_selection = self.get_current_selections()
        primary_list_idx = self.get_primary_list_idx()
        widgets = [
            self.camera_list,
            self.image_plane_list,
        ]
        self.list_ui_qvl.removeItem(self.list_option_qhl)
        if primary_list_idx == om2.MFn.kCamera:
            widgets.reverse()
        for widget in widgets:

            self.list_ui_qvl.addWidget(widget)
        self.list_ui_qvl.insertLayout(2, self.list_option_qhl)

        self.populate_primary_list()
        self.populate_secondary_list()
        _, main_node_type, ordered_lists = self.get_active_info()
        for list_widget in ordered_lists:
            for item in list_widget.list_items():
                for name, handles in orig_selection[main_node_type].items():
                    if not handles[0].isValid() or not handles[1].isValid():
                        continue
                    if handles[0] == item.transform_handle:
                        item.setSelected(True)

        if orig_selection[main_node_type]:
            for item in ordered_lists[0].list_items():
                if item.text() in orig_selection[main_node_type]:
                    item.setSelected(True)
                    break


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
        self,
        message,
        lasts=3000,
        in_view_message=True,
        pos="topCenter",
        formation="<hl>{}</hl>"
    ):
        """
        Show a warning message on the status bar and in the viewport.
        """
        if in_view_message:
            cmds.inViewMessage(
                smg=formation.format(message), fade=True, pos=pos
                )

        self.status_bar.showMessage(message, lasts=lasts)

    def get_widget_attribute_mapping(self, prefix=om2.MFn.kCamera):
        """
        Return a mapping of the widget and the maya attribute name.
        """
        mapping = {}
        for widget_name in dir(self):
            if not widget_name.startswith(str(prefix)):
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
    def connect_attributes(self, key=om2.MFn.kCamera):
        """
        Connect the widget signal to set the maya attributes.
        """
        widget_attribute_mapping = self.get_widget_attribute_mapping(key)
        if key == om2.MFn.kCamera:
            object_cmd = self.get_cam
        else:
            object_cmd = self.get_imageplane

        for widget, attribute in widget_attribute_mapping.items():
            signal = consts.QtAttributeSignal.get(type(widget))
            if signal is None:
                continue
            # self.imageAlphaGain.valueChanged.connect(self.set_alpha_gain)
            # todo
            signal.connect(
                lambda x: cmds.setAttr(object_cmd() + "." + attribute)
            )
    def get_current_selections(self):
        """
        Get the selection of GUI lists, and/or the actual camera and
        image plane scene nodes.
        """
        selection = {}
        for kind, list_widget in zip(
            (om2.MFn.kCamera, om2.MFn.kImagePlane),
            (self.camera_list, self.image_plane_list),
        ):
            selection[kind] = {
                item.text(): (item.transform_handle, item.shape_handle)
                for item in list_widget.selectedItems()
            }
        return selection

    # def get_list_selection(self, selection=None):
    #     """
    #     Get the selection of GUI lists, and/or the actual camera and
    #     image plane scene nodes.
    #     """
    #     gui_selection = list_widget.list_selected_text()
    #     for list_widget in (self.camera_list, self.image_plane_list):
    #         selection.setdefault("gui", []).extend(
    #             list_widget.list_selected_text().values()
    #         )
    #     return selection
    def get_active_info(self):
        main_node_type = self.get_primary_list_idx()
        cam_first = main_node_type == om2.MFn.kCamera
        ordered_lists = (self.camera_list, self.image_plane_list)
        if not cam_first:
            ordered_lists = list(reversed(ordered_lists))

        return cam_first, main_node_type, ordered_lists
    def print_selected(self, txt):
        print("\n"+txt)
        print("\t",[item.text() for item in self.camera_list.selectedItems()])
        print("\t",)

    def refresh_and_restore(self):
        selected_cams = [
            item.text() for item in self.camera_list.selectedItems()
        ]
        selected_ips = [
            item.text() for item in self.image_plane_list.selectedItems()
        ]
        self.populate_camera_goodies()
        for list_widget, selected in zip(
            (self.camera_list, self.image_plane_list),
            (selected_cams, selected_ips),
        ):
            for item in list_widget.list_items():
                if item.text() in selected:
                    item.setSelected(True)


    def on_lists_selection_change(self):
        # todo: When item(s) selected, highlight corresponding cam or ip
        sender = self.sender()
        sender_selected = sender.selectedItems()
        selected_handles = [item.transform_handle for item in sender_selected]
        cam_first, main_node_type, ordered_lists = self.get_active_info()
        reverse_updating = self.display_updating_mode()
        selection_linked = self.is_selection_linked()
        if reverse_updating == 2:
            context_manager = contexts.NullContext
        else:
            context_manager = contexts.QtSignalContext
        if sender == ordered_lists[0] and reverse_updating:
            with contexts.QtSignalContext([ordered_lists[1]], block=True):
                self.populate_secondary_list()
        elif selection_linked:
            primary_list_items = ordered_lists[0].list_items()
            selecting = []
            for item in sender_selected:
                camera_goodies = get_connected_camera_goodies(
                    item.transform_handle
                )
                _, (camera, camera_shape), image_planes, = camera_goodies
                if cam_first and camera is not None:
                    with context_manager([ordered_lists[0]], block=True):
                        for cam_item in primary_list_items:
                            if cam_item.transform_handle.object() == camera:
                                selecting.append(cam_item)

            with context_manager(ordered_lists, block=True):
                for cam_item in primary_list_items:
                    select = cam_item in selecting
                    cam_item.setSelected(select)

            # with contexts.QtSignalContext(ordered_lists, block=True):
                if reverse_updating:
                    for item in ordered_lists[1].list_items():
                        for handle in selected_handles:
                            if item.transform_handle == handle:
                                item.setSelected(True)
                                break


    def populate_secondary_list(self):
        cam_first, main_node_type, ordered_lists = self.get_active_info()
        ordered_lists[1].clear()
        selected_items = ordered_lists[0].selectedItems()
        all_items = ordered_lists[0].list_items()
        active_items = (
            ordered_lists[0].selectedItems()
            or
            ordered_lists[0].list_items()
        )
        transforms = []
        if selected_items:
            for item in selected_items:
                # todo: if not item.transform_handle.isValid(), repopulate and reselect matching name.
                if not item.transform_handle.isValid():
                    self.refresh_and_restore()
                    break
                _, (camera, camera_shape), image_planes = get_connected_camera_goodies(
                    item.transform_handle
                )
                # standalone image planes return None for camera
                if camera is None:
                    continue
                if main_node_type == om2.MFn.kImagePlane:
                    transforms.append(camera)
                else:
                    transforms.extend([tsf for tsf, _ in image_planes])
        else:
            if main_node_type == om2.MFn.kCamera:
                node_type = om2.MFn.kImagePlane
            else:
                node_type = om2.MFn.kCamera
            transforms.extend(
                [shape for shape in crux.ls(node_type)]
            )
        # todo: if selected cam only has one image plane, select it
        # todo: populate non-attached image planes
        new_items = ordered_lists[1].add(transforms)
        single_select = len(selected_items) == 1
        if single_select and len(new_items) == 1:
            new_items[0].setSelected(True)


    def refresh_and_restore_scene_select(self, restore_scene_selection=True):
        added_items = self.populate_primary_list()
        names = [
            [
                crux.convert_node(
                    getattr(item, attr), "partialPath"
                )
                for item in added_items
            ]
            for attr in ("transform_handle", "shape_handle")
        ]
        cam_first, main_node_type, ordered_lists = self.get_active_info()
        if restore_scene_selection:
            scene_selection = crux.convert_nodes(
                crux.get_selection(), "partialPath"
            )
            # todo: if selected is IP, update ip and cam GUI selection accordingly
            for node_name in reversed(scene_selection):
                for names_ in names:
                    try:
                        ids = names_.index(node_name)
                        break
                    except ValueError:
                        continue
                else:
                    return
                current_item = added_items[ids]
                if current_item.text() == node_name:
                    current_item.setSelected(True)

            for item in ordered_lists[-1].list_items():
                if item.text() in scene_selection:
                    item.setSelected(True)

    @contexts.block_qt_signals
    def populate_primary_list(self):
        """
        Populate scene camera and image plane nodes to the list widgets.
        """
        # with contexts.QtSignalContext((self.camera_list, self.image_plane_list)):
        for list_widget in (self.camera_list, self.image_plane_list):
            list_widget.clear()
        _, main_node_type, ordered_lists = self.get_active_info()
        add_items = ordered_lists[0].add(
            sorted(
                crux.ls(node_type=main_node_type, return_type="partialPath")
            )
        )
        return add_items

    @contexts.block_qt_signals
    def align_gui_widgets_to_scene_node(
        self,
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
            (om2.MFn.kCamera, om2.MFn.kImagePlane),
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


class ListWidget(QtWidgets.QListWidget):
    """
    ListWidget for camera related items with some custom methods.
    """
    def __init__(self, parent):
        super(ListWidget, self).__init__(parent)
        self.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
    #
    # def clear(self):
    #     with contexts.QtSignalContext([self]):
    #         super().clear()

    def add(self, nodes):
        """ Shortcut to add QtWidgets"""
        items = []
        for node in nodes:
            mobj = crux.convert_node(node, om2.MObject)
            camera_goodies = get_connected_camera_goodies(mobj)
            (node_type, transform, shape), _, _ = camera_goodies
            partial_path = crux.convert_node(transform, "partialPath")
            if node_type == om2.MFn.kImagePlane:
                partial_path = partial_path.split("->")[-1]
            self.addItem(partial_path)
            item = self.item(self.count() - 1)
            item.node_type = node_type
            item.transform_handle, item.shape_handle = (
                crux.convert_node(mobj, om2.MObjectHandle)
                for mobj in (transform, shape)
            )
            items.append(item)

        return items

    def list_items(self):
        return [self.item(cnt) for cnt in range(self.count())]

    # def list_selected_text(self):
    #     selected_widget = self.selectedItems()
    #     texts = {}
    #     for widget in selected_widget:
    #         if hasattr(widget, "handle"):
    #             if widget.transform_handle.isValid():
    #                 texts[widget] = crux.convert_node(
    #                     widget.transform_handle, "partialPath"
    #                 )
    #         else:
    #             texts[widget] = widget.text()
    #     return texts

def list_scene_camera_goodies():
    camera_mobjects = crux.ls(
        node_type=om2.MFn.kCamera, return_type=om2.MObject
    )
    scene_camera_goodies = {
        crux.convert_node(
            cam, "partialPath"
        ): get_connected_camera_goodies(cam)
        for cam in camera_mobjects
    }

    image_planes = {
        crux.convert_node(tsf, "partialPath"): (
            (om2.MFn.kImagePlane, tsf, shape),
            cam_info,
            image_planes,
        )
        for _, cam_info, image_planes in scene_camera_goodies.values()
        for tsf, shape in image_planes
    }
    scene_camera_goodies.update(image_planes)
    return scene_camera_goodies

def get_connected_camera_goodies(node):
    mobject = crux.convert_node(node, om2.MObject)
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
                for plug in list(connections.values())[0][1]
            ][0]
        else:
            camera, camera_shape = None, None

    else:
        msg = "{0} is not a camera goody".format(
            crux.convert_node(mobject, "partialPath")
        )
        raise RuntimeError(msg)

    if source_transform is None:
        source_transform = crux.get_parent(shapes[0])

    image_planes = []
    if camera_shape is not None:
        connections = crux.list_connections(
            camera_shape, "imagePlane", source=True, destination=False
        )
        image_planes = [
            (crux.get_parent(dst.node()), dst.node())
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
    # update_ui(transform, shape, widget_name=widget_name)


#
#
# def update_ui(transform, shape, widget_name=consts.ObjectName.CameraList):
#     """ update the UI by selection changed callback """
#     # index = {'camera': 0, 'image_plane': 1}[mode]
#     gui = CameramanGUI()
#     camera, camera_shape, image_plane, image_plane_shape = (None,) * 4
#     if widget_name == consts.ObjectName.CameraList:
#         camera = transform
#         camera_shape = shape
#     else:
#         image_plane = transform
#         image_plane_shape = shape
#
#     list_widget = getattr(gui, widget_name)
#     list_widget.setFocus()
#
#     get_connected_cmd = {
#         consts.ObjectName.CameraList: get_connected_cam,
#         consts.ObjectName.ImagePlaneList: get_connected_imagePlane,
#     }[widget_name]
#
#
#     fp = main.mobj2(node, 'fullPath')
#     if fp in full_path:
#         updating_listWidget.set_selected(
#             updating_listWidget.item(full_path.index(fp))
#             )
#     else:
#         connected = get_connected_cmd(node)
#         if connected:
#             connected = connected[0]
#         connected_fp = main.mobj2(connected, 'fullPath')
#         all_fp = listWidget[1 - index].list_items()[3]
#         if not connected_fp in all_fp:
#             return
#         idx = all_fp.index(connected_fp)
#         listWidget[1 - index].set_selected(listWidget[1 - index].item(idx))
#         idx = updating_listWidget.list_items()[3].index(fp)
#         updating_listWidget.set_selected(updating_listWidget.item(idx))
#
