from six import string_types

import maya.api.OpenMaya as om2


def get_selection():
    """ API get selection """
    sel_list = om2.MGlobal.getActiveSelectionList()
    return [(sel_list.getDependNode(c)) for c in range(sel_list.length())]


def get_shape(mObj):
    """ get the shape of given object, if it's already a shape, return itself"""
    shapes = []
    if mObj.hasFn(om2.MFn.kTransform):
        for c in range(mobj2(mObj, 'dagPath').numberOfShapesDirectlyBelow()):
            shapes.append(mobj2(mObj, 'dagPath').extendToShape(c).node())
    elif mObj.hasFn(om2.MFn.kShape):
        shapes.append(mObj)
    return shapes


def get_parent(mObj):
    """ as title """
    return mobj2(mObj, 'dagFn').parent(0)


def api_ls(return_type, obj_type=None):
    """ ls object by API"""
    dagIterator = om2.MItDependencyNodes(obj_type)
    result = []
    while (not dagIterator.isDone()):
        current = dagIterator.thisNode()
        result.append(current)
        dagIterator.next()
    return [mobj2(i, return_type) for i in result]


def handle_tsf(handle, nodeType):
    return mobj2(get_parent(mobj2(handle, 'mobj')), nodeType)


def get_nodes_tsf(obj, returnType):
    """ Return the shape node, even if you select its tranform parent"""
    returnV = None
    if not obj.hasFn(om2.MFn.kDagNode):
        return
    if obj.hasFn(returnType):
        returnV = obj
    else:
        slDagPath = mobj2(obj, 'dagPath')
        if not slDagPath.numberOfShapesDirectlyBelow():
            return None
        shape = slDagPath.extendToShape(0)
        if shape.hasFn(returnType):
            returnV = shape
    return returnV


def mobj2(obj, return_type):
    def get(obj, return_type):
        if return_type == 'shortName':
            return om2.MFnDependencyNode(obj).name()
        elif return_type == 'fullPath':
            return om2.MDagPath.getAPathTo(obj).fullPathName()
        elif return_type == 'fn':
            return om2.MFnDependencyNode(obj)
        elif return_type == 'partialPath':
            return om2.MDagPath.getAPathTo(obj).partialPathName()
        elif return_type == 'handle':
            return om2.MObjectHandle(obj)
        elif return_type == 'dagPath':
            return om2.MDagPath.getAPathTo(obj)
        elif return_type == 'dagFn':
            return om2.MFnDagNode(obj)
        elif return_type == 'mobj':
            return obj

    def convert(obj):
        if isinstance(obj, om2.MDagPath):
            return obj.node()
        if isinstance(obj, om2.MObjectHandle):
            return obj.object()
        elif isinstance(obj, om2.MObject):
            return obj
        elif isinstance(obj, string_types):
            return get_depend_node(obj)
        elif isinstance(obj, (list, tuple)):
            return [convert(o) for o in obj]
        elif isinstance(obj, om2.MObjectArray):
            return [convert(obj[c]) for c in range(len(obj))]
        else:
            raise TypeError(obj)

    obj = convert(obj)
    if isinstance(obj, list):
        return [get(o, return_type) for o in obj]
    elif isinstance(obj, om2.MObject):
        return get(obj, return_type)
    else:
        raise TypeError(obj)


def get_depend_node(name_str):
    node = []
    if isinstance(name_str, list):
        for name in name_str:
            selection = om2.MSelectionList()
            selection.add(name)
        node = [selection.getDependNode(c) for c in range(len(name_str))]
    else:
        selection = om2.MSelectionList()
        selection.add(name_str)
        node = selection.getDependNode(0)
    return node
