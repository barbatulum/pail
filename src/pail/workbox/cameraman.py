# -*- coding: utf-8 -*-
import os
import sys
from six import integer_types, string_types

import maya.mel as mel
import maya.cmds as cmds
import pymel.all as pm
import maya.api.OpenMaya as om2



from PySide2 import QtCore, QtGui, QtWidgets

from ..crux import camera, main, gui, main, transform, util
from ..crux.util import Callback, undo_dec


class CameramanGUI(QtWidgets.QMainWindow):
    def __init__(self, parent):
        QtWidgets.QMainWindow.__init__(self, parent)
        # dockable
        # self.setObjectName('CamTool')
        mel.eval("colorManagementPrefs -edit -cmEnabled 1")
        self.callback = None
        self.setWindowTitle('CamTool')
        self.resize(675, 760)
        self.last_active_panel = None
        self.update_panel()

        self.statusBar = QtWidgets.QStatusBar(self)
        set_font_size(self.statusBar, 13)
        self.setStatusBar(self.statusBar)

        # arrange layout
        self.win_central_widget = QtWidgets.QWidget(self)
        self.setCentralWidget(self.win_central_widget)
        self.win_gridLayout = QtWidgets.QGridLayout(self.win_central_widget)  # top most window layout
        self.panel_vis_layoutWidget = QtWidgets.QWidget(self.win_central_widget)
        self.panel_vis_layout = QtWidgets.QHBoxLayout(self.panel_vis_layoutWidget)
        self.sep_layoutWidget = QtWidgets.QWidget(self.win_central_widget)
        self.sep_layout = QtWidgets.QHBoxLayout(self.sep_layoutWidget)
        self.main_layoutWidget = QtWidgets.QWidget(self.win_central_widget)  # layout to contain left and right column
        self.main_layout = QtWidgets.QHBoxLayout(self.main_layoutWidget)
        self.left_widget = QtWidgets.QWidget(self.main_layoutWidget)
        self.left_layout = QtWidgets.QVBoxLayout(self.left_widget)
        self.right_widget = QtWidgets.QWidget(self.main_layoutWidget)
        self.right_layout = QtWidgets.QVBoxLayout(self.right_widget)

        self.win_gridLayout.addWidget(self.main_layoutWidget, 2, 0, 1, 1)
        self.win_gridLayout.addWidget(self.sep_layoutWidget, 1, 0, 1, 1)
        self.win_gridLayout.addWidget(self.panel_vis_layoutWidget, 0, 0, 1, 1)
        self.main_layout.addWidget(self.left_widget)
        self.main_layout.addWidget(self.right_widget)

        self.panel_vis_layout.setContentsMargins(0, 0, 0, 0)
        self.panel_vis_layout.setContentsMargins(0, 0, 0, 0)
        self.sep_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.left_layout.setContentsMargins(0, 0, 0, 0)
        self.right_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setStretch(0, 0)
        self.main_layout.setStretch(1, 1)

        # left column
        # camera/imagePlane list related function
        self.func_list = FuncLayout(self.left_widget)
        self.refresh_cam_QPB = self.func_list.add(QtWidgets.QPushButton('Refresh'))
        self.prior_QPB = self.func_list.add(QtWidgets.QPushButton('Camera first'))
        self.prior_QPB.setCheckable(1)

        self.refresh_cam_QPB.clicked.connect(self.refresh)
        self.prior_QPB.clicked.connect(self.switch_lists)

        # camera scroll area
        self.cam_listWidget = ListWidget(self.left_widget)
        self.imagePlane_listWidget = ListWidget(self.left_widget)

        def set_menu_signal(listWidget, function):
            listWidget.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
            listWidget.connect(listWidget, QtCore.SIGNAL('customContextMenuRequested(QPoint)'), function)

        set_menu_signal(self.cam_listWidget, self.rClick_cam)
        set_menu_signal(self.imagePlane_listWidget, self.rClick_imagePlane)

        # only cam currentItem changed need to update?
        self.cam_listWidget.currentItemChanged.connect(self.update_cam_sets)
        # selection change - update ui
        self.cam_listWidget.itemSelectionChanged.connect(Callback(self.click_update, self.cam_listWidget))
        self.imagePlane_listWidget.itemSelectionChanged.connect(Callback(self.click_update, self.imagePlane_listWidget))
        # double click - select
        self.cam_listWidget.doubleClicked.connect(lambda: self.select_node(self.cam_listWidget))
        self.imagePlane_listWidget.doubleClicked.connect(lambda: self.select_node(self.imagePlane_listWidget))

        self.func_panel_vis = FuncLayout(self.panel_vis_layoutWidget)
        self.vis_wireframeOnShaded_QPB = self.func_panel_vis.add(QtWidgets.QPushButton('Wireframe on Shaded'))
        self.vis_imagePlane_QPB = self.func_panel_vis.add(QtWidgets.QPushButton('ImagePlane'))
        self.vis_gpuCache_QPB = self.func_panel_vis.add(QtWidgets.QPushButton('GPU Cache'))
        self.vis_selectionHiliteDisplay_QPB = self.func_panel_vis.add(QtWidgets.QPushButton('SL Highlight'))
        self.vis_nurbsCurves_QPB = self.func_panel_vis.add(QtWidgets.QPushButton('Nurbs'))
        self.vis_polymeshes_QPB = self.func_panel_vis.add(QtWidgets.QPushButton('Polygon'))
        self.vis_cameras_QPB = self.func_panel_vis.add(QtWidgets.QPushButton('Camera'))
        self.vis_locators_QPB = self.func_panel_vis.add(QtWidgets.QPushButton('Locators'))

        for child in self.func_panel_vis.children():
            if isinstance(child, QtWidgets.QPushButton):
                child.setCheckable(1)

        self.vis_wireframeOnShaded_QPB.clicked.connect(
            lambda: gui.set_show_hide(self.update_panel(), 'wireframeOnShaded', self.vis_wireframeOnShaded_QPB.isChecked())
            )
        self.vis_imagePlane_QPB.clicked.connect(
            lambda: gui.set_show_hide(self.update_panel(), 'imagePlane', self.vis_imagePlane_QPB.isChecked())
            )
        self.vis_gpuCache_QPB.clicked.connect(
            lambda: gui.set_show_hide(self.update_panel(), 'gpuCache', self.vis_gpuCache_QPB.isChecked())
            )
        self.vis_selectionHiliteDisplay_QPB.clicked.connect(
            lambda: gui.set_show_hide(
                self.update_panel(), 'selectionHiliteDisplay', self.vis_selectionHiliteDisplay_QPB.isChecked()
                )
            )
        self.vis_nurbsCurves_QPB.clicked.connect(
            lambda: gui.set_show_hide(self.update_panel(), 'nurbsCurves', self.vis_nurbsCurves_QPB.isChecked())
            )
        self.vis_polymeshes_QPB.clicked.connect(
            lambda: gui.set_show_hide(self.update_panel(), 'polymeshes', self.vis_polymeshes_QPB.isChecked())
            )
        self.vis_cameras_QPB.clicked.connect(
            lambda: gui.set_show_hide(self.update_panel(), 'camera', self.vis_cameras_QPB.isChecked())
            )
        self.vis_locators_QPB.clicked.connect(
            lambda: gui.set_show_hide(self.update_panel(), 'locators', self.vis_locators_QPB.isChecked())
            )

        add_separator(self.sep_layoutWidget, 10)

        # right column
        # function set: color space of image plane
        self.func_colorspace = FuncLayout(self.right_widget)
        self.func_colorspace.add(QtWidgets.QLabel('Color Space'))
        self.colorspace_QCombo = self.func_colorspace.add(QtWidgets.QComboBox())
        self.colorspace_QCombo.addItems(['Raw', 'sRGB', 'ACES2065-1'])

        self.colorspace_QCombo.currentIndexChanged.connect(
            lambda: camera.set_colorspace(self.get_image_plane(), self.colorspace_QCombo.currentText())
            )

        # function set: color space mode of image plane
        self.func_colorspace_mode = FuncLayout(self.right_widget)
        self.func_colorspace_mode.add(QtWidgets.QLabel('Display Mode'))
        self.display_mode_QCombo = self.func_colorspace_mode.add(QtWidgets.QComboBox())
        self.display_mode_QCombo.addItems(['None', 'Outline', 'RGB', 'RGBA', 'Luminance', 'Alpha'])

        self.display_mode_QCombo.currentIndexChanged.connect(
            lambda: camera.set_colorspace_display_mode(self.get_image_plane(), self.display_mode_QCombo.currentIndex())
            )

        # function set: Toggle look thru to force image plane to refresh
        self.func_setLookThru = FuncLayout(self.right_widget)
        self.setLookThru_QPB = self.func_setLookThru.add(QtWidgets.QPushButton('Set Look Thru'))

        self.setLookThru_QPB.clicked.connect(lambda: camera.look_thru(self.get_image_plane()))

        # function set: reload image sequence by disconnecting frame expression
        self.func_reloadIS = FuncLayout(self.right_widget)
        self.reloadIS_QPB = self.func_reloadIS.add(QtWidgets.QPushButton('Reload image sequence'))

        self.reloadIS_QPB.clicked.connect(lambda: camera.reload_image_sequence(self.get_image_plane()))

        # function set: image path
        self.func_imageName = FuncLayout(self.right_widget)
        self.func_imageName.add(QtWidgets.QLabel('Image Name'))
        self.imageName_QLE = self.func_imageName.add(QtWidgets.QLineEdit())
        self.browseImagePath_QPB = self.func_imageName.add(QtWidgets.QPushButton('...'))

        self.imageName_QLE.editingFinished.connect(lambda: self.set_image_name(self.imageName_QLE.text()))
        self.browseImagePath_QPB.clicked.connect(self.browse_image_path)

        # function set: image plane's depth and fit
        self.func_depth = FuncLayout(self.right_widget)
        self.func_depth.add(QtWidgets.QLabel(' Depth'))
        self.imageDepth_QDSB = self.func_depth.add(QtWidgets.QDoubleSpinBox())
        self.imageDepth_QDSB.setRange(0.01, 1000000000)
        self.fit_QCombo = self.func_depth.add(QtWidgets.QComboBox())
        self.fit_QCombo.addItems(['Fill', 'Best', 'Horizontal', 'Vertical', 'To Size'])
        self.func_depth._layout.setStretch(1, 1)
        self.func_depth._layout.setStretch(2, 1)

        self.imageDepth_QDSB.valueChanged.connect(
            lambda: self.get_image_plane().depth.set(self.imageDepth_QDSB.value())
            )
        self.fit_QCombo.currentIndexChanged.connect(
            lambda: self.get_image_plane().fit.set(self.fit_QCombo.currentIndex())
            )

        # function set: alpha gain
        self.func_alphaGain = FuncLayout(self.right_widget)
        self.func_alphaGain.add(QtWidgets.QLabel('Alpha Gain'))
        self.imageAlphaGain = self.func_alphaGain.add(QtWidgets.QSlider())
        self.imageAlphaGain.setRange(0, 50)
        self.imageAlphaGain.setSingleStep(1)
        self.imageAlphaGain.setOrientation(QtCore.Qt.Horizontal)
        self.imageAlphaGain.valueChanged.connect(self.set_alpha_gain)

        add_separator(self.right_widget, 10)

        # function set: Set near/far clip plane
        self.func_clipPlane = FuncLayout(self.right_widget)
        self.func_clipPlane.add(QtWidgets.QLabel('Set Clip'))
        self.nearClipPlane_QDSB = self.func_clipPlane.add(QtWidgets.QDoubleSpinBox())
        self.nearClipPlane_QDSB.setRange(0.01, 1000000000)
        self.farClipPlane_QDSB = self.func_clipPlane.add(QtWidgets.QDoubleSpinBox())
        self.farClipPlane_QDSB.setRange(0.01, 1000000000)
        self.farClipPlane_QDSB.setValue(100000)
        self.func_clipPlane._layout.setStretch(1, 1)
        self.func_clipPlane._layout.setStretch(2, 1)

        self.nearClipPlane_QDSB.valueChanged.connect(
            lambda: camera.set_clip_plane(
                self.get_cam().getShape(), self.nearClipPlane_QDSB.value(), self.farClipPlane_QDSB.value()
                )
            )
        self.farClipPlane_QDSB.valueChanged.connect(
            lambda: camera.set_clip_plane(
                self.get_cam().getShape(), self.nearClipPlane_QDSB.value(), self.farClipPlane_QDSB.value()
                )
            )

        # function set: quickly lock/unlock transform attributes of camera
        self.func_lockTransform = FuncLayout(self.right_widget)
        self.lockTransform_QPB = self.func_lockTransform.add(QtWidgets.QPushButton('Lock'))
        self.unlockTransform_QPB = self.func_lockTransform.add(QtWidgets.QPushButton('Unlock'))

        self.lockTransform_QPB.clicked.connect((lambda: camera.lock_cam_tsf(self.get_cam(), 1)))
        self.unlockTransform_QPB.clicked.connect(lambda: transform.unlock_shapes(self.get_cam()))

        # function set: rotate order of cam
        self.func_rotateOrder = FuncLayout(self.right_widget)
        self.camScale = self.func_rotateOrder.add(QtWidgets.QLabel('  1.0  '))
        set_font_size(self.camScale, 14)
        self.rotateOrder_QCombo = self.func_rotateOrder.add(QtWidgets.QComboBox())
        self.bake_cam_QPB = self.func_rotateOrder.add(QtWidgets.QPushButton('Bake to World'))
        set_font_size(self.rotateOrder_QCombo, 14)
        self.rotateOrder_QCombo.addItems(['xyz', 'yzx', 'zxy', 'xzy', 'yxz', 'zyx'])
        self.func_rotateOrder._layout.setStretch(1, 1)
        self.func_rotateOrder._layout.setStretch(2, 1)

        self.rotateOrder_QCombo.currentIndexChanged.connect(self.change_cam_rotateOrder)
        self.bake_cam_QPB.clicked.connect(self.bake_cam)

        add_separator(self.right_widget, 10)

        self.func_bake_scale = FuncLayout(self.right_widget)
        self.reset_scale = self.func_bake_scale.add(QtWidgets.QCheckBox("Reset Scale"))
        self.reset_scale.setChecked(True)
        self.rep_world_bake_btn = self.func_bake_scale.add(QtWidgets.QPushButton("Bake"))
        self.rep_world_bake_btn.clicked.connect(self.bake_cam_world)

        add_separator(self.right_widget, 10)

        # spacer to push all function set upward
        spacerItem = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.right_layout.addItem(spacerItem)

        # Function set: playblast
        self.func_playblast = FuncLayout(self.right_widget)
        self.playblast_qpb = self.func_playblast.add(QtWidgets.QPushButton('Playblast'))
        self.playblastOptions_qpb = self.func_playblast.add(QtWidgets.QPushButton('...'))
        self.func_playblast._layout.setStretch(0, 1)
        self.func_playblast._layout.setStretch(1, 0)

        self.playblast_qpb.clicked.connect(pm.playblast)
        self.playblastOptions_qpb.clicked.connect(pm.runtime.PlayblastOptions)

        # MISC
        self.sc_callback = om2.MEventMessage.addEventCallback(
            "SelectionChanged", Callback(selection_changed_cam_tool, ui=self)
            )
        self.update_imagePlane_sets()
        self.update_cam_sets()

    def change_cam_rotateOrder(self):
        transform.set_rotate_order(self.get_cam(), self.rotateOrder_QCombo.currentText())

    def bake_cam_world(self):
        cam = self.get_cam()
        if not cam:
            util.warning('No active camera', ui=self.statusBar)
            return
        camera.bake_to_world2(
            str(cam),
            reset_scale=self.reset_scale.isChecked()
        )

    @undo_dec
    def bake_cam(self):
        transform.bake_to_world(self.get_cam())

    def enterEvent(self, event):
        """ Update panel show/hide option when mouse enter the UI """
        current_panel = self.update_panel()
        if not current_panel:
            return
        self.vis_gpuCache_QPB.setChecked(
            bool(cmds.modelEditor(current_panel, q=1, queryPluginObjects='gpuCacheDisplayFilter'))
            )
        self.vis_imagePlane_QPB.setChecked(bool(cmds.modelEditor(current_panel, q=1, imagePlane=1)))
        self.vis_wireframeOnShaded_QPB.setChecked(bool(cmds.modelEditor(current_panel, q=1, wireframeOnShaded=1)))
        self.vis_nurbsCurves_QPB.setChecked(bool(cmds.modelEditor(current_panel, q=1, nurbsCurves=1)))
        self.vis_polymeshes_QPB.setChecked(bool(cmds.modelEditor(current_panel, q=1, polymeshes=1)))
        self.vis_cameras_QPB.setChecked(bool(cmds.modelEditor(current_panel, q=1, cameras=1)))
        self.vis_selectionHiliteDisplay_QPB.setChecked(
            bool(cmds.modelEditor(current_panel, q=1, selectionHiliteDisplay=1))
            )
        self.update_cam_sets()
        self.update_imagePlane_sets()

    def block_signal(self, block):
        """ Block UI signal (when updating) """
        for func_layout in self.right_widget.children():
            if isinstance(
                    func_layout, FuncLayout
                    ):  # and not func_layout in [self.func_power_preset, self.func_p_tag_selec_cam]:
                for child in func_layout.children():
                    child.blockSignals(block)

    @undo_dec
    def set_image_name(self, text):
        """ Set path of imagePlane """
        if not camera.set_image_name(self.get_image_plane(), text):
            util.warning('image not exists', ui=self.statusBar)
            self.imageName_QLE.setText('')
            return
        self.imageName_QLE.setText(text)
        pm.mel.eval('ogs -reset')
        # reload_image_sequence(self.get_image_plane())

    def refresh(self):
        """ Refresh button function: clear all listWidget and then add back """
        pm.mel.eval("colorManagementPrefs -edit -cmEnabled 1")
        for listWidget in self.cam_listWidget, self.imagePlane_listWidget:
            for i in range(listWidget.count()):
                listWidget.takeItem(0)
        self.switch_lists(force=self.prior_QPB.isChecked())

    def set_alpha_gain(self):
        ip = self.get_image_plane()
        if ip:
            ip.alphaGain.set(self.imageAlphaGain.value() / 50.)

    def update_cam_sets(self):
        """ update camera attribute on UI by selection """
        self.block_signal(1)
        sl = self.cam_listWidget.selectedItems()
        if not sl:
            self.nearClipPlane_QDSB.setEnabled(0)
            self.farClipPlane_QDSB.setEnabled(0)
            self.rotateOrder_QCombo.setEnabled(0)
            self.block_signal(0)
            return
        src = sl[0].src
        if not src.isValid():
            self.block_signal(0)
            return
        cam = pm.PyNode(main.mobj2(src, 'fullPath'))
        cam_scale = cam.cameraScale.get()
        self.camScale.setText('  {}  '.format(cam_scale))
        if not cam_scale == 1.:
            assign_bg_color(self.camScale, 'red')
        else:
            self.camScale.setStyleSheet('')
        if cam.nearClipPlane.isSettable():
            self.nearClipPlane_QDSB.setValue(cam.nearClipPlane.get())
            self.nearClipPlane_QDSB.setEnabled(1)
        else:
            self.nearClipPlane_QDSB.setEnabled(0)
        if cam.farClipPlane.isSettable():
            self.farClipPlane_QDSB.setValue(cam.farClipPlane.get())
            self.farClipPlane_QDSB.setEnabled(1)
        else:
            self.farClipPlane_QDSB.setEnabled(0)
        cam_tsf = cam.getParent()
        if cam_tsf.rotateOrder.isSettable():
            self.rotateOrder_QCombo.setCurrentIndex(cam_tsf.rotateOrder.get())
            self.rotateOrder_QCombo.setEnabled(1)
        else:
            self.rotateOrder_QCombo.setEnabled(0)
        self.block_signal(0)

    def update_imagePlane_sets(self):
        """ update imagePlane attribute on UI by selection """
        self.block_signal(1)
        sl = self.imagePlane_listWidget.selectedItems()
        if not sl:
            self.colorspace_QCombo.setEnabled(0)
            self.fit_QCombo.setEnabled(0)
            self.display_mode_QCombo.setEnabled(0)
            self.imageDepth_QDSB.setEnabled(0)
            self.imageAlphaGain.setEnabled(0)
            self.imageName_QLE.setEnabled(0)
            self.imageName_QLE.setText('')
            self.setLookThru_QPB.setEnabled(0)
            self.reloadIS_QPB.setEnabled(0)
            self.imageName_QLE.setEnabled(0)
            self.browseImagePath_QPB.setEnabled(0)
            self.block_signal(0)
            return
        src = sl[0].src
        if not src.isValid():
            self.block_signal(0)
            return
        imagePlane = imagePlane_to_pynode(src)[-1]
        self.setLookThru_QPB.setEnabled(1)
        self.fit_QCombo.setEnabled(1)
        self.reloadIS_QPB.setEnabled(1)
        self.imageName_QLE.setEnabled(1)
        self.browseImagePath_QPB.setEnabled(1)
        self.colorspace_QCombo.setEnabled(1)
        self.display_mode_QCombo.setEnabled(1)
        self.imageDepth_QDSB.setEnabled(1)
        self.imageAlphaGain.setEnabled(1)
        self.imageName_QLE.setEnabled(1)
        current_colorpsace = imagePlane.colorSpace.get()
        if current_colorpsace in ['Raw', 'sRGB', 'ACES2065-1']:
            self.colorspace_QCombo.setCurrentIndex({'Raw': 0, 'sRGB': 1, 'ACES2065-1': 2}[imagePlane.colorSpace.get()])
        else:
            util.warning("Colorspace is not one of 'Raw','sRGB','ACES2065-1', the UI wont update", self.statusBar)
        self.fit_QCombo.setCurrentIndex(imagePlane.fit.get())
        self.display_mode_QCombo.setCurrentIndex(
            {'None': 0, 'Outline': 1, 'RGB': 2, 'RGBA': 3, 'Luminance': 4, 'Alpha': 5}[
                imagePlane.displayMode.get(asString=1)]
            )
        self.imageDepth_QDSB.setValue(imagePlane.depth.get())
        self.imageAlphaGain.setValue(imagePlane.alphaGain.get() * 50)
        self.imageName_QLE.setText(imagePlane.imageName.get())
        self.block_signal(0)

    def closeEvent(self, event):
        """ Remove callback on UI Closing """
        try:
            om2.MMessage.removeCallback(self.sc_callback)
        except:
            pass

    @undo_dec
    def browse_image_path(self):
        """ Browse image path for imagePlane """
        usd = pm.internalVar(usd=True)
        usd = '/'.join(usd.split('/')[:4]) + '/scripts'
        line = self.imageName_QLE.text()
        line = line if line else usd
        file_path = pm.fileDialog2(dir=line, dialogStyle=2, caption='Browse Image', fileMode=1, returnFilter=False)
        if file_path:
            file_path = file_path[0]
            self.set_image_name(file_path)

    def select_node(self, listWidget):
        """ Select object when double click on UI listWidgets """
        sl = listWidget.selectedItems()
        if not sl:
            return
        sl = sl[0]
        if listWidget == self.cam_listWidget:
            pm.select(main.handle_tsf(sl.src, 'fullPath'))
        else:
            pm.select(imagePlane_to_pynode(main.mobj2(sl.src, 'mobj'))[-1])
        return sl.src

    def rClick_cam(self, QPos):
        """Wrapper for right click on QListWidget - camera list"""
        self.rClick_go(QPos, self.cam_listWidget)

    def rClick_imagePlane(self, QPos):
        """Wrapper for right click on QListWidget - camera list"""
        self.rClick_go(QPos, self.imagePlane_listWidget)

    def rClick_go(self, QPos, listWidget):
        """ Build popup menu for RMB in listWidgets """
        self.list_menu = QtWidgets.QMenu()
        if listWidget == self.cam_listWidget:
            action_lookThru = self.list_menu.addAction('Look Thru')
            self.connect(action_lookThru, QtCore.SIGNAL('triggered()'), lambda: self.lookThru(listWidget))
        action_rename = self.list_menu.addAction('Rename')
        self.connect(action_rename, QtCore.SIGNAL('triggered()'), lambda: self.rename_item(listWidget))
        action_delete = self.list_menu.addAction('Delete')
        self.connect(action_delete, QtCore.SIGNAL('triggered()'), lambda: self.delete_item(listWidget))
        if listWidget == self.cam_listWidget:
            action_renameMasterCam = self.list_menu.addAction('Rename to masterCam')
            self.connect(
                action_renameMasterCam, QtCore.SIGNAL('triggered()'),
                lambda: self.rename_item(listWidget, n='masterCam')
                )
            action_new = self.list_menu.addAction('New')
            self.connect(action_new, QtCore.SIGNAL('triggered()'), lambda: self.create_new_cam(at_lookAt=True))
        else:
            action_renameMasterCam = self.list_menu.addAction('Rename to imagePlane1')
            self.connect(
                action_renameMasterCam, QtCore.SIGNAL('triggered()'),
                lambda: self.rename_item(listWidget, n='imagePlane1')
                )
            action_new = self.list_menu.addAction('New')
            self.connect(action_new, QtCore.SIGNAL('triggered()'), self.create_new_imageplane)
        parent_pos = listWidget.mapToGlobal(QtCore.QPoint(0, 0))
        self.list_menu.move(parent_pos + QPos)
        self.list_menu.show()

    @undo_dec
    def create_new_imageplane(self):
        """ create new imagePlane for selected(UI) camera """
        cam = self.get_cam()
        if not cam:
            util.warning('No active camera', ui=self.statusBar)
            return
        return pm.imagePlane(camera=cam)

    def create_new_cam(self, at_lookAt=True):
        """ Create new camera """
        panel = self.update_panel()
        new_cam = camera.create_new_cam(panel, at_lookAt=at_lookAt)
        return new_cam

    @undo_dec
    def lookThru(self, list_widget):
        """ lookThru current item in listWidget """
        panel = self.update_panel()
        src = list_widget.currentItem().src
        if not panel:
            util.warning('Haven\'t got an active panel.')
            return
        if not src.isValid():
            return
        fp = main.mobj2(main.get_parent(src.object()), 'fullPath')
        mel.eval('lookThroughModelPanel {} {}'.format(fp, self.update_panel()))

    @undo_dec
    def rename_item(self, list_widget, n=None):
        """ Rename current item in listWidget """
        t = list_widget.currentItem().text()
        result = 'OK'
        if not n:
            result = cmds.promptDialog(
                title='Rename', text=t, message='Enter Name:', button=['OK', 'Cancel'], defaultButton='OK',
                cancelButton='Cancel', dismissString='Cancel'
                )
            n = cmds.promptDialog(query=True, text=True)
        if not n or result == 'Cancel':
            return
        for c, i in enumerate(cmds.ls(n)):
            cmds.rename(i, "{}_{}".format(n, c + 1))
        main.mobj2(main.get_parent(list_widget.currentItem().src.object()), 'fn').setName(n)
        # list_widget.currentItem().setText(n)
        list_widget.update_names()

    @undo_dec
    def delete_item(self, list_widget):
        """ Delete current item in listWidget """
        item = list_widget.currentItem()
        if not item:
            return
        list_widget.selectionModel().clear()
        fp = main.mobj2(main.get_parent(item.src.object()), 'fullPath')
        cmds.delete(fp)
        if not cmds.objExists(fp):
            list_widget.takeItem(list_widget.row(item))
        list_widget.update_names()

    def switch_lists(self, force=None):
        """ Switch the order of two listWidget and update accordingly """
        self.block_signal(1)
        status = self.prior_QPB.isChecked() if force == None else force
        type_list = ['camera', 'imagePlane']
        mType = [om2.MFn.kCamera, om2.MFn.kImagePlane][status]
        lss = main.api_ls('mobj', obj_type=mType)
        widget_list = [self.cam_listWidget, self.imagePlane_listWidget]
        self.prior_QPB.setText(['Camera first', 'imagePlane first'][status])
        scroll_as = self.cam_listWidget.scrollArea, self.imagePlane_listWidget.scrollArea
        self.left_layout.removeWidget(scroll_as[1 - status])
        self.left_layout.addWidget(scroll_as[1 - status])
        self.imagePlane_listWidget.clear()
        self.cam_listWidget.clear()
        remove_skip_cam = []
        for cam in lss:
            sn = main.mobj2(cam, 'shortName')
            if not 'shakeCam' in sn and not 'tweakCam' in sn:
                widget_list[status].add(main.mobj2(cam, 'handle'))
        self.block_signal(0)

    def click_update(self, listWidget):
        list_widgets = self.cam_listWidget, self.imagePlane_listWidget
        index = list_widgets.index(listWidget)
        if index:
            self.update_imagePlane_sets()
        else:
            self.update_cam_sets()
        """ Update UI when click on an item in listWidgets """
        item = listWidget.selectedItems()
        if not item:
            return
        item = item[0]
        if not item.src.isValid():
            listWidget.selectionModel().clear()
            listWidget.takeItem(listWidget.row(item))
            return

        self.update_imagePlane_sets()
        self.update_cam_sets()
        list_widgets = self.cam_listWidget, self.imagePlane_listWidget
        index = list_widgets.index(listWidget)
        get_connected_cmd = [get_connected_imagePlane, get_connected_cam][index]
        if int(self.prior_QPB.isChecked()) == 1 - index:  # pass if is active one is at the bottom
            return
        src_widget = list_widgets[index]
        dst_widget = list_widgets[1 - index]
        dst_widget.clear()
        connected_tsf = get_connected_cmd(item.src)
        if not connected_tsf:
            return
        for i in connected_tsf:
            dst_widget.add(i)
        dst_widget.set_selected(0)
        for list_w in list_widgets:
            list_w.update_names()
        if index:
            self.update_cam_sets()
        else:
            self.update_imagePlane_sets()

    def update_panel(self):
        """ Get current panel, if its a modelPanel, update the self.last_active_panel
            if not, return the self.last_active_panel (use the previous current panel) """
        current_panel = cmds.getPanel(withFocus=1)
        self.last_active_panel = current_panel if 'modelPanel' in current_panel else self.last_active_panel
        return self.last_active_panel

    def get_active_cam(self):
        """ get the camera from the self.last_active_panel """
        panel = self.update_panel()
        cam = cmds.modelPanel(panel, q=1, camera=1)
        cam = pm.PyNode(cam).getParent() if cam else None
        return cam

    def get_cam(self):
        """ get camera PyNode from listWidget """
        cam = None
        if not self.cam_listWidget.count():
            util.warning('You have no cam in cam list.', ui=self.statusBar)
            return None
        sl_items = self.cam_listWidget.selectedItems()
        if sl_items:
            cam = sl_items[0].src
        else:
            if self.cam_listWidget.count() == 1:
                cam = self.cam_listWidget.item(0).src
            else:
                util.warning('You haven\'t select any camera in the list', ui=self.statusBar)
                return None
        cam = pm.PyNode(main.mobj2(cam, 'fullPath')).getParent()
        return cam

    def get_image_plane(self):
        """ get imagePlane PyNode from listWidget """
        imagePlane = None
        if not self.imagePlane_listWidget.count():
            util.warning('You have no imagePlane in list.', ui=self.statusBar)
            return None
        sl_items = self.imagePlane_listWidget.selectedItems()
        if sl_items:
            imagePlane = sl_items[0].src
        else:
            if self.imagePlane_listWidget.count() == 1:
                imagePlane = self.imagePlane_listWidget.item(0).src
            else:
                util.warning('You haven\'t select any camera in the list', ui=self.statusBar)
                return None
        imagePlane = imagePlane_to_pynode(imagePlane)[-1]
        return imagePlane


