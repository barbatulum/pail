import six

import maya.cmds as cmds
import maya.api.OpenMaya as om2
import pymel.all as pm

from . import _log as _log
from . import anim as anim
from . import constants as consts
from . import contexts as contexts
from . import lssl as lssl
from .util import undo_dec, warning
from typing import Union, List, Tuple

_logger = _log.get_logger(__name__)


@undo_dec
def bake_to_world(transform, mode='keyRange'):
    all_vec, all_rVec = [], []
    temp_loc = pm.spaceLocator()
    cst = pm.parentConstraint(transform, temp_loc, mo=0)
    f_start, f_end = pm.playbackOptions(q=1, min=1), pm.playbackOptions(
        q=1, max=1
    )
    for i in range(int(f_start), int(f_end + 1)):
        all_vec.append(temp_loc.t.get(t=i))
        all_rVec.append(temp_loc.r.get(t=i))
    pm.delete(temp_loc)
    transform.setParent(w=1)
    for ats in transform.t, transform.r:
        ats.unlock()
        pm.cutKey(ats)
        [attr.unlock() for attr in ats.children()]
        [pm.cutKey(attr) for attr in ats.children()]
    for c in range(int(f_start), int(f_end + 1)):
        pm.setKeyframe(transform, t=c, at='tx', v=all_vec[c - int(f_start)][0])
        pm.setKeyframe(transform, t=c, at='ty', v=all_vec[c - int(f_start)][1])
        pm.setKeyframe(transform, t=c, at='tz', v=all_vec[c - int(f_start)][2])
        pm.setKeyframe(
            transform, t=c, at='rx', v=all_rVec[c - int(f_start)][0]
        )
        pm.setKeyframe(
            transform, t=c, at='ry', v=all_rVec[c - int(f_start)][1]
        )
        pm.setKeyframe(
            transform, t=c, at='rz', v=all_rVec[c - int(f_start)][2]
        )


def set_rotate_order(transform, ro):
    if isinstance(ro, (float, int)):
        ro = int(ro)
    elif isinstance(ro, six.string_types):
        ro = getattr(consts.CmdsRotateOrder, "k" + ro.upper())
    transform.ro.set(ro)


def set_rotate_order_cmds(camera, ro):
    if isinstance(ro, (float, int)):
        ro = int(ro)
    elif isinstance(ro, six.string_types):
        ro = dict(xyz=0, yzx=1, zxy=2, xzy=3, yxz=4, zyx=5)[ro]
    cmds.setAttr(camera + ".rotateOrder", ro)


@undo_dec
def unlock_shapes(cam_tsf):
    unlock_all(cam_tsf)
    for shape in cam_tsf.getShapes():
        unlock_all(shape)


def unlock_all(obj):
    for attr in obj.listAttr(locked=1):
        try:
            attr.unlock()
        except:
            warning('{} is unlockable'.format(attr))


def is_parentable(node: str = ""):
    """
    Return whether the given node can be parented to other nodes.
    """
    try:
        node_ref = cmds.referenceQuery(node, referenceNode=1)
    except RuntimeError as err:
        if not str(err).endswith(consts.Om2Error.NOT_FROM_REFERENCE):
            raise
        return True

    parents = cmds.listRelatives(node, parent=True)
    if not parents:
        return True

    parent = parents[0]
    try:
        parent_ref = cmds.referenceQuery(parent, referenceNode=1)
    except RuntimeError as err:
        if not str(err).endswith(consts.Om2Error.NOT_FROM_REFERENCE):
            raise
        return True
    if parent_ref != node_ref:
        return True
    return False


def transform_to_local_space(
    node,
    parent,
    frames,
    rotate_order=None,
    # it needs to be om2.MTransformationMatrix.kZYX,
    # not om2.MEulerRotation.kZYX
):
    frame_values = {}
    for frame in frames:
        node_matrix = lssl.get_matrix_data(node, frame=frame).matrix()
        parent_matrix = lssl.get_matrix_data(parent, frame=frame).matrix()
        new_matrix = node_matrix * parent_matrix.inverse()
        new_fn = om2.MTransformationMatrix(new_matrix)
        # though new_fn.reorderRotation(rotate_order) is slower than
        # new_fn.rotation(asQuaternion=False).reorderIt(rotate_order):
        #         if rotate_order is not None:
        #             rotate.reorderIt(rotate_order)
        # we use later one for readability.
        if rotate_order is not None:
            new_fn.reorderRotation(rotate_order)

        translate = new_fn.translation(
            om2.MSpace.kTransform
        )  # om2.MSpace.kWorld
        rotate = new_fn.rotation(asQuaternion=False)  # radians
        frame_values.setdefault(frame, {})["translate"] = translate
        # ? scale = new_fn.scale(om2.MSpace.kTransform)
        frame_values.setdefault(frame, {})["rotate"] = rotate
    return frame_values


