from functools import partial
import maya.api.OpenMaya as om2
from maya import cmds
import shiboken2
import maya.OpenMayaUI
import six
from PySide2 import QtCore, QtGui, QtWidgets
from ...crux import constants as crux_consts
from ...shortcuts import select as sc_select
from . import constants as consts
from .constants import ObjectName

class Alignment(object):
    right_align = (
        QtCore.Qt.AlignRight | QtCore.Qt.AlignTrailing | QtCore.Qt.AlignVCenter
    )
class SizePolicy(object):
    fixed_size = QtWidgets.QSizePolicy(
        QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed
    )
    horizontal_expanding = QtWidgets.QSizePolicy(
        QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed
    )

def populate_viewport_options(parent_widget, parent_layout):
    viewport_options_layout = QtWidgets.QHBoxLayout()
    parent_layout.addLayout(viewport_options_layout)

    preset_editor = QtWidgets.QPushButton("+", parent_widget)
    preset_editor.setObjectName(ObjectName.ShowOptions + "preset_editor")
    preset_editor.setSizePolicy(SizePolicy.fixed_size)
    preset_editor.setMinimumSize(QtCore.QSize(25, 0))
    preset_editor.setMaximumSize(QtCore.QSize(25, 16777215))
    viewport_options_layout.addWidget(preset_editor)

    items = [preset_editor]
    for label, option in consts.SHOW_OPTIONS_MAPPING.items():
        button = QtWidgets.QPushButton(label, parent_widget)
        button.setObjectName(ObjectName.ShowOptions + option)
        button.setCheckable(True)
        viewport_options_layout.addWidget(button)

        items.append(button)
    return [parent_widget]

def populate_basic_tools(parent_widget, parent_layout):
    basic_tools_layout = QtWidgets.QHBoxLayout()
    parent_layout.addLayout(basic_tools_layout)

    reorder_selection = QtWidgets.QPushButton("⇶", parent_widget)
    reorder_selection.setObjectName(ObjectName.BasicTools.reorder_selection)
    basic_tools_layout.addWidget(reorder_selection)
    full_path = maya.OpenMayaUI.MQtUtil.fullName(
        six.integer_types[-1](shiboken2.getCppPointer(reorder_selection)[0])
        )
    cmds.popupMenu(button=1, allowOptionBoxes=1, mm=1,parent=full_path)
    cmds.menuItem(label="Select Root Nodes", radialPosition='N', command=lambda *args: sc_select.select_roots())
    cmds.menuItem(label="Select Hierarchy", radialPosition='S', command=lambda *args: sc_select.select_hierarchy())
    cmds.menuItem(label="Select First", radialPosition='W', command=lambda *args: sc_select.select_first())
    cmds.menuItem(label="Select Last", radialPosition='E', command=lambda *args: sc_select.select_last())
    cmds.menuItem(label="Reverse Selection", command=lambda *args: sc_select.reverse_selection())

    # filter_selection = QtWidgets.QPushButton("∰🏯🏰🛃🐾🎰🧩🌐🕃🔩🧲🔣💦🧾🧿➿⛎", parent_widget)
    filter_selection = QtWidgets.QPushButton("💦", parent_widget)
    filter_selection.setObjectName(ObjectName.BasicTools.filter_selection)
    basic_tools_layout.addWidget(filter_selection)
    full_path = maya.OpenMayaUI.MQtUtil.fullName(
        six.integer_types[-1](shiboken2.getCppPointer(filter_selection)[0])
        )
    cmds.popupMenu(button=1, allowOptionBoxes=1, mm=1,parent=full_path)
    cmds.menuItem(
        label="Select Cameras",
        radialPosition='W',
        command=lambda *args: sc_select.select_filtered_selection(
            node_types=(om2.MFn.kCamera,)
        )
    )
    cmds.menuItem(
        label="Select Image Planes",
        radialPosition='E',
        command=lambda *args: sc_select.select_filtered_selection(
            node_types=(om2.MFn.kImagePlane,)
        )
    )
    cmds.menuItem(
        label="Filter Presets",
        radialPosition='N',
        command=lambda *args: sc_select.select_filtered_selection(
            node_types=()
        )
    )
    cmds.menuItem(
        label="Camera Goodies",
        radialPosition='S',
        command=lambda *args: sc_select.select_filtered_selection(
            node_types=(om2.MFn.kImagePlane, om2.MFn.kCamera)
        )
    )
    cmds.menuItem(
        label="Select Meshes",
        command=lambda *args: sc_select.select_filtered_selection(
            node_types=(om2.MFn.kMesh,)
        )
    )
    cmds.menuItem(
        label="Select Nurbs Curves",
        command=lambda *args: sc_select.select_filtered_selection(
            node_types=(om2.MFn.kNurbsCurve,)
        )
    )
    cmds.menuItem(
        label="Select Locators",
        command=lambda *args: sc_select.select_filtered_selection(
            node_types=(om2.MFn.kLocator,)
        )
    )
    cmds.menuItem(
        label="Select Locators & Curves",
        command=lambda *args: sc_select.select_filtered_selection(
            node_types=(om2.MFn.kLocator, om2.MFn.kNurbsCurve)
        )
    )
    cmds.menuItem(
        label="Select Joints",
        command=lambda *args: sc_select.select_filtered_selection(
            node_types=(om2.MFn.kJoint,)
        )
    )

    return [parent_widget]


