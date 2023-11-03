# -*- coding: utf-8 -*-
import os
import maya.mel as mm
import maya.cmds as mc
import pymel.all as pm
import maya.api.OpenMaya as om2
import maya.OpenMayaUI as omui
import shiboken2
from PySide2 import QtCore, QtGui, QtWidgets
# dockable
# from maya.app.general.mayaMixin import MayaQWidgetDockableMixin
# import power_preset
# reload(power_preset)
# import p_tag_selec_cam
# reload(p_tag_selec_cam)


class Callback(object):
    def __init__(self, func, *args, **kwargs):
        self.func = func
        self.args = args
        self.kwargs = kwargs
    def __call__(self, *args):
        return self.func(*self.args, **self.kwargs)


def undo_dec(func):
    '''A decorator that will make commands undoable in maya'''

    def _deco(*args, **kwargs):
        mc.undoInfo(openChunk=True)
        funcReturn = None
        try:
            funcReturn = func(*args, **kwargs)
        except:
            print sys.exc_info()[1]
        finally:
            mc.undoInfo(closeChunk=True)
            return funcReturn
    return _deco


# The main UI class
# dockable
# class CamTool_UI(MayaQWidgetDockableMixin,QtWidgets.QMainWindow):
class CamTool_UI(QtWidgets.QMainWindow):
    def __init__(self, parent):
        QtWidgets.QMainWindow.__init__(self, parent)
        # dockable
        # self.setObjectName('CamTool')
        pm.mel.eval("colorManagementPrefs -edit -cmEnabled 1")
        self.callback = None
        self.setWindowTitle('CamTool')
        self.resize(675, 760)
        self.last_active_panel = None
        self.update_panel()

        self.statusBar = QtWidgets.QStatusBar(self)
        set_font_size(self.statusBar,13)
        self.setStatusBar(self.statusBar)

        # arrange layout
        self.win_central_widget = QtWidgets.QWidget(self)
        self.setCentralWidget(self.win_central_widget)
        self.win_gridLayout = QtWidgets.QGridLayout(self.win_central_widget) # top most window layout
        self.panel_vis_layoutWidget = QtWidgets.QWidget(self.win_central_widget)
        self.panel_vis_layout = QtWidgets.QHBoxLayout(self.panel_vis_layoutWidget)
        self.sep_layoutWidget = QtWidgets.QWidget(self.win_central_widget)
        self.sep_layout = QtWidgets.QHBoxLayout(self.sep_layoutWidget)
        self.main_layoutWidget = QtWidgets.QWidget(self.win_central_widget) # layout to contain left and right column
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
        ## camera/imagePlane list related function
        self.func_list = FuncLayout(self.left_widget)
        self.refresh_cam_QPB = self.func_list.add(QtWidgets.QPushButton('Refresh'))
        self.prior_QPB = self.func_list.add(QtWidgets.QPushButton('Camera first'))
        self.prior_QPB.setCheckable(1)

        self.refresh_cam_QPB.clicked.connect(self.refresh)
        self.prior_QPB.clicked.connect(self.switch_lists)


        ## camera scroll area
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
        self.cam_listWidget.itemSelectionChanged.connect(Callback(self.click_update,self.cam_listWidget))
        self.imagePlane_listWidget.itemSelectionChanged.connect(Callback(self.click_update,self.imagePlane_listWidget))
        # double click - select
        self.cam_listWidget.doubleClicked.connect(lambda: self.select_node(self.cam_listWidget))
        self.imagePlane_listWidget.doubleClicked.connect(lambda: self.select_node(self.imagePlane_listWidget))

        ######################################

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

        self.vis_wireframeOnShaded_QPB.clicked.connect(lambda: set_show_hide(self.update_panel(), 'wireframeOnShaded', self.vis_wireframeOnShaded_QPB.isChecked()))
        self.vis_imagePlane_QPB.clicked.connect(lambda: set_show_hide(self.update_panel(), 'imagePlane', self.vis_imagePlane_QPB.isChecked()))
        self.vis_gpuCache_QPB.clicked.connect(lambda: set_show_hide(self.update_panel(), 'gpuCache', self.vis_gpuCache_QPB.isChecked()))
        self.vis_selectionHiliteDisplay_QPB.clicked.connect(lambda: set_show_hide(self.update_panel(), 'selectionHiliteDisplay',self.vis_selectionHiliteDisplay_QPB.isChecked()))
        self.vis_nurbsCurves_QPB.clicked.connect(lambda: set_show_hide(self.update_panel(), 'nurbsCurves', self.vis_nurbsCurves_QPB.isChecked()))
        self.vis_polymeshes_QPB.clicked.connect(lambda: set_show_hide(self.update_panel(), 'polymeshes', self.vis_polymeshes_QPB.isChecked()))
        self.vis_cameras_QPB.clicked.connect(lambda: set_show_hide(self.update_panel(), 'camera', self.vis_cameras_QPB.isChecked()))
        self.vis_locators_QPB.clicked.connect(lambda: set_show_hide(self.update_panel(), 'locators', self.vis_locators_QPB.isChecked()))

        #######################################
        add_separator(self.sep_layoutWidget,10)
        #######################################

        # right column
        ## function set: color space of image plane
        self.func_colorspace = FuncLayout(self.right_widget)
        self.func_colorspace.add(QtWidgets.QLabel('Color Space'))
        self.colorspace_QCombo = self.func_colorspace.add(QtWidgets.QComboBox())
        self.colorspace_QCombo.addItems(['Raw', 'sRGB', 'ACES2065-1'])

        self.colorspace_QCombo.currentIndexChanged.connect(lambda: set_colorspace(self.get_image_plane(), self.colorspace_QCombo.currentText()))

        ## function set: color space mode of image plane
        self.func_colorspace_mode = FuncLayout(self.right_widget)
        self.func_colorspace_mode.add(QtWidgets.QLabel('Display Mode'))
        self.display_mode_QCombo = self.func_colorspace_mode.add(QtWidgets.QComboBox())
        self.display_mode_QCombo.addItems(['None','Outline','RGB','RGBA','Luminance','Alpha'])

        self.display_mode_QCombo.currentIndexChanged.connect(lambda: set_colorspace_display_mode(self.get_image_plane(), self.display_mode_QCombo.currentIndex()))

        ## function set: Toggle look thru to force image plane to refresh
        self.func_setLookThru = FuncLayout(self.right_widget)
        self.setLookThru_QPB = self.func_setLookThru.add(QtWidgets.QPushButton('Set Look Thru'))

        self.setLookThru_QPB.clicked.connect(lambda: look_thru(self.get_image_plane()))

        ## function set: reload image sequence by disconnecting frame expression
        self.func_reloadIS = FuncLayout(self.right_widget)
        self.reloadIS_QPB = self.func_reloadIS.add(QtWidgets.QPushButton('Reload image sequence'))

        self.reloadIS_QPB.clicked.connect(lambda: reload_image_sequence(self.get_image_plane()))

        ## function set: image path
        self.func_imageName = FuncLayout(self.right_widget)
        self.func_imageName.add(QtWidgets.QLabel('Image Name'))
        self.imageName_QLE = self.func_imageName.add(QtWidgets.QLineEdit())
        self.browseImagePath_QPB = self.func_imageName.add(QtWidgets.QPushButton('...'))

        self.imageName_QLE.editingFinished.connect(lambda: self.set_image_name(self.imageName_QLE.text()))
        self.browseImagePath_QPB.clicked.connect(self.browse_image_path)

        ## function set: image plane's depth and fit
        self.func_depth = FuncLayout(self.right_widget)
        self.func_depth.add(QtWidgets.QLabel(' Depth'))
        self.imageDepth_QDSB = self.func_depth.add(QtWidgets.QDoubleSpinBox())
        self.imageDepth_QDSB.setRange(0.01, 1000000000)
        self.fit_QCombo = self.func_depth.add(QtWidgets.QComboBox())
        self.fit_QCombo.addItems(['Fill', 'Best','Horizontal','Vertical','To Size'])
        self.func_depth._layout.setStretch(1, 1)
        self.func_depth._layout.setStretch(2, 1)

        self.imageDepth_QDSB.valueChanged.connect(lambda: self.get_image_plane().depth.set(self.imageDepth_QDSB.value()))
        self.fit_QCombo.currentIndexChanged.connect(lambda: self.get_image_plane().fit.set(self.fit_QCombo.currentIndex()))

        ## function set: alpha gain
        self.func_alphaGain = FuncLayout(self.right_widget)
        self.func_alphaGain.add(QtWidgets.QLabel('Alpha Gain'))
        self.imageAlphaGain = self.func_alphaGain.add(QtWidgets.QSlider())
        self.imageAlphaGain.setRange(0,50)
        self.imageAlphaGain.setSingleStep(1)
        self.imageAlphaGain.setOrientation(QtCore.Qt.Horizontal)
        self.imageAlphaGain.valueChanged.connect(self.set_alpha_gain)

        ###################################
        add_separator(self.right_widget,10)
        ###################################

        ## function set: Set near/far clip plane
        self.func_clipPlane = FuncLayout(self.right_widget)
        self.func_clipPlane.add(QtWidgets.QLabel('Set Clip'))
        self.nearClipPlane_QDSB = self.func_clipPlane.add(QtWidgets.QDoubleSpinBox())
        self.nearClipPlane_QDSB.setRange(0.01, 1000000000)
        self.farClipPlane_QDSB = self.func_clipPlane.add(QtWidgets.QDoubleSpinBox())
        self.farClipPlane_QDSB.setRange(0.01, 1000000000)
        self.farClipPlane_QDSB.setValue(100000)
        self.func_clipPlane._layout.setStretch(1, 1)
        self.func_clipPlane._layout.setStretch(2, 1)

        self.nearClipPlane_QDSB.valueChanged.connect(lambda: set_clip_plane(self.get_cam().getShape(), self.nearClipPlane_QDSB.value(),self.farClipPlane_QDSB.value()))
        self.farClipPlane_QDSB.valueChanged.connect(lambda: set_clip_plane(self.get_cam().getShape(), self.nearClipPlane_QDSB.value(),self.farClipPlane_QDSB.value()))

        ## function set: quickly lock/unlock transform attributes of camera
        self.func_lockTransform = FuncLayout(self.right_widget)
        self.lockTransform_QPB = self.func_lockTransform.add(QtWidgets.QPushButton('Lock'))
        self.unlockTransform_QPB = self.func_lockTransform.add(QtWidgets.QPushButton('Unlock'))

        self.lockTransform_QPB.clicked.connect((lambda: lock_cam_tsf(self.get_cam(),1)))
        self.unlockTransform_QPB.clicked.connect(lambda: unlock_cam_shapes(self.get_cam()))

        ## function set: rotate order of cam
        self.func_rotateOrder = FuncLayout(self.right_widget)
        self.camScale = self.func_rotateOrder.add(QtWidgets.QLabel('  1.0  '))
        set_font_size(self.camScale,14)
        self.rotateOrder_QCombo = self.func_rotateOrder.add(QtWidgets.QComboBox())
        self.bake_cam_QPB = self.func_rotateOrder.add(QtWidgets.QPushButton('Bake to World'))
        set_font_size(self.rotateOrder_QCombo,14)
        self.rotateOrder_QCombo.addItems(['xyz', 'yzx','zxy','xzy','yxz','zyx'])
        self.func_rotateOrder._layout.setStretch(1, 1)
        self.func_rotateOrder._layout.setStretch(2, 1)

        self.rotateOrder_QCombo.currentIndexChanged.connect(self.change_cam_rotateOrder)
        self.bake_cam_QPB.clicked.connect(self.bake_cam)

        ###################################
        add_separator(self.right_widget,10)
        ###################################
        ###################################
        # TODO : for selected cam
        ## Batch function set: quickly rename the only left camera and image plane to masterCam and imagePlane1
        ## function set: power preset
        # self.func_power_preset_auto = FuncLayout(self.right_widget)
        # self.power_preset_auto_QPB = self.func_power_preset_auto.add(QtWidgets.QPushButton('Batch: Power Preset Auto'))
        # self.power_preset_single_QPB = self.func_power_preset_auto.add(QtWidgets.QPushButton('Batch: Power Preset Single'))
        # assign_bg_color(self.power_preset_auto_QPB, 'DarkSlateGrey')
        # self.func_power_preset_auto._layout.setStretch(0, 2)
        # self.func_power_preset_auto._layout.setStretch(1, 3)
        #
        # self.power_preset_auto_QPB.clicked.connect(power_preset.main)
        # # self.buttonName.clicked.connect(lambda: functionName(self.get_image_plane()))
        # self.power_preset_single_QPB.clicked.connect(lambda: power_preset.power_preset_single(self.get_cam()))
        ###################################

        # ## function set: power preset
        # # quickly image plane to imagePlane1 and reset 'masterCam' to standard setting
        # self.func_power_preset = FuncLayout(self.right_widget)
        # self.power_preset_QPB = self.func_power_preset.add(QtWidgets.QPushButton('Batch: Power Preset'))
        # assign_bg_color(self.power_preset_QPB, 'DarkSlateGrey')
        # self.power_preset_QPB.clicked.connect(self.start_power_preset)

        # ## Batch function set: set all camera to general camera preset
        # self.func_p_tag_selec_cam = FuncLayout(self.right_widget)
        # self.p_tag_selec_cam_QPB = self.func_p_tag_selec_cam.add(QtWidgets.QPushButton('Vendor Ingest: Power Camera Tag (AF pipe only)'))
        # assign_bg_color(self.p_tag_selec_cam_QPB,'DarkSlateGrey')
        # self.p_tag_selec_cam_QPB.clicked.connect(p_tag_selec_cam.main)

        ## Batch function set: set all camera to general camera preset
        # self.func_batch_cameraPreset = FuncLayout(self.right_widget)
        # self.batch_cameraPreset_QPB = self.func_batch_cameraPreset.add(QtWidgets.QPushButton('Batch: Camera Preset'))
        # assign_bg_color(self.batch_cameraPreset_QPB,'DarkSlateGrey')
        # self.batch_cameraPreset_QPB.setEnabled(0)

        ## spacer to push all function set upward ##
        spacerItem = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.right_layout.addItem(spacerItem)
        ############################################

        ## Function set: playblast
        self.func_playblast = FuncLayout(self.right_widget)
        self.playblast_qpb = self.func_playblast.add(QtWidgets.QPushButton('Playblast'))
        self.playblastOptions_qpb = self.func_playblast.add(QtWidgets.QPushButton('...'))
        self.func_playblast._layout.setStretch(0, 1)
        self.func_playblast._layout.setStretch(1, 0)

        self.playblast_qpb.clicked.connect(pm.playblast)
        self.playblastOptions_qpb.clicked.connect(pm.runtime.PlayblastOptions)

        ################### MISC ###################
        self.sc_callback = om2.MEventMessage.addEventCallback("SelectionChanged", Callback(selection_changed_cam_tool,ui=self))
        self.update_imagePlane_sets()
        self.update_cam_sets()

    def start_power_preset(self):
        power_preset.main()

    def change_cam_rotateOrder(self):
        set_rotate_order(self.get_cam(),self.rotateOrder_QCombo.currentText())

    @undo_dec
    def bake_cam(self):
        bake_to_world(self.get_cam())

    def enterEvent(self, event):
        """ Update panel show/hide option when mouse enter the UI """
        current_panel = self.update_panel()
        if not current_panel:
            return
        self.vis_gpuCache_QPB.setChecked(bool(mc.modelEditor(current_panel, q=1, queryPluginObjects='gpuCacheDisplayFilter')))
        self.vis_imagePlane_QPB.setChecked(bool(mc.modelEditor(current_panel, q=1,imagePlane=1)))
        self.vis_wireframeOnShaded_QPB.setChecked(bool(mc.modelEditor(current_panel, q=1,wireframeOnShaded=1)))
        self.vis_nurbsCurves_QPB.setChecked(bool(mc.modelEditor(current_panel, q=1,nurbsCurves=1)))
        self.vis_polymeshes_QPB.setChecked(bool(mc.modelEditor(current_panel, q=1,polymeshes=1)))
        self.vis_cameras_QPB.setChecked(bool(mc.modelEditor(current_panel, q=1,cameras=1)))
        self.vis_selectionHiliteDisplay_QPB.setChecked(bool(mc.modelEditor(current_panel, q=1,selectionHiliteDisplay=1)))
        self.update_cam_sets()
        self.update_imagePlane_sets()

    def block_signal(self,block):
        """ Block UI signal (when updating) """
        for func_layout in self.right_widget.children():
            if isinstance(func_layout, FuncLayout):# and not func_layout in [self.func_power_preset, self.func_p_tag_selec_cam]:
                for child in func_layout.children():
                    child.blockSignals(block)

    @undo_dec
    def set_image_name(self, text):
        """ Set path of imagePlane """
        if not set_image_name(self.get_image_plane(), text):
            warning('image not exists', ui=self.statusBar)
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
            ip.alphaGain.set(self.imageAlphaGain.value()/50.)

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
        cam = pm.PyNode(mobj2(src,'fullPath'))
        cam_scale = cam.cameraScale.get()
        self.camScale.setText('  {}  '.format(cam_scale))
        if not cam_scale == 1.:
            assign_bg_color(self.camScale,'red')
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
        if current_colorpsace in ['Raw','sRGB','ACES2065-1']:
            self.colorspace_QCombo.setCurrentIndex({'Raw':0, 'sRGB':1,'ACES2065-1':2}[imagePlane.colorSpace.get()])
        else:
            warning("Colorspace is not one of 'Raw','sRGB','ACES2065-1', the UI wont update",self.statusBar)
        self.fit_QCombo.setCurrentIndex(imagePlane.fit.get())
        self.display_mode_QCombo.setCurrentIndex({'None':0,'Outline': 1, 'RGB':2, 'RGBA':3,'Luminance':4,'Alpha':5}[imagePlane.displayMode.get(asString=1)])
        self.imageDepth_QDSB.setValue(imagePlane.depth.get())
        self.imageAlphaGain.setValue(imagePlane.alphaGain.get()*50)
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
            pm.select(handle_tsf(sl.src,'fullPath'))
        else:
            pm.select(imagePlane_to_pynode(mobj2(sl.src,'mobj'))[-1])
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
            self.connect(action_renameMasterCam, QtCore.SIGNAL('triggered()'), lambda: self.rename_item(listWidget, n='masterCam'))
            action_new = self.list_menu.addAction('New')
            self.connect(action_new, QtCore.SIGNAL('triggered()'), lambda: self.create_new_cam(at_lookAt=True))
        else:
            action_renameMasterCam = self.list_menu.addAction('Rename to imagePlane1')
            self.connect(action_renameMasterCam, QtCore.SIGNAL('triggered()'), lambda: self.rename_item(listWidget, n='imagePlane1'))
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
            warning('No active camera',ui=self.statusBar)
            return
        return pm.imagePlane(camera=cam)

    def create_new_cam(self,at_lookAt=True):
        """ Create new camera """
        panel = self.update_panel()
        cam = None
        if not panel:
            at_lookAt = False
        else:
            current_cam = mc.modelPanel(panel, q=1, cam=1)
            if not current_cam:
                at_lookAt = False
        new_cam = pm.createNode('camera').getParent()
        if at_lookAt:
            pm.xform(new_cam,ws=1,t=pm.xform(current_cam, q=1,ws=1,t=1))
            pm.xform(new_cam,ws=1,ro=pm.xform(current_cam, q=1,ws=1,ro=1))
            pm.move(new_cam,(0, 0, pm.PyNode(current_cam).centerOfInterest.get()*-1),r=1,os=1,wd=1)
            [i.set(0) for i in new_cam.r.children()]
        return new_cam

    @undo_dec
    def lookThru(self,list_widget):
        """ lookThru current item in listWidget """
        panel = self.update_panel()
        src = list_widget.currentItem().src
        if not panel:
            warning('Haven\'t got an active panel.')
            return
        if not src.isValid():
            return
        fp = mobj2(get_parent(src.object()), 'fullPath')
        mm.eval('lookThroughModelPanel {} {}'.format(fp, self.update_panel()))

    @undo_dec
    def rename_item(self,list_widget,n=None):
        """ Rename current item in listWidget """
        t= list_widget.currentItem().text()
        result = 'OK'
        if not n:
            result = mc.promptDialog(title='Rename',text=t, message='Enter Name:',button=['OK', 'Cancel'], defaultButton='OK', cancelButton='Cancel', dismissString='Cancel')
            n = mc.promptDialog(query=True, text=True)
        if not n or result == 'Cancel':
            return
        for c, i in enumerate(mc.ls(n)):
            mc.rename(i,"{}_{}".format(n,c+1))
        mobj2(get_parent(list_widget.currentItem().src.object()), 'fn').setName(n)
        # list_widget.currentItem().setText(n)
        list_widget.update_names()

    @undo_dec
    def delete_item(self,list_widget):
        """ Delete current item in listWidget """
        item = list_widget.currentItem()
        if not item:
            return
        list_widget.selectionModel().clear()
        fp = mobj2(get_parent(item.src.object()), 'fullPath')
        mc.delete(fp)
        if not mc.objExists(fp):
            list_widget.takeItem(list_widget.row(item))
        list_widget.update_names()

    def switch_lists(self, force=None):
        """ Switch the order of two listWidget and update accordingly """
        self.block_signal(1)
        status = self.prior_QPB.isChecked() if force == None else force
        type_list = ['camera','imagePlane']
        mType = [om2.MFn.kCamera,om2.MFn.kImagePlane][status]
        lss = api_ls('mobj',obj_type=mType)
        widget_list = [self.cam_listWidget, self.imagePlane_listWidget]
        self.prior_QPB.setText(['Camera first','imagePlane first'][status])
        scroll_as = self.cam_listWidget.scrollArea, self.imagePlane_listWidget.scrollArea
        self.left_layout.removeWidget(scroll_as[1-status])
        self.left_layout.addWidget(scroll_as[1-status])
        self.imagePlane_listWidget.clear()
        self.cam_listWidget.clear()
        remove_skip_cam = []
        for cam in lss:
            sn = mobj2(cam,'shortName')
            if not 'shakeCam' in sn and not 'tweakCam' in sn:
                widget_list[status].add(mobj2(cam,'handle'))
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
        if int(self.prior_QPB.isChecked()) == 1 - index: # pass if is active one is at the bottom
            return
        src_widget = list_widgets[index]
        dst_widget = list_widgets[1-index]
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
        current_panel = mc.getPanel(withFocus=1)
        self.last_active_panel = current_panel if 'modelPanel' in current_panel else self.last_active_panel
        return self.last_active_panel

    def get_active_cam(self):
        """ get the camera from the self.last_active_panel """
        panel = self.update_panel()
        cam = mc.modelPanel(panel, q=1, camera=1)
        cam = pm.PyNode(cam).getParent() if cam else None
        return cam

    def get_cam(self):
        """ get camera PyNode from listWidget """
        cam = None
        if not self.cam_listWidget.count():
            warning('You have no cam in cam list.',ui=self.statusBar)
            return None
        sl_items = self.cam_listWidget.selectedItems()
        if sl_items:
            cam = sl_items[0].src
        else:
            if self.cam_listWidget.count() == 1:
                cam = self.cam_listWidget.item(0).src
            else:
                warning('You haven\'t select any camera in the list',ui=self.statusBar)
                return None
        cam = pm.PyNode(mobj2(cam,'fullPath')).getParent()
        return cam

    def get_image_plane(self):
        """ get imagePlane PyNode from listWidget """
        imagePlane = None
        if not self.imagePlane_listWidget.count():
            warning('You have no imagePlane in list.',ui=self.statusBar)
            return None
        sl_items = self.imagePlane_listWidget.selectedItems()
        if sl_items:
            imagePlane = sl_items[0].src
        else:
            if self.imagePlane_listWidget.count() == 1:
                imagePlane = self.imagePlane_listWidget.item(0).src
            else:
                warning('You haven\'t select any camera in the list',ui=self.statusBar)
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
        set_font_size(self,14)
        self.girdLayout.addWidget(self, 0, 0, 1, 1)
        self.scrollArea.setWidget(self.scrollWidget)

    def add(self, item):
        """ Shortcut to add QtWidgets"""
        self.addItem(handle_tsf(item, 'shortName'))
        p_path = handle_tsf(item, 'partialPath')
        last = self.list_items()[2][-1]
        last.setToolTip(p_path)
        try:
            if mc.camera(p_path,q=1,startupCamera=1):
                # last.setBackground(QtGui.QColor(0, 1., .5, 1.));
                last.setForeground(QtGui.QColor('grey'));
        except:
            pass
        last.src = mobj2(item, 'handle')
        return last

    def update_names(self):
        """ update item names """
        items = [self.item(i) for i in range(self.count())]
        for c, item in enumerate(items):
            if not item.src.isValid():
                self.takeItem(self.row(item))
            else:
                item.setToolTip(handle_tsf(item.src,'partialPath'))
                item.setText(handle_tsf(item.src, 'shortName'))

    def list_items(self):
        """ list different types of item """
        items = [self.item(i) for i in range(self.count())]
        full_path_names, src = [],[]
        for item in items:
            if hasattr(item,'src'):
                src.append(item.src)
                full_path_names.append(mobj2(item.src,'fullPath'))
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
        if isinstance(input, int):
            self.setCurrentItem(self.item(input))
        elif isinstance(input, (unicode, str)):
            names = self.list_items()[0]
            self.setCurrentItem(self.item(names.index(input)))
        elif isinstance(input, QtWidgets.QListWidgetItem):
            self.setCurrentItem(input)
        elif isinstance(input, om2.MObject):
            idx = self.list_items()[3].index(mobj2(input,'fullPath'))
            self.setCurrentItem(self.item(idx))

    def remove(self, input):
        """ remove selected by different types of input should be implemented more """
        if not isinstance(input, int):
            names = [i[0] for i in self.list_items()]
            if isinstance(input, (unicode, str)):
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

    def add(self,widget):
        widget.setParent(self)
        self._layout.addWidget(widget)
        return widget


