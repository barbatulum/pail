import maya.cmds as cmds
import maya.mel as mel
from typing import Union, Tuple, List


def get_working_time_range():
    """
    Get the highlighted time range or the playback range.
    """
    times = get_highlighted_time_range(as_string=False)
    if times[1] - times[0] == 1:
        times = get_range_slider_range(animation=True)
    return times


def get_highlighted_time_range(
    as_string: bool = False
) -> Union[str, Tuple[float, float]]:
    """
    Get highlighted time range from time slider.
    """
    time_range = cmds.timeControl(
        mel.eval('$tmpVar=$gPlayBackSlider'), query=True, range=True
    )
    if not as_string:
        time_range = (float(frame) for frame in time_range.split(':'))
    return time_range


def get_range_slider_range(animation: bool = True) -> Tuple[float, float]:
    """
    Get range slider range.
    """
    if animation:
        kwargs = ("animationStartTime", "animationEndTime")
    else:
        kwargs = ("minTime", "maxTime")

    # noinspection PyTypeChecker
    return tuple(
        cmds.playbackOptions(query=True, **{kwarg: True}) for kwarg in kwargs
    )

def clear_selected_animation(nodes: List[str] = None):
    """
    Clear animation curves of the give nodes or those of the selected nodes.
    """
    if not nodes:
        nodes = cmds.ls(sl=True)
    if not nodes:
        return
    anim_curves = cmds.keyframe(nodes, q=True, name=True)
    if anim_curves:
        cmds.cutKey(anim_curves)
