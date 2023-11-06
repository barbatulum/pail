
import maya.cmds as cmds
import maya.mel as mel


def clear_time_slider_keys():
    """
    Clear keys on time slider, at the current time or in the selected range.
    """
    time_slider = mel.eval('$temp=$gPlayBackSlider')
    cmds.cutKey(
        clear=True,
        includeUpperBound=False,
        animation='objects',
        time=tuple(cmds.timeControl(time_slider, q=1, rangeArray=1)),
        option='keys'
    )