def populate_camera_attributes(parent_widget, parent_layout):
    group_box = QtWidgets.QGroupBox("Camera Attributes", parent_widget)
    group_box.setObjectName(ObjectName.Camera.group_box)
    parent_layout.addWidget(group_box)
    grid_layout = QtWidgets.QGridLayout(group_box)

    label = QtWidgets.QLabel("Rotate Order", group_box)
    label.setAlignment(Alignment.right_align)
    grid_layout.addWidget(label, 0, 0, 1, 1)
    rotate_order = QtWidgets.QComboBox(group_box)
    rotate_order.setObjectName(ObjectName.Camera.rotate_order)
    rotate_order.setSizePolicy(SizePolicy.horizontal_expanding)
    rotate_order.addItems(crux_consts.RotateOrderStr)
    grid_layout.addWidget(rotate_order, 0, 1, 1, 1)

    # clip distance
    label = QtWidgets.QLabel("Clip Distance", group_box)
    label.setAlignment(Alignment.right_align)
    grid_layout.addWidget(label, 1, 0, 1, 1)

    clip_distance_layout = QtWidgets.QHBoxLayout()
    grid_layout.addLayout(clip_distance_layout, 1, 1, 1, 1)

    near_clip_plane = QtWidgets.QDoubleSpinBox(group_box)
    near_clip_plane.setDecimals(3)
    near_clip_plane.setMinimum(0.001)
    near_clip_plane.setMaximum(100000.)
    near_clip_plane.setSingleStep(0.1)
    near_clip_plane.setObjectName(ObjectName.Camera.near_clip_plane)
    clip_distance_layout.addWidget(near_clip_plane)

    far_clip_plane = QtWidgets.QDoubleSpinBox(group_box)
    far_clip_plane.setDecimals(0)
    far_clip_plane.setMinimum(0.)
    far_clip_plane.setMaximum(10000000.)
    far_clip_plane.setValue(10000.)
    far_clip_plane.setObjectName(ObjectName.Camera.far_clip_plane)
    clip_distance_layout.addWidget(far_clip_plane)


    return [parent_widget, group_box]