class ListWidget(QtWidgets.QListWidget):
    def __init__(self, parent):
        super(ListWidget, self).__init__()
        self.scrollArea = QtWidgets.QScrollArea(parent)
        parent.layout().addWidget(self.scrollArea)
        self.scrollArea.setWidgetResizable(True)
        self.scrollWidget = QtWidgets.QWidget()
        self.scrollWidget.setGeometry(QtCore.QRect(0, 0, 274, 308))
        self.girdLayout = QtWidgets.QGridLayout(self.scrollWidget)
        self.setParent(self.scrollWidget)
        set_font_size(self, 14)
        self.girdLayout.addWidget(self, 0, 0, 1, 1)
        self.scrollArea.setWidget(self.scrollWidget)

    def add(self, item):
        """ Shortcut to add QtWidgets"""
        self.addItem(main.handle_tsf(item, 'shortName'))
        p_path = main.handle_tsf(item, 'partialPath')
        last = self.list_items()[2][-1]
        last.setToolTip(p_path)
        try:
            if cmds.camera(p_path, q=1, startupCamera=1):
                last.setForeground(QtGui.QColor('grey'))
        except:
            pass
        last.src = main.mobj2(item, 'handle')
        return last

    def update_names(self):
        """ update item names """
        items = [self.item(i) for i in range(self.count())]
        for c, item in enumerate(items):
            if not item.src.isValid():
                self.takeItem(self.row(item))
            else:
                item.setToolTip(main.handle_tsf(item.src, 'partialPath'))
                item.setText(main.handle_tsf(item.src, 'shortName'))

    def list_items(self):
        """ list different types of item """
        items = [self.item(i) for i in range(self.count())]
        full_path_names, src = [], []
        for item in items:
            if hasattr(item, 'src'):
                src.append(item.src)
                full_path_names.append(main.mobj2(item.src, 'fullPath'))
            else:
                src.append(None)
                full_path_names.append(None)
        return [i.text() for i in items], src, items, full_path_names

    def get_selected(self):
        """ get current selected item, returning different types of data """
        item = self.selectedItems()
        if not item:
            return None
        item = item[0]
        return item.text(), item.src, item

    def set_selected(self, input):
        """ set selected by different types of input should be implemented more """
        if isinstance(input, integer_types):
            self.setCurrentItem(self.item(input))
        elif isinstance(input, string_types):
            names = self.list_items()[0]
            self.setCurrentItem(self.item(names.index(input)))
        elif isinstance(input, QtWidgets.QListWidgetItem):
            self.setCurrentItem(input)
        elif isinstance(input, om2.MObject):
            idx = self.list_items()[3].index(main.mobj2(input, 'fullPath'))
            self.setCurrentItem(self.item(idx))

    def remove(self, input):
        """ remove selected by different types of input should be implemented more """
        if not isinstance(input, integer_types):
            names = [i[0] for i in self.list_items()]
            if isinstance(input, string_types):
                input = names.index(input)
            elif isinstance(input, QtWidgets.QListWidgetItem):
                input = names.index(input.text())
                self.setCurrentItem(input)
        self.takeItem(input)