def set_font_size(widget,font_size):
    font = QtGui.QFont()
    font.setPointSize(font_size)
    widget.setFont(font)
    return widget


def get_maya_ui_long_name(QtWidget):
    return omui.MQtUtil.fullName(long(shiboken2.getCppPointer(QtWidget)[0]))


def warning(msg, ui=None, lasts=3000):
    mc.inViewMessage(smg='<hl>{}</hl>'.format(msg), fade=1, pos='topCenter')
    mc.warning(msg)
    if ui:
        ui.showMessage(msg, lasts)
    return msg


def get_maya_window():
    ptr = omui.MQtUtil.mainWindow()
    if ptr is not None:
        return shiboken2.wrapInstance(long(ptr), QtWidgets.QMainWindow)


def assign_bg_color(widget, color):
    styleSheet = widget.styleSheet()
    if 'background-color:' in styleSheet:
        splits = styleSheet.split('background-color:')
        splits_end = splits[-1].split(';')[-1]
        styleSheet = '{}background-color: {};{}'.format(splits[0], color, splits_end)
    else:
        styleSheet = 'background-color: {};{}'.format(color,styleSheet)
    widget.setStyleSheet(styleSheet)
    return styleSheet


def add_separator(parent_widget,size):
    line = QtWidgets.QFrame(parent_widget)
    line.setMinimumSize(QtCore.QSize(0, size))
    line.setFrameShape(QtWidgets.QFrame.HLine)
    line.setFrameShadow(QtWidgets.QFrame.Sunken)
    parent_widget.layout().addWidget(line)


