from numbers import Number
from typing import Union, List

import maya.api.OpenMaya as om2

from . import _log as _log
from . import constants as consts

_logger = _log.get_logger(__name__)
_NODE_TYPE_CMD = {om2.MObject: "getDependNode", om2.MDagPath: "getDagPath"}

def get_nodes(
    items: List[Union[om2.MObject, om2.MDagPath, str]],
    return_type=Union[om2.MObject, om2.MDagPath, str]
) -> List[Union[om2.MObject, om2.MDagPath, str]]:
    """
    Get strings, MObjects or MDagPaths from given objects.
    """
    invalids, nonexistents = [], []
    base_types = (str, om2.MDagPath, om2.MObject)

    invalids = [item for item in items if not isinstance(item, base_types)]
    if invalids:
        _logger.critical(
            "Invalid objects to get %s: %s",
            tuple((i, type(i)) for i in invalids),
            invalids
        )
    ms_list = om2.MSelectionList()
    for item in items:
        try:
            ms_list.add(item)
        except RuntimeError as e:
            if str(e).startswith(consts.Om2Error.OBJECT_EXISTENT):
                nonexistents.append(item)
            else:
                raise

    if invalids or nonexistents:
        raise RuntimeError("Given objects {} are not all valid.".format(items))

    if return_type is str:
        return ms_list.getSelectionStrings()
    else:
        try:
            get_cmd = getattr(ms_list, _NODE_TYPE_CMD[return_type])
        except KeyError:
            raise KeyError(
                "{0} is invalid, it must be one of the {1}".format(
                    return_type, _NODE_TYPE_CMD.keys()
                )
            )
        return [get_cmd(count) for count in range(ms_list.length())]


def get_matrix_data(
    mobj: om2.MObject,
    frame: Union[None, Number],
    mtime_unit: Union[None, int]
) -> om2.MFnMatrixData:
    """
    Get om2.MFnMatrixData data from given MObject at given frame, using given
    MTime unit.
    """
    fn = om2.MFnDependencyNode(mobj)
    plug = fn.findPlug('worldMatrix', False)
    plug = plug.elementByLogicalIndex(0)
    arg = ()
    if mtime_unit is None:
        mtime_unit = om2.MTime.uiUnit()
    if frame is not None:
        arg = (om2.MDGContext(om2.MTime(frame, mtime_unit)),)

    plug_mobj = plug.asMObject(*arg)
    return om2.MFnMatrixData(plug_mobj)


def get_transform_matrix(
    node_mobj: om2.MObject,
    frame: Union[None, Number] = None,
    mtime_unit: Union[None, int] = None,
):
    """
    Get om2.MTransformationMatrix from given MObject at given frame, using
    given MTime unit.
    """
    matrix_data = get_matrix_data(
        node_mobj, frame=frame, mtime_unit=mtime_unit
        )
    return om2.MTransformationMatrix(matrix_data.matrix())