def bake_to_local_space(
    node,
    parent,
    process_locked_nodes: bool = True,
    process_locked_attrs: bool = True,
    process_referenced_nodes: bool = True,
    translate: bool = True,
    rotate: bool = True,
    frame_range: Union[str, List, Tuple] = "working",
    rotate_order: Union[None, str, int] = None,
):
    transform_attributes = ""
    if translate:
        transform_attributes += "t"
    if rotate:
        transform_attributes += "r"
    transform_attributes = [
        "{0}.{1}{2}".format(node, attribute, axis)
        for attribute in transform_attributes for axis in " xyz"
    ]
    if not process_referenced_nodes:
        if cmds.referenceQuery(node, isNodeReferenced=True):
            _logger.error("Node %s is referenced, aborting.", node)
            return

    node_locked = cmds.lockNode(node, query=True)
    parent_locked = False
    if parent:
        parent_locked = cmds.lockNode(parent, query=True)
    if node_locked or parent_locked and not process_locked_nodes:
        _logger.error(
            "Node %s is locked, you have to set process_locked_nodes"
            " to True to proceed, aborting.",
            node,
        )
        return False

    if not process_locked_attrs and any(
        cmds.getAttr(attr, lock=True)
        for attr in transform_attributes
    ):
        _logger.error("Some of the attributes are locked, aborting.")
        return False

    if parent and not is_parentable(node):
        _logger.error(
            "Node %s is not one of the top level nodes in the reference "
            "hence cannot be parented to %s, aborting.",
            node, parent
        )
        return False
    if frame_range == "working":
        frame_range = anim.get_working_time_range()
    elif not isinstance(frame_range, (list, tuple)):
        frame_range = anim.get_range_slider_range()
    frames = anim.plot_frames(*frame_range)

    # with contexts.LockContext([node, parent]+ attributes) as X,
    # contexts.NamespaceContext() as Y, C() as Z:
    nodes = [node]
    if parent:
        nodes.append([parent])
    with contexts.LockContext(
        nodes + transform_attributes
    ), contexts.NamespaceContext():
        connected_curves = {
            attr: cmds.listConnections(source=True, destination=False) for attr
            in transform_attributes
        }
        for destinations, src in connected_curves.items():
            if not destinations:
                continue
            # As cutKey clear the spreadsheets of referenced animation curves,
            # we disconnect them to keep them intact.
            for dst in destinations:
                if not cmds.referenceQuery(dst, isNodeReferenced=True):
                    continue
                cmds.disconnectAttr(src, dst, nextAvailable=True)
            anim.clear_animation([node])

        frame_values = transform_to_local_space(
            node, parent, frames=frames, rotate_order=rotate_order
        )
        translate_curves = []
        rotate_curves = []
        for axis in "XYZ":
            if translate:
                translate_curves.append(
                    cmds.createNode(
                        'animCurveTL',
                        name='{0}_translate{1}'.format(node, axis)
                    )
                )

            if rotate:
                rotate_curves.append(
                    cmds.createNode(
                        'animCurveTA', name='{0}_rotate{1}'.format(node, axis)
                    )
                )

        for key, curve_nodes in zip(
            ("translate", "rotate"), (translate_curves, rotate_curves)
        ):
            for frame, values in frame_values.items():
                for axis_cnt in range(3):
                    cmds.setKeyframe(
                        curve_nodes[axis_cnt],
                        value=frame_values[frame][key][axis_cnt],
                        time=frame,
                    )


def constraint_bake(
    camera,
    constraint_type: str = "parentConstraint",
    use_working_range: bool = True,
    rotate_order: Union[None, str, int] = None,
    new_parent: Union[None, str] = None,
):
    if use_working_range:
        time_range = anim.get_working_time_range()
    else:
        time_range = anim.get_range_slider_range(animation=False)

    locator = cmds.spaceLocator(name="worldLoc")[0]
    cam_ro = cmds.getAttr(camera + ".rotateOrder")
    if rotate_order is None:
        # todo: lock context,
        # todo: if camera's ro is connected, connect to locator and bake
        #       the locator's
        cmds.setAttr(locator + ".rotateOrder", cam_ro)
    else:
        set_rotate_order_cmds(locator, rotate_order)

    if new_parent:
        cmds.parent(locator, new_parent)

    constraint = getattr(cmds, constraint_type)(
        camera, locator, maintainOffset=False
    )

    # bake locator

    # cut camera keys,
    if new_parent is None:
        camera = cmds.parent(camera, world=True)[0]
    else:
        camera = cmds.parent(camera, new_parent)[0]

    cmds.delete(locator)
    cmds.setAttr(camera, 1, 1, 1)