def init_window():
    #  dockable
    # if not 'customMixinWindow' in globals():
    #     customMixinWindow = None
    ui = CamTool_UI(get_maya_window())
    ui.setAttribute(QtCore.Qt.WA_DeleteOnClose)
    # dockable
    # ui.show(dockable=True)
    ui.show()
    return ui


####################
# Generic Function #
####################


def mobj2(obj,return_type):
    def get(obj,return_type):
        if return_type == 'shortName':
            return om2.MFnDependencyNode(obj).name()
        elif return_type == 'fullPath':
            return om2.MDagPath.getAPathTo(obj).fullPathName()
        elif return_type == 'fn':
            return om2.MFnDependencyNode(obj)
        elif return_type == 'partialPath':
            return om2.MDagPath.getAPathTo(obj).partialPathName()
        elif return_type == 'handle':
            return om2.MObjectHandle(obj)
        elif return_type == 'dagPath':
            return om2.MDagPath.getAPathTo(obj)
        elif return_type == 'dagFn':
            return om2.MFnDagNode(obj)
        elif return_type == 'mobj':
            return obj
    def convert(obj):
        if isinstance(obj, om2.MDagPath):
            return obj.node()
        if isinstance(obj, om2.MObjectHandle):
            return obj.object()
        elif isinstance(obj, om2.MObject):
            return obj
        elif isinstance(obj, (str,unicode)):
            return get_depend_node(obj)
        elif isinstance(obj, (list,tuple)):
            return [convert(o) for o in obj]
        elif isinstance(obj, om2.MObjectArray):
            return [convert(obj[c]) for c in range(len(obj))]
        else:
            raise TypeError(obj)
    obj = convert(obj)
    if isinstance(obj, list):
        return [get(o,return_type) for o in obj]
    elif isinstance(obj, om2.MObject):
        return get(obj, return_type)
    else:
        raise TypeError(obj)


