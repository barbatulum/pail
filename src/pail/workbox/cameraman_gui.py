from PySide2 import QtCore, QtGui, QtWidgets
# from . import cameraman_function_sets
import cameraman_function_sets


class QSingleton(type(QtCore.QObject), type):
    # https://github.com/davidlatwe/sweet/blob/main/src/sweet/gui/models.py#L22
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(QSingleton, cls).__call__(
                *args, **kwargs
            )
        return cls._instances[cls]


class CameramanGUI(QtWidgets.QMainWindow, metaclass=QSingleton):
    def __init__(self, parent):
        QtWidgets.QMainWindow.__init__(self, parent)
        self.central_widget = QtWidgets.QWidget(self)
        self.setCentralWidget(self.central_widget)
        self.central_vertical_layout = QtWidgets.QVBoxLayout(
            self.central_widget
            )

        # top_layout
        self.top_layout = QtWidgets.QVBoxLayout()
        self.central_vertical_layout.addLayout(self.top_layout)

        cameraman_function_sets.populate_viewport_options(
            parent_widget=self.central_widget, parent_layout=self.top_layout
        )

        # mid/btm layouts
        self.mid_layout = QtWidgets.QHBoxLayout()
        self.central_vertical_layout.addLayout(self.mid_layout)

        self.btm_layout = QtWidgets.QHBoxLayout()
        self.central_vertical_layout.addLayout(self.btm_layout)

        # Mid layout -> left/right panel layouts
        self.list_ui_qvl = QtWidgets.QVBoxLayout()
        self.mid_layout.addLayout(self.list_ui_qvl)
        self.right_panel_layout = QtWidgets.QVBoxLayout()
        self.mid_layout.addLayout(self.right_panel_layout)
        self.mid_layout.setStretch(0, 1)
        self.mid_layout.setStretch(1, 2)

        # Mid layout -> left panel -> list UIs
        self.list_ui_commands_qhl = QtWidgets.QHBoxLayout()
        self.refresh_qpb = QtWidgets.QPushButton(
            "Refresh", self.central_widget
            )
        self.qlist_order_pqb = QtWidgets.QPushButton(
            "Camera first", self.central_widget
            )
        self.list_ui_commands_qhl.addWidget(self.refresh_qpb)
        self.list_ui_commands_qhl.addWidget(self.qlist_order_pqb)
        self.list_ui_qvl.addLayout(self.list_ui_commands_qhl)

        self.camera_list_qlistw = QtWidgets.QListWidget(self.central_widget)
        self.list_ui_qvl.addWidget(self.camera_list_qlistw)
        self.image_plane_list_qlistw = QtWidgets.QListWidget(
            self.central_widget
            )
        self.list_ui_qvl.addWidget(self.image_plane_list_qlistw)

        # Mid layout -> right panel -> function widget
        self.functions_tabs = QtWidgets.QTabWidget(self.central_widget)
        self.right_panel_layout.addWidget(self.functions_tabs)

        self.main_tab_qw = QtWidgets.QWidget()
        self.functions_tabs.addTab(self.main_tab_qw, "Main")
        self.main_tab_qvl = QtWidgets.QVBoxLayout(self.main_tab_qw)

        self.config_tab_qw = QtWidgets.QWidget()
        self.functions_tabs.addTab(self.config_tab_qw, "Config")
        self.config_tab_qvl = QtWidgets.QVBoxLayout(self.config_tab_qw)

        self.functions_tabs.setTabPosition(QtWidgets.QTabWidget.North)
        self.functions_tabs.setTabShape(QtWidgets.QTabWidget.Rounded)
        self.functions_tabs.setDocumentMode(True)
        self.functions_tabs.setMovable(True)
        self.functions_tabs.setCurrentIndex(0)

        cameraman_function_sets.populate_image_plane_attributes(
            parent_widget=self.main_tab_qw, parent_layout=self.main_tab_qvl
        )
        cameraman_function_sets.populate_image_plane_commands(
            parent_widget=self.main_tab_qw, parent_layout=self.main_tab_qvl
        )
        cameraman_function_sets.populate_bake(
            parent_widget=self.main_tab_qw, parent_layout=self.main_tab_qvl
        )

        self.make_pusher(self.main_tab_qvl)

        cameraman_function_sets.populate_playblast(
            parent_widget=self.central_widget,
            parent_layout=self.right_panel_layout,
        )

        cameraman_function_sets.populate_name_preset(
            parent_widget=self.config_tab_qw,
            parent_layout=self.config_tab_qvl
        )
        self.make_pusher(self.config_tab_qvl)

    @staticmethod
    def make_pusher(self, layout):
        pusher = QtWidgets.QSpacerItem(
            20,
            40,
            QtWidgets.QSizePolicy.Minimum,
            QtWidgets.QSizePolicy.Expanding,
        )
        layout.addItem(pusher)