class FuncLayout(QtWidgets.QWidget):
    def __init__(self, parent):
        super(FuncLayout, self).__init__()
        self._layout = QtWidgets.QHBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._parent_layout = parent.layout()
        self._parent_layout.addWidget(self)

    def add(self, widget):
        widget.setParent(self)
        self._layout.addWidget(widget)
        return widget


def set_font_size(widget, font_size):
    font = QtGui.QFont()
    font.setPointSize(font_size)
    widget.setFont(font)
    return widget


def assign_bg_color(widget, color):
    styleSheet = widget.styleSheet()
    if 'background-color:' in styleSheet:
        splits = styleSheet.split('background-color:')
        splits_end = splits[-1].split(';')[-1]
        styleSheet = '{}background-color: {};{}'.format(splits[0], color, splits_end)
    else:
        styleSheet = 'background-color: {};{}'.format(color, styleSheet)
    widget.setStyleSheet(styleSheet)
    return styleSheet


def add_separator(parent_widget, size):
    line = QtWidgets.QFrame(parent_widget)
    line.setMinimumSize(QtCore.QSize(0, size))
    line.setFrameShape(QtWidgets.QFrame.HLine)
    line.setFrameShadow(QtWidgets.QFrame.Sunken)
    parent_widget.layout().addWidget(line)


