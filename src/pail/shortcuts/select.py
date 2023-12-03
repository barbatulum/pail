import maya.cmds as cmds
import maya.api.OpenMaya as om2
from .. import crux


def get_unique_names(mobjects):
    names = []
    for mobject in mobjects:
        try:
            # faster than using uniqueName
            names.append(om2.MDagPath.getAPathTo(mobject).fullPathName())
        except TypeError:
            fn = om2.MFnDependencyNode(mobject)
            names.append(fn.uniqueName())
    return names


def get_selection_names():
    selection = om2.MGlobal.getActiveSelectionList()
    names = []
    for cnt in range(selection.length()):
        try:
            # faster than using uniqueName
            names.append(selection.getDagPath(cnt).fullPathName())
        except TypeError:
            fn = om2.MFnDependencyNode(selection.getDependNode(cnt))
            names.append(fn.uniqueName())
    return names
def get_selection_roots():
    names = get_selection_names()
    roots = []
    for name in names:
        if "|" in name:
            name = name.split("|")[1]
        roots.append(name)
    return roots


def select_roots():
    cmds.select(get_selection_roots())


def select_hierarchy():
    cmds.select(hierarchy=True)


def select_first(*args):
    selection = om2.MGlobal.getActiveSelectionList()
    if selection.length():
        cmds.select(om2.MFnDependencyNode(selection.getDependNode(0)).uniqueName())

def select_last():
    selection = om2.MGlobal.getActiveSelectionList()
    length = selection.length()
    if length:
        cmds.select(om2.MFnDependencyNode(selection.getDependNode(length - 1)).uniqueName())

def reverse_selection():
    selected = get_selection_names()
    cmds.select(selected[::-1])


def filter_nodes(mobjects, node_types=()):
    valid_transforms = []
    for mobject in mobjects:
        shapes = []
        try:
            dag_path = om2.MDagPath.getAPathTo(mobject)
            if mobject.hasFn(om2.MFn.kTransform):
                transform = mobject
            else:
                transform = dag_path.transform()
                shapes = [mobject]
        except RuntimeError:
            transform = mobject
            shapes = [mobject]
        if not shapes:
            child_count = dag_path.numberOfShapesDirectlyBelow()
            shapes = [
                dag_path.extendToShape(c_cnt).node() for c_cnt in range(child_count)
            ]
        for shape in shapes:
            for node_type in node_types:
                if shape.hasFn(node_type):
                    if isinstance(transform, om2.MDagPath):
                        transform = transform.transform()
                    valid_transforms.append(
                        (
                            [om2.MFnDependencyNode(transform).uniqueName()],
                            [om2.MFnDependencyNode(s).uniqueName() for s in shapes],
                        )
                    )
                    break
    return valid_transforms


def filter_selection(node_types=()):
    selection = om2.MGlobal.getActiveSelectionList()
    mobjects = [
        selection.getDependNode(cnt) for cnt in range(selection.length())
    ]
    return filter_nodes(mobjects, node_types)


def select_filtered_selection(node_types=(), shape=False):
    cmds.select(
        [
            node
            for nodes in filter_selection(node_types=node_types)
            for node in nodes[int(shape)]
        ]
    )
