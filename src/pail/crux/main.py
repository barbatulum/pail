from six import string_types

import maya.api.OpenMaya as om2


def get_depend_nodes(names):
    selection = om2.MSelectionList()
    for name in names:
        selection.add(name)
    return [selection.getDependNode(c) for c in range(len(names))]


def get_mobject(node):
    if isinstance(node, om2.MDagPath):
        return node.node()
    if isinstance(node, om2.MObjectHandle):
        return node.object()
    elif isinstance(node, om2.MObject):
        return node
    elif isinstance(node, string_types):
        return get_depend_nodes([node])[0]
    elif isinstance(node, (list, tuple)):
        return [get_mobject(o) for o in node]
    elif isinstance(node, om2.MObjectArray):
        return [get_mobject(node[c]) for c in range(len(node))]
    else:
        raise TypeError(node)


def convert_node(node, return_type):
    node = get_mobject(node)
    if return_type == om2.MObject:
        return node
    elif return_type == om2.MDagPath:
        return om2.MDagPath.getAPathTo(node)
    elif return_type in (
        om2.MFnDependencyNode,
        om2.MObjectHandle,
        om2.MFnDagNode,
    ):
        return return_type(node)
    elif return_type == 'shortName':
        return om2.MFnDependencyNode(node).name()
    elif return_type == 'fullPath':
        return om2.MDagPath.getAPathTo(node).fullPathName()
    elif return_type == 'partialPath':
        return om2.MDagPath.getAPathTo(node).partialPathName()
    else:
        raise TypeError(return_type)


def convert_nodes(nodes, return_type):
    return [convert_node(get_mobject(node), return_type) for node in nodes]


def get_parent(parent, return_type=om2.MObject):
    parent_node = convert_node(parent, om2.MFnDagNode).parent(0)
    return convert_node(parent_node, return_type)


def get_shapes(node, siblings=False):
    mobject = convert_node(node, om2.MObject)
    is_transform = mobject.hasFn(om2.MFn.kTransform)
    if not siblings and not is_transform:
        raise ValueError(
            "{0} has no shape, it's a transform node.".format(
                convert_node(mobject, om2.MFnDependencyNode)
            )
        )
    if is_transform:
        transform = mobject
    else:
        transform = get_parent(mobject)

    dag_path = om2.MDagPath.getAPathTo(transform)
    child_count = dag_path.numberOfShapesDirectlyBelow()
    shapes = [
        dag_path.extendToShape(cnt) for cnt in
        range(child_count)
    ]

    return shapes


def get_selection():
    """ API get selection """
    sel_list = om2.MGlobal.getActiveSelectionList()
    return [(sel_list.getDependNode(c)) for c in range(sel_list.length())]

def ls(node_type=om2.MFn.kCamera, return_type=om2.MObject):
    nodes = []
    dag_iter = om2.MItDag(om2.MItDag.kDepthFirst, node_type)
    while not dag_iter.isDone():
        obj = dag_iter.currentItem()
        nodes.append(obj)
        dag_iter.next()

    return convert_nodes(nodes, return_type)


def list_connections(*args, source=False, destination=True):
    src_plug = None
    arg_len = len(args)
    if arg_len == 2 and isinstance(args[1], string_types):
        src, attribute_name = args
    elif arg_len == 1 and isinstance(args[0], string_types):
        src, attribute_name = args[0].split('.')
    elif arg_len == 1 and isinstance(args[0], om2.MPlug):
        src_plug = args[0]
    else:
        raise TypeError("Invalid arguments: {0}".format(args))
    if src_plug is None:
        node = convert_node(src, om2.MFnDependencyNode)
        src_plug = node.findPlug(attribute_name, False)

    connections = {}
    if src_plug.isArray:
        indexes = src_plug.getExistingArrayAttributeIndices()
        for ind in indexes:
            child_plug = src_plug.connectionByPhysicalIndex(ind)
            connected = child_plug.connectedTo(source, destination)
            if connected:
                connections[ind] = (child_plug, connected)

    else:
        connected = src_plug.connectedTo(source, destination)
        if connected:
            connections[None] = (src_plug, connected)

    return connections


def is_attribute_settable(simple=False):
    """
    Verify is the attribute is settalbe, locked or connected, locked/animated by reference, expression, etc.
    if preferences are not set to be editalbe in the preference, cmds.getAttr(settable=1) will return True
    node in the reference that is locked can be unlocked even if it's referenced into the scene.
    """