def populate_image_plane_attributes(parent_widget, parent_layout):
    group_box = QtWidgets.QGroupBox("Image Plane Attributes", parent_widget)
    group_box.setObjectName(consts.ObjectName.ImagePlane.attributes_group_box)
    parent_layout.addWidget(group_box)
    grid_layout = QtWidgets.QGridLayout(group_box)

    # color space
    label = QtWidgets.QLabel("Color Space", group_box)
    label.setAlignment(Alignment.right_align)
    grid_layout.addWidget(label, 0, 0, 1, 1)

    color_space = QtWidgets.QComboBox(group_box)
    color_space.setObjectName(ObjectName.ImagePlane.color_space)
    color_space.addItems(consts.ValidColorSpaces)
    grid_layout.addWidget(color_space, 0, 1, 1, 1)

    # display mode
    label_display_mode = QtWidgets.QLabel("Display Mode", group_box)
    label_display_mode.setAlignment(Alignment.right_align)
    grid_layout.addWidget(label_display_mode, 1, 0, 1, 1)

    display_mode = QtWidgets.QComboBox(group_box)
    display_mode.setObjectName(ObjectName.ImagePlane.display_mode)
    display_mode.addItems(consts.AttrEnumMapping.DisplayMode.keys())
    grid_layout.addWidget(display_mode, 1, 1, 1, 1)

    # image path
    label_image_path = QtWidgets.QLabel("Image Path", group_box)
    label_image_path.setAlignment(Alignment.right_align)
    grid_layout.addWidget(label_image_path, 2, 0, 1, 1)

    image_path_layout = QtWidgets.QHBoxLayout()
    grid_layout.addLayout(image_path_layout, 2, 1, 1, 1)

    image_path = QtWidgets.QLineEdit(group_box)
    image_path.setObjectName(ObjectName.ImagePlane.image_path)
    image_path_layout.addWidget(image_path)

    browse_image_path = QtWidgets.QPushButton("...", group_box)
    browse_image_path.setObjectName(ObjectName.ImagePlane.browse_image_path)
    browse_image_path.setSizePolicy(SizePolicy.fixed_size)
    browse_image_path.setMinimumSize(QtCore.QSize(20, 0))
    browse_image_path.setMaximumSize(QtCore.QSize(20, 16777215))
    image_path_layout.addWidget(browse_image_path)

    image_path_layout.setStretch(0, 1)

    # placement
    label_placement = QtWidgets.QLabel("Placement", group_box)
    label_placement.setAlignment(Alignment.right_align)
    grid_layout.addWidget(label_placement, 3, 0, 1, 1)

    placement_layout = QtWidgets.QHBoxLayout()
    grid_layout.addLayout(placement_layout, 3, 1, 1, 1)

    placement_depth = QtWidgets.QDoubleSpinBox(group_box)
    placement_depth.setObjectName(ObjectName.ImagePlane.placement_depth)
    placement_layout.addWidget(placement_depth)

    fit_mode = QtWidgets.QComboBox(group_box)
    fit_mode.setObjectName(ObjectName.ImagePlane.fit_mode)
    fit_mode.addItems(consts.AttrEnumMapping.FitMode.keys())
    placement_layout.addWidget(fit_mode)


    # alpha gain
    label_alpha_gain = QtWidgets.QLabel("Alpha Gain", group_box)
    label_alpha_gain.setAlignment(Alignment.right_align)
    grid_layout.addWidget(label_alpha_gain, 4, 0, 1, 1)

    alpha_gain_slider = QtWidgets.QSlider(group_box)
    alpha_gain_slider.setOrientation(QtCore.Qt.Horizontal)
    alpha_gain_slider.setObjectName(ObjectName.ImagePlane.alpha_gain)
    grid_layout.addWidget(alpha_gain_slider, 4, 1, 1, 1)


    return [parent_widget, group_box]