def get_depend_node(name_str):
    node = []
    if isinstance(name_str, list):
        for name in name_str:
            selection = om2.MSelectionList()
            selection.add(name)
        node = [selection.getDependNode(c) for c in range(len(name_str))]
    else:
        selection = om2.MSelectionList()
        selection.add(name_str)
        node = selection.getDependNode(0)
    return node


def selection_changed_cam_tool(*args, **kwargs):
    """ Callback function to update the UI by Maya selection changed event """
    ui = kwargs.get('ui')
    sel_list = om2.MGlobal.getActiveSelectionList()
    if not sel_list.length():
        return None, None
    last = sel_list.getDependNode(sel_list.length()-1)
    return_cam = get_nodes_tsf(last,om2.MFn.kCamera)
    return_imagePlane = get_nodes_tsf(last,om2.MFn.kImagePlane)
    if return_cam:
        update_ui(return_cam, mode='cam', ui=ui)
    if return_imagePlane:
        update_ui(return_imagePlane, mode='imagePlane',ui=ui)
    return return_cam, return_imagePlane


def update_ui(node, mode='cam',ui=None):
    """ update the UI by selection changed callback """
    index = {'cam':0,'imagePlane':1}[mode]
    listWidget = ui.cam_listWidget, ui.imagePlane_listWidget
    updating_listWidget = listWidget[index]
    get_connected_cmd = [get_connected_cam, get_connected_imagePlane][1-index]
    ui.switch_lists(force=ui.prior_QPB.isChecked())
    _, _, _, full_path = updating_listWidget.list_items()
    item = [updating_listWidget.item(i) for i in range(updating_listWidget.count())]
    fp = mobj2(node,'fullPath')
    if fp in full_path:
        updating_listWidget.set_selected(updating_listWidget.item(full_path.index(fp)))
    else:
        connected = get_connected_cmd(node)
        if connected:
            connected = connected[0]
        connected_fp = mobj2(connected,'fullPath')
        all_fp = listWidget[1-index].list_items()[3]
        if not connected_fp in all_fp:
            return
        idx = all_fp.index(connected_fp)
        listWidget[1-index].set_selected(listWidget[1-index].item(idx))
        idx = updating_listWidget.list_items()[3].index(fp)
        updating_listWidget.set_selected(updating_listWidget.item(idx))


