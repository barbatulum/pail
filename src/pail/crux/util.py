import sys

import maya.cmds as cmds
import pymel.all as pm


def evaluate_expression():
    [cmds.dgeval(exp) for exp in cmds.ls(type='expression')]
