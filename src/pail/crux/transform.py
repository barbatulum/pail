import six

import maya.cmds as cmds
import maya.api.OpenMaya as om2
import pymel.all as pm

from . import anim as anim
from . import constants as consts
from . import lssl as lssl
from .util import undo_dec, warning
from typing import Union


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
        ro = consts.ROTATE_ORDER[ro]
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
        #  todo: if camera's ro is connected, connect to locator and bake
        #   the locator's
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

    #  connect locator anim curves to
    #     # camera

    cmds.delete(locator)
    cmds.setAttr(camera, 1, 1, 1)


def transform_to_local(
    node,
    parent,
    frame_range,
    rotate_order=None,
    # it needs to be om2.MTransformationMatrix.kZYX, not om2.MEulerRotation.kZYX
):
    for frame in frame_range:
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
        rotate = new_fn.rotation(asQuaternion=False) # radians
        # ? scale = new_fn.scale(om2.MSpace.kTransform)
        yield translate, rotate


cmds.createNode('animCurveTL', name='translate')
cmds.createNode('animCurveTA', name='rotate')

for cnt in range(100):
    cmds.setKeyframe("animcurve_name", value=cnt, time=cnt)