def init_window():
    #  dockable
    # if not 'customMixinWindow' in globals():
    #     customMixinWindow = None
    ui = CameramanGUI(gui.get_maya_window())
    ui.setAttribute(QtCore.Qt.WA_DeleteOnClose)
    # dockable
    # ui.show(dockable=True)
    ui.show()
    return ui


def selection_changed_cam_tool(*args, **kwargs):
    """ Callback function to update the UI by Maya selection changed event """
    ui = kwargs.get('ui')
    sel_list = om2.MGlobal.getActiveSelectionList()
    if not sel_list.length():
        return None, None
    last = sel_list.getDependNode(sel_list.length() - 1)
    return_cam = main.get_nodes_tsf(last, om2.MFn.kCamera)
    return_imagePlane = main.get_nodes_tsf(last, om2.MFn.kImagePlane)
    if return_cam:
        update_ui(return_cam, mode='cam', ui=ui)
    if return_imagePlane:
        update_ui(return_imagePlane, mode='imagePlane', ui=ui)
    return return_cam, return_imagePlane


def update_ui(node, mode='cam', ui=None):
    """ update the UI by selection changed callback """
    index = {'cam': 0, 'imagePlane': 1}[mode]
    listWidget = ui.cam_listWidget, ui.imagePlane_listWidget
    updating_listWidget = listWidget[index]
    get_connected_cmd = [get_connected_cam, get_connected_imagePlane][1 - index]
    ui.switch_lists(force=ui.prior_QPB.isChecked())
    _, _, _, full_path = updating_listWidget.list_items()
    item = [updating_listWidget.item(i) for i in range(updating_listWidget.count())]
    fp = main.mobj2(node, 'fullPath')
    if fp in full_path:
        updating_listWidget.set_selected(updating_listWidget.item(full_path.index(fp)))
    else:
        connected = get_connected_cmd(node)
        if connected:
            connected = connected[0]
        connected_fp = main.mobj2(connected, 'fullPath')
        all_fp = listWidget[1 - index].list_items()[3]
        if not connected_fp in all_fp:
            return
        idx = all_fp.index(connected_fp)
        listWidget[1 - index].set_selected(listWidget[1 - index].item(idx))
        idx = updating_listWidget.list_items()[3].index(fp)
        updating_listWidget.set_selected(updating_listWidget.item(idx))


