import six
import pymel.all as pm

from .util import undo_dec, warning


@undo_dec
def bake_to_world(transform, mode='keyRange'):
    all_vec, all_rVec = [], []
    temp_loc = pm.spaceLocator()
    cst = pm.parentConstraint(transform, temp_loc, mo=0)
    f_start, f_end = pm.playbackOptions(q=1, min=1), pm.playbackOptions(q=1, max=1)
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
        pm.setKeyframe(transform, t=c, at='rx', v=all_rVec[c - int(f_start)][0])
        pm.setKeyframe(transform, t=c, at='ry', v=all_rVec[c - int(f_start)][1])
        pm.setKeyframe(transform, t=c, at='rz', v=all_rVec[c - int(f_start)][2])


def set_rotate_order(transform, ro):
    if isinstance(ro, (float, int)):
        ro = int(ro)
    elif isinstance(ro, six.string_types):
        ro = dict(xyz=0, yzx=1, zxy=2, xzy=3, yxz=4, zyx=5)[ro]
    transform.ro.set(ro)


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
