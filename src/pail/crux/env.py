import maya.api.OpenMaya as om2


def is_interactive():
    return om2.MGlobal.mayaState() == om2.MGlobal.kInteractive