def populate_image_plane_commands(parent_widget, parent_layout):
    group_box = QtWidgets.QGroupBox("Image Plane Commands", parent_widget)
    group_box.setObjectName(consts.ObjectName.ImagePlane.cmds_group_box)
    parent_layout.addWidget(group_box)
    grid_layout = QtWidgets.QGridLayout(group_box)

    lock_shape = QtWidgets.QPushButton("Lock Shape", group_box)
    lock_shape.setObjectName(ObjectName.ImagePlane.lock_shape)
    grid_layout.addWidget(lock_shape, 0, 1, 1, 1)

    set_look_through = QtWidgets.QPushButton("Set Look Through", group_box)
    set_look_through.setObjectName(ObjectName.ImagePlane.set_look_through)
    grid_layout.addWidget(set_look_through, 0, 0, 1, 1)

    reload_image = QtWidgets.QPushButton("Reload Image Sequence", group_box)
    reload_image.setObjectName(ObjectName.ImagePlane.reload_image)
    grid_layout.addWidget(reload_image, 1, 0, 1, 1)

    unlock_shape = QtWidgets.QPushButton("Unlock Shape", group_box)
    unlock_shape.setObjectName(ObjectName.ImagePlane.unlock_shape)
    grid_layout.addWidget(unlock_shape, 1, 1, 1, 1)

    return [parent_widget, group_box]


def populate_bake(parent_widget, parent_layout):
    group_box = QtWidgets.QGroupBox("Bake to Space", parent_widget)
    group_box.setObjectName(ObjectName.TransformBake.group_box)
    parent_layout.addWidget(group_box)
    main_layout = QtWidgets.QVBoxLayout(group_box)

    sub_row_layout = QtWidgets.QHBoxLayout()
    main_layout.addLayout(sub_row_layout)

    bake_reset_scale = QtWidgets.QCheckBox("Reset Scale", group_box)
    bake_reset_scale.setObjectName(ObjectName.TransformBake.reset_scale)
    sub_row_layout.addWidget(bake_reset_scale)

    rotate_order = QtWidgets.QComboBox(group_box)
    rotate_order.setObjectName(ObjectName.TransformBake.rotate_order)
    rotate_order.addItems(crux_consts.RotateOrderStr)
    sub_row_layout.addWidget(rotate_order)

    do_bake = QtWidgets.QPushButton("Bake", group_box)
    do_bake.setObjectName(ObjectName.TransformBake.do_bake)
    main_layout.addWidget(do_bake)

    return [parent_widget, group_box]


def populate_notes(parent_widget, parent_layout):
    group_box = QtWidgets.QGroupBox("Notes", parent_widget)
    group_box.setObjectName(ObjectName.Notes.group_box)
    parent_layout.addWidget(group_box)
    layout = QtWidgets.QVBoxLayout(group_box)

    notes_content = QtWidgets.QPlainTextEdit(group_box)
    notes_content.setObjectName(ObjectName.Notes.notes_content)
    layout.addWidget(notes_content)

    return [parent_widget, group_box]


def populate_playblast(parent_widget, parent_layout):
    group_box = QtWidgets.QGroupBox("Playblast", parent_widget)
    group_box.setObjectName(ObjectName.Playblast.group_box)
    parent_layout.addWidget(group_box)

    grid_layout = QtWidgets.QGridLayout(group_box)
    grid_layout.setContentsMargins(0, 0, 0, 0)
    do_playblast = QtWidgets.QPushButton("Playblast", group_box)
    do_playblast.setObjectName(ObjectName.Playblast.do_playblast)
    do_playblast.setSizePolicy(SizePolicy.horizontal_expanding)
    do_playblast.setMinimumSize(QtCore.QSize(0, 30))
    # do_playblast.setMaximumSize(QtCore.QSize(30, 30))
    grid_layout.addWidget(do_playblast, 0, 0, 1, 1)

    options = QtWidgets.QPushButton("...", group_box)
    options.setObjectName(ObjectName.Playblast.options)
    options.setMinimumSize(QtCore.QSize(30, 30))
    options.setMaximumSize(QtCore.QSize(30, 30))
    grid_layout.addWidget(options, 0, 1, 1, 1)

    return [parent_widget, group_box]


