import os
from six import integer_types

import maya.cmds as cmds
import maya.mel as mel
import pymel.all as pm

from . import util
from .contexts import undo_chunk


@undo_chunk
def set_clip_plane(cam, near, far):
    cmds.setAttr(cam + '.nearClipPlane', near)
    cmds.setAttr(cam + '.farClipPlane', far)


@undo_chunk
def set_image_name(image_plane, file_path):
    cmds.setAttr(image_plane + ".imageName", "")
    cmds.setAttr(image_plane + ".useFrameExtension", 0)
    if os.path.isfile(file_path) and os.access(file_path, os.R_OK):
        cmds.setAttr(image_plane + ".imageName", file_path)
        cmds.setAttr(image_plane + ".useFrameExtension", 1)


def create_new_cam(panel, look_at=True):
    """ Create new camera """
    cam = None
    if not panel:
        look_at = False
    else:
        current_cam = cmds.modelPanel(panel, q=1, cam=1)
        if not current_cam:
            look_at = False
    new_cam = pm.createNode('camera').getParent()
    if look_at:
        pm.xform(new_cam, ws=1, t=pm.xform(current_cam, q=1, ws=1, t=1))
        pm.xform(new_cam, ws=1, ro=pm.xform(current_cam, q=1, ws=1, ro=1))
        pm.move(new_cam, (0, 0, pm.PyNode(current_cam).centerOfInterest.get() * -1), r=1, os=1, wd=1)
        [i.set(0) for i in new_cam.r.children()]
    return new_cam


@undo_chunk
def lock_cam_tsf(cam, lock_it=True):
    for attr in cam.t, cam.r:
        attr.setLocked(lock_it)
        for child in attr.children():
            child.setLocked(lock_it)
    camShape = cam.getShape()
    camShape.hfa.setLocked(lock_it)
    camShape.vfa.setLocked(lock_it)
    camShape.fl.setLocked(lock_it)
    camShape.lsr.setLocked(lock_it)


@undo_chunk
def reload_image_sequence(imagePlane):
    imagePlane.frameExtension.unlock()
    pm.delete(imagePlane.frameExtension.listConnections())
    cmds.setAttr(imagePlane.name() + '.useFrameExtension', 1)
    # pm.mel.eval(imagePlane.name())
    pm.mel.eval('ogs -reset')
    util.evaluate_expression()


def set_colorspace(imagePlane, colorspace):
    pm.mel.eval("colorManagementPrefs -edit -cmEnabled 1")
    imagePlane.colorSpace.set(colorspace)


def set_colorspace_display_mode(imagePlane, mode):
    if not isinstance(mode, integer_types):
        mode = {'None': 0, 'RGB': 2, 'RGBA': 3}[mode]
    imagePlane.displayMode.set(mode)


def look_thru(imagePlane):
    imagePlane.displayOnlyIfCurrent.set(0)
    imagePlane.displayOnlyIfCurrent.set(1)

@undo_chunk
def bake_to_world2(camera, reset_scale=True):
    min_time = cmds.playbackOptions(q=True, minTime=True)
    max_time = cmds.playbackOptions(q=True, maxTime=True)

    world_loc = cmds.spaceLocator(name="worldLoc")[0]
    cam_rotate_order = cmds.getAttr(camera + ".rotateOrder")
    cmds.setAttr(world_loc + ".rotateOrder", cam_rotate_order)

    paren_constraint = cmds.parentConstraint(camera, world_loc, maintainOffset=False)

    cmds.ogs(pause=True)
    cmds.bakeResults(
        world_loc, simulation=True, attribute=["tx", "ty", "tz", "rx", "ry", "rz"], time=(min_time, max_time)
    )
    cmds.ogs(pause=True)

    cmds.delete(paren_constraint)  # Delete parent constraint.

    cmd = 'cutKey -time ":" -hierarchy none  -at "tx" -at "ty" -at "tz" -at "rx" -at "ry" -at "rz" {0};'.format(
        camera
    )
    mel.eval(cmd)
    unparented_cam = cmds.parent(camera, world=True)[0]

    cmd = 'cutKey -time ":" -hierarchy none  -at "tx" -at "ty" -at "tz" -at "rx" -at "ry" -at "rz" {0};'.format(
        world_loc
    )
    mel.eval(cmd)

    cmd = (
        'pasteKey -option replaceCompletely -copies 1 -connect 0 -timeOffset 0 -floatOffset 0 -valueOffset 0 '
       '"{0}";'.format(unparented_cam)
    )
    mel.eval(cmd)
    cmds.delete(world_loc)

    if reset_scale:
        cmds.setAttr(unparented_cam + ".sx", 1)
        cmds.setAttr(unparented_cam + ".sy", 1)
        cmds.setAttr(unparented_cam + ".sz", 1)