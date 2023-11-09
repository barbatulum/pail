from PySide2 import QtCore, QtGui, QtWidgets


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
    label_option_mapping = {
        "Wireframe + Shaded": "",
        "Image Plane": "",
        "GPU Cache": "",
        "SL Highlight": "",
        "Nurbs": "",
        "Polygon": "",
        "Camera": "",
        "Locator": "",
    }
    viewport_options_layout = QtWidgets.QHBoxLayout()
    parent_layout.addLayout(viewport_options_layout)

    preset_editor_qpb = QtWidgets.QPushButton("+", parent_widget)
    preset_editor_qpb.setSizePolicy(SizePolicy.fixed_size)
    preset_editor_qpb.setMinimumSize(QtCore.QSize(25, 0))
    preset_editor_qpb.setMaximumSize(QtCore.QSize(25, 16777215))
    viewport_options_layout.addWidget(preset_editor_qpb)

    buttons = []
    for label, option in label_option_mapping.items():
        buttons.append(QtWidgets.QPushButton(label, parent_widget))
        buttons[-1].setCheckable(True)
        viewport_options_layout.addWidget(buttons[-1])



    return viewport_options_layout, [preset_editor_qpb] + buttons

def populate_image_plane_attributes(parent_widget, parent_layout):
    group_box = QtWidgets.QGroupBox("Image Plane Attributes", parent_widget)
    parent_layout.addWidget(group_box)
    grid_layout = QtWidgets.QGridLayout(group_box)

    # color space
    label_color_space = QtWidgets.QLabel("Color Space", group_box)
    label_color_space.setAlignment(Alignment.right_align)
    grid_layout.addWidget(label_color_space, 0, 0, 1, 1)

    color_space_qcb = QtWidgets.QComboBox(group_box)
    grid_layout.addWidget(color_space_qcb, 0, 1, 1, 1)

    # display mode
    label_display_mode = QtWidgets.QLabel("Display Mode", group_box)
    label_display_mode.setAlignment(Alignment.right_align)
    grid_layout.addWidget(label_display_mode, 1, 0, 1, 1)

    display_mode_qcb = QtWidgets.QComboBox(group_box)
    grid_layout.addWidget(display_mode_qcb, 1, 1, 1, 1)

    # image path
    label_image_path = QtWidgets.QLabel("Image Path", group_box)
    label_image_path.setAlignment(Alignment.right_align)
    grid_layout.addWidget(label_image_path, 2, 0, 1, 1)

    image_path_qhl = QtWidgets.QHBoxLayout()
    grid_layout.addLayout(image_path_qhl, 2, 1, 1, 1)

    image_path_qline = QtWidgets.QLineEdit(group_box)
    image_path_qhl.addWidget(image_path_qline)

    browse_image_path_qpb = QtWidgets.QPushButton("...", group_box)
    browse_image_path_qpb.setSizePolicy(SizePolicy.fixed_size)
    browse_image_path_qpb.setMinimumSize(QtCore.QSize(20, 0))
    browse_image_path_qpb.setMaximumSize(QtCore.QSize(20, 16777215))
    image_path_qhl.addWidget(browse_image_path_qpb)

    image_path_qhl.setStretch(0, 1)

    # placement
    label_placement = QtWidgets.QLabel("Placement", group_box)
    label_placement.setAlignment(Alignment.right_align)
    grid_layout.addWidget(label_placement, 3, 0, 1, 1)

    placement_qhl = QtWidgets.QHBoxLayout()
    grid_layout.addLayout(placement_qhl, 3, 1, 1, 1)

    placement_depth_qdsb = QtWidgets.QDoubleSpinBox(group_box)
    placement_qhl.addWidget(placement_depth_qdsb)

    fit_mode = QtWidgets.QComboBox(group_box)
    fit_mode.addItems(["Fill", "Best", "Horizontal", "Vertical", "To Size"])
    placement_qhl.addWidget(fit_mode)


    # alpha gain
    label_alpha_gain = QtWidgets.QLabel("Alpha Gain", group_box)
    label_alpha_gain.setAlignment(Alignment.right_align)
    grid_layout.addWidget(label_alpha_gain, 4, 0, 1, 1)

    alpha_gain_slider = QtWidgets.QSlider(group_box)
    alpha_gain_slider.setOrientation(QtCore.Qt.Horizontal)
    grid_layout.addWidget(alpha_gain_slider, 4, 1, 1, 1)

    # clip distance
    label_clip_distance = QtWidgets.QLabel("Clip Distance", group_box)
    label_clip_distance.setAlignment(Alignment.right_align)
    grid_layout.addWidget(label_clip_distance, 5, 0, 1, 1)

    clip_distance_qhl = QtWidgets.QHBoxLayout()
    grid_layout.addLayout(clip_distance_qhl, 5, 1, 1, 1)

    near_clip_distance_qdsb = QtWidgets.QDoubleSpinBox(group_box)
    near_clip_distance_qdsb.setDecimals(3)
    near_clip_distance_qdsb.setMinimum(0.001)
    near_clip_distance_qdsb.setMaximum(100000.)
    near_clip_distance_qdsb.setSingleStep(0.1)
    clip_distance_qhl.addWidget(near_clip_distance_qdsb)

    far_clip_distance_qdsb = QtWidgets.QDoubleSpinBox(group_box)
    far_clip_distance_qdsb.setDecimals(0)
    far_clip_distance_qdsb.setMinimum(0.)
    far_clip_distance_qdsb.setMaximum(10000000.)
    far_clip_distance_qdsb.setValue(10000.)
    clip_distance_qhl.addWidget(far_clip_distance_qdsb)