def get_connected_cam(imagePlane):
    """ get camera by given object's message connection (and has to be a camera node)"""
    connected = []
    fn = main.mobj2(imagePlane, 'fn')
    plug = fn.findPlug('message', False)
    for i in plug.connectedTo(0, 1):
        if i.node().hasFn(om2.MFn.kCamera):
            connected.append(i.node())
    return connected


def get_connected_imagePlane(cam):
    """ get imagePlane by given object's imagePlane attribute connection (and has to be a imagePlane node) """
    connected = []
    fn = main.mobj2(cam, 'fn')
    plug = fn.findPlug('imagePlane', False)
    for c in range(plug.numConnectedElements()):
        for connected_plug in plug.connectionByPhysicalIndex(c).connectedTo(1, 0):
            if connected_plug.node().hasFn(om2.MFn.kImagePlane):
                connected.append(connected_plug.node())
    return connected


def imagePlane_to_pynode(imagePlane):
    """ Convert the given imagePlane to pynode, use list index since pymel might get duplicate naming error"""
    imagePlane_parent = None
    imagePlane = main.mobj2(imagePlane, 'fullPath')
    imagePlane_strings = cmds.ls(type='imagePlane', long=1, ap=1)
    if imagePlane in imagePlane_strings:
        index = imagePlane_strings.index(imagePlane)
        imagePlane = pm.ls(type='imagePlane')[index]
    return imagePlane_parent, imagePlane


def show():
    global cameraman_gui
    try:
        cameraman_gui.close()
    except:
        pass
    cameraman_gui = init_window()
    cameraman_gui.switch_lists(force=0)
    return cameraman_gui


if __name__ == '__main__':
    show()

"""
cmds.addAttr('camShape', longName='notes', dt="string")
cmds.setAttr('camShape.notes', 'aaac',type='string')
"""