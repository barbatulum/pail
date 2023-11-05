import maya.api.OpenMaya as om2
from six import string_types

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


class Om2Error(object):
    OBJECT_EXISTENT = "(kInvalidParameter): Object does not exist"
    NO_MATCHING_NAMESPACE = "No namespace matches name"
