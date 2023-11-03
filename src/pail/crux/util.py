import sys

import maya.cmds as cmds
import pymel.all as pm


def warning(msg, ui=None, lasts=3000):
    cmds.inViewMessage(smg='<hl>{}</hl>'.format(msg), fade=1, pos='topCenter')
    cmds.warning(msg)
    if ui:
        ui.showMessage(msg, lasts)
    return msg

class Callback(object):
    def __init__(self, func, *args, **kwargs):
        self.func = func
        self.args = args
        self.kwargs = kwargs

    def __call__(self, *args):
        return self.func(*self.args, **self.kwargs)


def evaluate_expression():
    [pm.dgeval(i) for i in pm.ls(type='expression')]


def undo_dec(func):
    """
    A decorator that will make commands undoable in maya.
    """

    def _deco(*args, **kwargs):
        cmds.undoInfo(openChunk=True)
        func_return = None
        try:
            func_return = func(*args, **kwargs)
        except:
            print(sys.exc_info()[1])
        finally:
            cmds.undoInfo(closeChunk=True)
            return func_return

    return _deco