def populate_name_preset(parent_widget, parent_layout):
    group_box = QtWidgets.QGroupBox("Name Presets", parent_widget)
    # todo: add validator to check if the name is valid
    group_box.setObjectName(ObjectName.NamePresets.group_box)
    parent_layout.addWidget(group_box)
    grid_layout = QtWidgets.QGridLayout(group_box)

    # Camera names
    label = QtWidgets.QLabel("Camera Names", group_box)
    label.setAlignment(Alignment.right_align)
    grid_layout.addWidget(label, 0, 0, 1, 1)
    preset_camera_names = QtWidgets.QLineEdit(group_box)
    preset_camera_names.setObjectName(ObjectName.NamePresets.name_presets_field)
    grid_layout.addWidget(preset_camera_names, 0, 1, 1, 1)

    return [parent_widget, group_box]


def populate_gui_options(parent_widget, parent_layout):
    group_box = QtWidgets.QGroupBox("GUI Options", parent_widget)
    group_box.setObjectName(ObjectName.NamePresets.group_box)
    parent_layout.addWidget(group_box)
    grid_layout = QtWidgets.QGridLayout(group_box)

    label = QtWidgets.QLabel("Disable standalone image planes", group_box)
    label.setAlignment(Alignment.right_align)
    grid_layout.addWidget(label, 0, 0, 1, 1)
    disable_standalone_ip = QtWidgets.QCheckBox(group_box)
    disable_standalone_ip.setObjectName(ObjectName.GUIOptions.disable_standalone_ip)
    grid_layout.addWidget(disable_standalone_ip, 0, 1, 1, 1)

    label = QtWidgets.QLabel("Interactive Lists", group_box)
    label.setAlignment(Alignment.right_align)
    grid_layout.addWidget(label, 1, 0, 1, 1)
    interactive_lists = QtWidgets.QCheckBox(group_box)
    interactive_lists.setObjectName(ObjectName.GUIOptions.interactive_lists)
    grid_layout.addWidget(interactive_lists, 1, 1, 1, 1)

    # Camera names
    label = QtWidgets.QLabel("Update Primary", group_box)
    label.setAlignment(Alignment.right_align)
    grid_layout.addWidget(label, 2, 0, 1, 1)
    update_primary_list_by_secondary = QtWidgets.QCheckBox(group_box)
    update_primary_list_by_secondary.setObjectName(ObjectName.GUIOptions.update_primary_list_by_secondary)
    grid_layout.addWidget(update_primary_list_by_secondary, 2, 1, 1, 1)

    label = QtWidgets.QLabel("Align GUI to scene selection", group_box)
    label.setAlignment(Alignment.right_align)
    grid_layout.addWidget(label, 3, 0, 1, 1)
    align_gui_to_scene = QtWidgets.QCheckBox(group_box)
    align_gui_to_scene.setObjectName(ObjectName.GUIOptions.align_gui_to_scene)
    grid_layout.addWidget(align_gui_to_scene, 3, 1, 1, 1)

    label = QtWidgets.QLabel("Font Size", group_box)
    label.setAlignment(Alignment.right_align)
    grid_layout.addWidget(label, 4, 0, 1, 1)
    slider = QtWidgets.QSlider(group_box)
    slider.setOrientation(QtCore.Qt.Horizontal)
    slider.setObjectName(ObjectName.GUIOptions.font_size)
    grid_layout.addWidget(slider, 4, 1, 1, 1)

    label = QtWidgets.QLabel("Update Mode", group_box)
    label.setAlignment(Alignment.right_align)
    grid_layout.addWidget(label, 5, 0, 1, 1)
    combo_box = QtWidgets.QComboBox(group_box)
    combo_box.setObjectName(ObjectName.GUIOptions.update_mode)
    combo_box.setSizePolicy(SizePolicy.horizontal_expanding)
    combo_box.addItems(("Immediate", "On Entering", "Manual"))
    grid_layout.addWidget(combo_box, 5, 1, 1, 1)

    return [parent_widget, group_box]