def get_connected_cam(imagePlane):
    """ get camera by given object's message connection (and has to be a camera node)"""
    connected = []
    fn = mobj2(imagePlane,'fn')
    plug = fn.findPlug('message',False)
    for i in plug.connectedTo(0,1):
        if i.node().hasFn(om2.MFn.kCamera):
            connected.append(i.node())
    return connected


def get_connected_imagePlane(cam):
    """ get imagePlane by given object's imagePlane attribute connection (and has to be a imagePlane node) """
    connected = []
    fn = mobj2(cam,'fn')
    plug = fn.findPlug('imagePlane',False)
    for c in range(plug.numConnectedElements()):
        for connected_plug in plug.connectionByPhysicalIndex(c).connectedTo(1,0):
            if connected_plug.node().hasFn(om2.MFn.kImagePlane):
                connected.append(connected_plug.node())
    return connected


def get_selection():
    """ API get selection """
    sel_list = om2.MGlobal.getActiveSelectionList()
    return [(sel_list.getDependNode(c)) for c in range(sel_list.length())]


def get_shape(mObj):
    """ get the shape of given object, if its already a shape, return itself"""
    shapes = []
    if mObj.hasFn(om2.MFn.kTransform):
        for c in range(mobj2(mObj, 'dagPath').numberOfShapesDirectlyBelow()):
            shapes.append(mobj2(mObj, 'dagPath').extendToShape(c).node())
    elif mObj.hasFn(om2.MFn.kShape):
        shapes.append(mObj)
    return shapes


