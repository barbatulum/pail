import maya.api.OpenMaya as om2
from six import string_types

RotateOrderStr = ["xyz", "yzx", "zxy", "xzy", "yxz", "zyx"]

class CmdsRotateOrder:
    kXYZ = om2.MEulerRotation.kXYZ
    kYZX = om2.MEulerRotation.kYZX
    kZXY = om2.MEulerRotation.kZXY
    kXZY = om2.MEulerRotation.kXZY
    kYXZ = om2.MEulerRotation.kYXZ
    kZYX = om2.MEulerRotation.kZYX



def get_rotate_order(rotate_order, data_source=om2.MTransformationMatrix):
    # om2.MEulerRotation, cmds rotate order are the same as MEulerRotation
    if isinstance(rotate_order, string_types):
        return getattr(data_source, "k" + rotate_order.upper())


class Om2Error:
    OBJECT_EXISTENT = "(kInvalidParameter): Object does not exist"
    NO_MATCHING_NAMESPACE = "No namespace matches name"
    NOT_FROM_REFERENCE = "not from a referenced file"


class PanelType:
    """
    Since maya.cmds takes strings, Object.KEY is faster then Enum's Object.KEY.value
    """
    model_panel = 'modelPanel'
    graph_editor = 'graphEditor'
    outliner_panel = 'outlinerPanel'
    node_editor = 'nodeEditorPanel'
    scripted_panel = 'scriptedPanel'


EditorNameMapping = {
    'graphEditor': 'GraphEd',
    'nodeEditorPanel': 'NodeEditorEd'
}


class GraphEditorRetrievingParameters:
    valid_mode = 'visible'
    working_order = ('focus', 'visible')
    reverse_visible_order = False