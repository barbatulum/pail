import math
from typing import Union, Tuple, List

import maya.cmds as cmds
import maya.mel as mel

from . import _log


_logger = _log.get_logger(__name__)


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


def plot_frames(
    start: Union[float, int],
    end: Union[float, int],
    sub_steps: Union[None, int] = None,
    step_size: Union[float, int] = 1,
    include: bool = False
) -> List[float]:
    # todo: support frame relative samples
    int_start = int(math.floor(start))
    int_end = int(math.ceil(end))
    if sub_steps is not None and not isinstance(sub_steps, int):
        raise RuntimeError(
            "Supplied sub_steps needs to be an integer.", sub_steps
        )

    if isinstance(sub_steps, int):
        steps = sub_steps + 1
        intervals = [1. / steps * step for step in range(1, steps)]
        _logger.warning(
            "sub_steps is supplied (%s), ignoring step_size %s", sub_steps,
            step_size
        )
    elif step_size > 1:
        raise RuntimeError("step_size needs to be strictly between zero and one.")
    else:
        intervals = [
            step_size * (1 + cnt) for cnt in range(int(1. // step_size))
        ]
    frames = {int_start - f for f in reversed(intervals)}
    for frame in range(int_start, int_end + 1):
        frames.add(float(frame))
        for interval in intervals:
            frames.add(frame + interval)
    if include:
        frames.update((float(start), float(end)))
    return sorted(frames)