def get_parent(mObj):
    """ as title """
    return mobj2(mObj,'dagFn').parent(0)


def api_ls(return_type, obj_type=None):
    """ ls object by API"""
    dagIterator = om2.MItDependencyNodes(obj_type)
    result = []
    while (not dagIterator.isDone()):
        current = dagIterator.thisNode()
        result.append(current)
        dagIterator.next()
    return [mobj2(i,return_type) for i in result]


def imagePlane_to_pynode(imagePlane):
    """ Convert the given imagePlane to pynode, use list index since pymel might get duplicate naming error"""
    imagePlane_parent = None
    imagePlane = mobj2(imagePlane,'fullPath')
    imagePlane_strings = mc.ls(type='imagePlane',long=1,ap=1)
    if imagePlane in imagePlane_strings:
        index = imagePlane_strings.index(imagePlane)
        imagePlane = pm.ls(type='imagePlane')[index]
    return imagePlane_parent, imagePlane


def handle_tsf(handle, nodeType):
    return mobj2(get_parent(mobj2(handle,'mobj')),nodeType)


def get_nodes_tsf(obj,returnType):
    """ Return the shape node, even if you select its tranform parent"""
    returnV = None
    if not obj.hasFn(om2.MFn.kDagNode):
        return
    if obj.hasFn(returnType):
        returnV = obj
    else:
        slDagPath = mobj2(obj, 'dagPath')
        if not slDagPath.numberOfShapesDirectlyBelow():
            return None
        shape = slDagPath.extendToShape(0)
        if shape.hasFn(returnType):
            returnV = shape
    return returnV


