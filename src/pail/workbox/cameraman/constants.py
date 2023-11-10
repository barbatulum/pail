from PySide2 import QtWidgets


QtGetCommands = {
    QtWidgets.QComboBox: "currentText",
    QtWidgets.QCheckBox: "isChecked",
    QtWidgets.QLineEdit: "text",
    QtWidgets.QSpinBox: "value",
    QtWidgets.QDoubleSpinBox: "value",
    QtWidgets.QSlider: "value",
}

QtSetCommands = {
    QtWidgets.QComboBox: "setCurrentIndex",
    QtWidgets.QCheckBox: "setCheckState",
    QtWidgets.QLineEdit: "setText",
    QtWidgets.QSpinBox: "setValue",
    QtWidgets.QDoubleSpinBox: "setValue",
    QtWidgets.QSlider: "setValue",
}

QtAttributeSignal = {
    QtWidgets.QComboBox: "currentIndexChanged",
    QtWidgets.QCheckBox: "stateChanged",
    QtWidgets.QLineEdit: "editingFinished",
    QtWidgets.QSpinBox: "valueChanged",
    QtWidgets.QDoubleSpinBox: "valueChanged",
    QtWidgets.QSlider: "valueChanged",
}

ValidColorSpaces = ['Raw', 'sRGB', 'ACES2065-1']
SHOW_OPTIONS_MAPPING = {
    "Wireframe + Shaded": "wireframeOnShaded",
    "Image Plane": "imagePlane",
    "GPU Cache": "gpuCache",
    "SL Highlight": "selectionHiliteDisplay",
    "Nurbs": "nurbsCurves",
    "Polygon": "polymeshes",
    "Camera": "camera",
    "Locator": "locators",
}

class AttrEnumMapping:
    FitMode= {
        "Fill": 0,
        "Best": 1,
        "Horizontal": 2,
        "Vertical":3,
        "To Size":4,
    }

    DisplayMode = {
        'None': 0,
        'Outline': 1,
        'RGB': 2,
        'RGBA': 3,
        'Luminance': 4,
        'Alpha': 5,
    }

    ColorSpace = {
        'None': 0,
        'Outline': 1,
        'RGB': 2,
        'RGBA': 3,
        'Luminance': 4,
        'Alpha': 5,
    }
class Main:
    Camera = "_cameraman_camera_"
    ImagePlane = "_cameraman_image_plane_"
class ObjectName:
    ShowOptions = "show_options_"
    CameraList = "_cameraman_camera_list"
    ImagePlaneList = "_cameraman_image_plane_list"

    class Camera:
        base = Main.Camera
        group_box = "group_box"
        rotate_order = base + "rotate_order"
        far_clip_plane = base + "far_clip_plane"
        near_clip_plane = base + "near_clip_plane"


    class ImagePlane:
        base = Main.ImagePlane
        attributes_group_box = "attributes_group_box"
        cmds_group_box = "cmds_group_box"
        alpha_gain = base + "alpha_gain"
        browse_image_path = base + "browse_image_path"
        color_space = base + "color_space"
        display_mode = base + "display_mode"
        fit_mode = base + "fit_mode"
        image_path = base + "image_path"
        lock_shape = base + "lock_shape"
        placement_depth = base + "placement_depth"
        reload_image = base + "reload_image"
        set_look_through = base + "set_look_through"
        unlock_shape = base + "unlock_shape"

    class TransformBake:
        base = "_cameraman_transform_bake_"
        group_box = "group_box"
        reset_scale = base + "reset_scale"
        rotate_order = base + "rotate_order"
        do_bake = base + "do_bake"

    class Notes:
        base = "_cameraman_notes_"
        group_box = "group_box"
        notes_content = base + "notes_content"

    class Playblast:
        base = "_cameraman_playblast_"
        group_box = "group_box"
        do_playblast = base + "do_playblast"
        options = base + "options"

    class NamePresets:
        base = "_cameraman_name_presets_"
        group_box = "group_box"
        name_presets_field = "name_presets_field"

    class GUIOptions:
        base = "_cameraman_gui_options_"
        group_box = "group_box"
        disable_update_callback = "disable_update_callback"
        align_gui_to_scene = "align_gui_to_scene"
        # align_gui_to_scene_on_leaving = "align_gui_to_scene_on_leaving"

AttributeMapping = {
    ObjectName.ImagePlane.alpha_gain: "alphaGain",
    ObjectName.ImagePlane.color_space: "colorSpace",
    ObjectName.ImagePlane.display_mode: "displayMode",
    ObjectName.ImagePlane.fit_mode: "fit",
    ObjectName.ImagePlane.placement_depth: "depth",
    ObjectName.Camera.rotate_order: "rotateOrder",
    ObjectName.Camera.far_clip_plane: "farClipPlane",
    ObjectName.Camera.near_clip_plane: "nearClipPlane",
}