def populate_image_plane_commands(parent_widget, parent_layout):
    group_box = QtWidgets.QGroupBox("Image Plane Commands", parent_widget)
    parent_layout.addWidget(group_box)
    grid_layout = QtWidgets.QGridLayout(group_box)

    lock_shape_qpb = QtWidgets.QPushButton("Lock Shape", group_box)
    grid_layout.addWidget(lock_shape_qpb, 0, 1, 1, 1)

    set_look_thru_qpb = QtWidgets.QPushButton("Set Look Through", group_box)
    grid_layout.addWidget(set_look_thru_qpb, 0, 0, 1, 1)

    reload_image_plane_qpb = QtWidgets.QPushButton("Reload Image Sequence", group_box)
    grid_layout.addWidget(reload_image_plane_qpb, 1, 0, 1, 1)

    unlock_shape_cmd_qpb = QtWidgets.QPushButton("Unlock", group_box)
    grid_layout.addWidget(unlock_shape_cmd_qpb, 1, 1, 1, 1)


def populate_bake(parent_widget, parent_layout):
    group_box = QtWidgets.QGroupBox("Bake to Space", parent_widget)
    parent_layout.addWidget(group_box)
    main_layout = QtWidgets.QVBoxLayout(group_box)

    sub_row_layout = QtWidgets.QHBoxLayout()
    main_layout.addLayout(sub_row_layout)

    bake_reset_scale_qcb = QtWidgets.QCheckBox("Reset Scale", group_box)
    sub_row_layout.addWidget(bake_reset_scale_qcb)

    rotate_order_qcb = QtWidgets.QComboBox(group_box)
    rotate_order_qcb.addItems(["xyz", "yzx", "zxy", "xzy", "yxz", "zyx"])
    sub_row_layout.addWidget(rotate_order_qcb)

    bake_qpb = QtWidgets.QPushButton("Bake", group_box)
    main_layout.addWidget(bake_qpb)


def populate_notes(parent_widget, parent_layout):
    group_box = QtWidgets.QGroupBox("Notes", parent_widget)
    parent_layout.addWidget(group_box)
    layout = QtWidgets.QVBoxLayout(group_box)

    notes_qpte = QtWidgets.QPlainTextEdit(group_box)
    layout.addWidget(notes_qpte)

def populate_playblast(parent_widget, parent_layout):
    group_box = QtWidgets.QGroupBox("Playblast", parent_widget)
    parent_layout.addWidget(group_box)

    grid_layout = QtWidgets.QGridLayout(group_box)
    grid_layout.setContentsMargins(0, 0, 0, 0)
    do_playblast_qpb = QtWidgets.QPushButton("Playblast", group_box)
    do_playblast_qpb.setSizePolicy(SizePolicy.horizontal_expanding)
    do_playblast_qpb.setMinimumSize(QtCore.QSize(0, 30))
    # do_playblast_qpb.setMaximumSize(QtCore.QSize(30, 30))
    grid_layout.addWidget(do_playblast_qpb, 0, 0, 1, 1)

    playblast_options_qpb = QtWidgets.QPushButton("...", group_box)
    playblast_options_qpb.setMinimumSize(QtCore.QSize(30, 30))
    playblast_options_qpb.setMaximumSize(QtCore.QSize(30, 30))
    grid_layout.addWidget(playblast_options_qpb, 0, 1, 1, 1)


def populate_name_preset(parent_widget, parent_layout):
    group_box = QtWidgets.QGroupBox("Name Presets", parent_widget)
    parent_layout.addWidget(group_box)
    grid_layout = QtWidgets.QGridLayout(group_box)

    # Camera names
    label_camera_names = QtWidgets.QLabel("Camera Names", group_box)
    label_camera_names.setAlignment(Alignment.right_align)
    grid_layout.addWidget(label_camera_names, 0, 0, 1, 1)
    preset_camera_names_qle = QtWidgets.QLineEdit(group_box)
    grid_layout.addWidget(preset_camera_names_qle, 0, 1, 1, 1)