##################
# Maya Functions #
##################


def look_thru(imagePlane):
    imagePlane.displayOnlyIfCurrent.set(0)
    imagePlane.displayOnlyIfCurrent.set(1)


def set_colorspace(imagePlane, colorspace):
    pm.mel.eval("colorManagementPrefs -edit -cmEnabled 1")
    imagePlane.colorSpace.set(colorspace)


def set_colorspace_display_mode(imagePlane, mode):
    if not isinstance(mode, int):
        mode = {'None':0,'RGB':2,'RGBA':3}[mode]
    imagePlane.displayMode.set(mode)


@undo_dec
def reload_image_sequence(imagePlane, ui=None):
    # if not imagePlane.frameExtension.listConnections():
    # if not imagePlane.useFrameExtension.get():
    #     warning('Image plane:{} is not a image sequence'.format(imagePlane),ui)
    #     return
    # mc.setAttr(imagePlane.name()+'.useFrameExtension', 0)
    imagePlane.frameExtension.unlock()
    pm.delete(imagePlane.frameExtension.listConnections())
    mc.setAttr(imagePlane.name()+'.useFrameExtension', 1)
    # pm.mel.eval(imagePlane.name())
    pm.mel.eval('ogs -reset')
    evaluate_expression()


def set_image_name(imagePlane, text):
    if os.path.isfile(text):
        imagePlane.useFrameExtension.set(0)
        imagePlane.imageName.set(text)
        imagePlane.useFrameExtension.set(1)
        return True
    elif text == '':
        imagePlane.imageName.set(text)
        imagePlane.useFrameExtension.set(0)
        return True
    else:
        return False
    # reload_image_sequence(imagePlane)


