from typing import Union

import maya.cmds as cmds


def toggle_work_and_timeline_boundary(end: bool = False):
    """
    Toggle between timeline start/end and work range start/end.
    """
    args = {'minTime': True}, {'animationStartTime': True}
    if end:
        args = {'maxTime': True}, {'animationEndTime': True}
    current_time = cmds.currentTime(query=True)
    work_time = cmds.playbackOptions(query=True, **args[0])
    timeline_time = cmds.playbackOptions(query=True, **args[1])
    if current_time == work_time:
        cmds.currentTime(timeline_time)
    else:
        cmds.currentTime(work_time)


def play_with_handle(frames: float = 6.):
    """
    Start playing with a handle of frames.
    """
    if cmds.play(query=True, state=True):
        cmds.play(state=False)
    else:
        start_time = cmds.currentTime(query=True) - frames
        min_time = cmds.playbackOptions(query=True, minTime=True)
        if start_time < min_time:
            start_time = min_time
        cmds.currentTime(start_time)
        cmds.play(state=True)


def step_thru_frames(frames: Union[float, int]):
    """
    Step through timeline by the given frames.
    """
    cmds.currentTime(cmds.currentTime(query=True) + frames)