@undo_dec
def set_clip_plane(cam, near,far):
    cam.nearClipPlane.set(near)
    cam.farClipPlane.set(far)
    return cam, near,far


@undo_dec
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


def set_rotate_order(transform, ro):
    if isinstance(ro,(float,int)):
        ro = int(ro)
    elif isinstance(ro,(str,unicode)):
        ro = dict(xyz=0, yzx=1, zxy=2,xzy=3,yxz=4,zyx=5)[ro]
    transform.ro.set(ro)


def set_show_hide(panel, obj_type, state):
    if not panel:
        warning('You have to ACTIVE a panel')
        return
    if obj_type =='nurbsCurves':
        mc.modelEditor(panel, e=1,nurbsCurves=state)
    if obj_type =='polymeshes':
        mc.modelEditor(panel, e=1,polymeshes=state)
    if obj_type =='locators':
        mc.modelEditor(panel, e=1,locators=state)
    if obj_type =='camera':
        mc.modelEditor(panel, e=1,cameras=state)
    if obj_type =='selectionHiliteDisplay':
        mc.modelEditor(panel, e=1,selectionHiliteDisplay=state)
    if obj_type =='wireframeOnShaded':
        mc.modelEditor(panel, e=1,wireframeOnShaded=state)
    if obj_type =='imagePlane':
        mc.modelEditor(panel, e=1,imagePlane=state)
    if obj_type =='gpuCache':
        mc.modelEditor(panel, e=1, pluginObjects=('gpuCacheDisplayFilter', state))


def unlock_all(obj):
    for attr in obj.listAttr(locked=1):
        try:
            attr.unlock()
        except:
            warning('{} is unlockable'.format(attr))


@undo_dec
def bake_to_world(transform,mode='keyRange'):
    all_vec,all_rVec = [],[]
    temp_loc = pm.spaceLocator()
    cst = pm.parentConstraint(transform, temp_loc,mo=0)
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
        pm.setKeyframe(transform, t=c, at='tx', v=all_vec[c-int(f_start)][0])
        pm.setKeyframe(transform, t=c, at='ty', v=all_vec[c-int(f_start)][1])
        pm.setKeyframe(transform, t=c, at='tz', v=all_vec[c-int(f_start)][2])
        pm.setKeyframe(transform, t=c, at='rx', v=all_rVec[c-int(f_start)][0])
        pm.setKeyframe(transform, t=c, at='ry', v=all_rVec[c-int(f_start)][1])
        pm.setKeyframe(transform, t=c, at='rz', v=all_rVec[c-int(f_start)][2])

def evaluate_expression():
    [pm.dgeval(i) for i in pm.ls(type='expression')]


@undo_dec
def unlock_cam_shapes(cam_tsf):
    unlock_all(cam_tsf)
    for shape in cam_tsf.getShapes():
        unlock_all(shape)


def main():
    global camtool_ui
    try:
        camtool_ui.close()
    except:
        pass
    # dockable
    # try: mc.workspaceControl('CamToolWorkspaceControl',cl=1)
    # except: pass
    # try: mc.deleteUI('CamToolWorkspaceControl', control=True)
    # except: pass
    camtool_ui = init_window()
    camtool_ui.switch_lists(force=0)
    return camtool_ui


if __name__ == '__main__':
    main()