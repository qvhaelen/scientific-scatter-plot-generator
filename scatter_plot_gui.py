import sys
import os
import json
import matplotlib.pyplot as plt
import random
from PyQt6.QtCore import Qt, QSize, QThread, pyqtSignal
from PyQt6.QtGui import QIcon, QPixmap, QTextCursor
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QTabWidget, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QPushButton, QProgressBar, QSpinBox, QDoubleSpinBox, QLineEdit, QCheckBox,
    QComboBox, QGroupBox, QListWidget, QListWidgetItem, QFileDialog, QMessageBox, QSplitter,
    QDialog, QDialogButtonBox, QFormLayout, QScrollArea, QFrame, QTextEdit
)

# Import the updated scatter generator code
from core import ScatterGeneratorSettings, ScatterGenerator

# Create a stream that redirects console output to a QTextEdit
class OutputStream:
    def __init__(self, text_widget):
        self.text_widget = text_widget
        
    def write(self, text):
        cursor = self.text_widget.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        cursor.insertText(text)
        self.text_widget.setTextCursor(cursor)
        self.text_widget.ensureCursorVisible()
        
    def flush(self):
        pass

class SettingsTab(QWidget):
    """Base class for settings tabs with common functionality"""
    def __init__(self, settings):
        super().__init__()
        self.settings = settings
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)
        
    def add_section(self, title):
        """Add a section header to the layout"""
        section_label = QLabel(f"<b>{title}</b>")
        section_label.setStyleSheet("font-size: 14px; margin-top: 15px; margin-bottom: 5px;")
        self.layout.addWidget(section_label)
        
    def add_setting(self, label, widget):
        """Add a setting with label and widget"""
        hbox = QHBoxLayout()
        hbox.addWidget(QLabel(label))
        hbox.addStretch()
        hbox.addWidget(widget)
        self.layout.addLayout(hbox)
        
    def add_row(self, widgets):
        """Add a row of widgets"""
        hbox = QHBoxLayout()
        for widget in widgets:
            hbox.addWidget(widget)
        self.layout.addLayout(hbox)
        
    def add_group(self, title, layout):
        """Add a group box with layout"""
        group = QGroupBox(title)
        group.setLayout(layout)
        self.layout.addWidget(group)

class GeneralSettingsTab(SettingsTab):
    def __init__(self, settings):
        super().__init__(settings)
        self.init_ui()
        
    def init_ui(self):
        self.add_section("Output Configuration")
        
        # Number of images
        self.num_images_spin = QSpinBox()
        self.num_images_spin.setRange(1, 1000)
        self.num_images_spin.setValue(self.settings.num_images)
        self.num_images_spin.valueChanged.connect(
            lambda v: setattr(self.settings, 'num_images', v))
        self.add_setting("Number of images:", self.num_images_spin)
        
        # Data series range
        hbox = QHBoxLayout()
        self.min_series_spin = QSpinBox()
        self.min_series_spin.setRange(1, 20)
        self.min_series_spin.setValue(self.settings.min_number_data_series)
        self.min_series_spin.valueChanged.connect(
            lambda v: setattr(self.settings, 'min_number_data_series', v))
        
        self.max_series_spin = QSpinBox()
        self.max_series_spin.setRange(1, 20)
        self.max_series_spin.setValue(self.settings.max_number_data_series)
        self.max_series_spin.valueChanged.connect(
            lambda v: setattr(self.settings, 'max_number_data_series', v))
        
        hbox.addWidget(QLabel("Minimum number of data series:"))
        hbox.addWidget(self.min_series_spin)
        hbox.addWidget(QLabel("Maximum number of data series:"))
        hbox.addWidget(self.max_series_spin)
        hbox.addStretch()
        self.layout.addLayout(hbox)
        
        # Output format
        self.format_combo = QComboBox()
        self.format_combo.addItems(['png', 'jpg', 'svg', 'pdf'])
        self.format_combo.setCurrentText(self.settings.output_format)
        self.format_combo.currentTextChanged.connect(
            lambda t: setattr(self.settings, 'output_format', t))
        self.add_setting("Output format of the generated scatter plots:", self.format_combo)
        
        # Output directory
        output_layout = QHBoxLayout()
        self.output_dir_edit = QLineEdit(self.settings.output_dir)
        self.output_dir_edit.textChanged.connect(
            lambda t: setattr(self.settings, 'output_dir', t))
        
        browse_btn = QPushButton("Browse...")
        browse_btn.clicked.connect(self.browse_output_dir)
        
        output_layout.addWidget(self.output_dir_edit)
        output_layout.addWidget(browse_btn)
        self.layout.addLayout(output_layout)
        
        # NEW: Vintage Effects and Customization section
        self.add_section("Vintage Effects and Customization")
        
        # Customize size resolution
        self.size_res_cb = QCheckBox("Customize size resolution")
        self.size_res_cb.setChecked(self.settings.customized_size_resolution)
        self.size_res_cb.stateChanged.connect(
            lambda s: setattr(self.settings, 'customized_size_resolution', 
                             s == Qt.CheckState.Checked.value))
        self.layout.addWidget(self.size_res_cb)
        
        # Vintage effect
        self.vintage_cb = QCheckBox("Add vintage effects to images")
        self.vintage_cb.setChecked(self.settings.vintage_bw_image)
        self.vintage_cb.stateChanged.connect(
            lambda s: setattr(self.settings, 'vintage_bw_image', 
                             s == Qt.CheckState.Checked.value))
        self.vintage_cb.stateChanged.connect(self.toggle_vintage_options)
        self.layout.addWidget(self.vintage_cb)
        
        # Vintage intensity
        intensity_layout = QHBoxLayout()
        self.intensity_label = QLabel("Vintage intensity (0.0-1.0):")
        self.intensity_spin = QDoubleSpinBox()
        self.intensity_spin.setRange(0.0, 1.0)
        self.intensity_spin.setSingleStep(0.1)
        self.intensity_spin.setValue(self.settings.vintage_intensity)
        self.intensity_spin.valueChanged.connect(
            lambda v: setattr(self.settings, 'vintage_intensity', v))
        intensity_layout.addWidget(self.intensity_label)
        intensity_layout.addWidget(self.intensity_spin)
        intensity_layout.addStretch()
        self.layout.addLayout(intensity_layout)
        
        # Texture file
        texture_layout = QHBoxLayout()
        self.texture_label = QLabel("Path to the texture file:")
        self.texture_edit = QLineEdit(self.settings.texture_file)
        self.texture_edit.textChanged.connect(
            lambda t: setattr(self.settings, 'texture_file', t))
        self.texture_browse_btn = QPushButton("Browse...")
        self.texture_browse_btn.clicked.connect(self.browse_texture_file)
        texture_layout.addWidget(self.texture_label)
        texture_layout.addWidget(self.texture_edit)
        texture_layout.addWidget(self.texture_browse_btn)
        self.layout.addLayout(texture_layout)
        
        # Initially set the vintage options enabled state
        self.toggle_vintage_options(self.settings.vintage_bw_image)
        
        # Add stretch to push content to top
        self.layout.addStretch()
        
    def browse_output_dir(self):
        """Open directory dialog for output path"""
        dir_path = QFileDialog.getExistingDirectory(
            self, "Select Output Directory", self.settings.output_dir)
        if dir_path:
            self.output_dir_edit.setText(dir_path)
            
    def browse_texture_file(self):
        """Open file dialog for texture file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Texture File", 
            os.path.dirname(self.settings.texture_file) if self.settings.texture_file else "",
            "Image Files (*.png *.jpg *.jpeg *.bmp)"
        )
        if file_path:
            self.texture_edit.setText(file_path)
            
    def toggle_vintage_options(self, state):
        """Enable/disable vintage options based on checkbox state"""
        enabled = state == Qt.CheckState.Checked.value
        self.intensity_label.setEnabled(enabled)
        self.intensity_spin.setEnabled(enabled)
        self.texture_label.setEnabled(enabled)
        self.texture_edit.setEnabled(enabled)
        self.texture_browse_btn.setEnabled(enabled)

class DataPointsSettingsTab(SettingsTab):
    def __init__(self, settings):
        super().__init__(settings)
        self.init_ui()
        
    def init_ui(self):
        # Markers selection
        self.add_section("Marker Selection for the Data Points")
        self.marker_list = QListWidget()
        self.marker_list.setSelectionMode(QListWidget.SelectionMode.MultiSelection)
        for marker in ['o', '^', 's', 'd', 'p', '*', '+', 'x', 'v', '<', '>']:
            item = QListWidgetItem(marker)
            self.marker_list.addItem(item)
            if marker in self.settings.markers:
                item.setSelected(True)
        self.marker_list.itemSelectionChanged.connect(self.update_markers)
        self.layout.addWidget(self.marker_list)
        
        # Points range
        hbox = QHBoxLayout()
        self.min_points_spin = QSpinBox()
        self.min_points_spin.setRange(1, 100)
        self.min_points_spin.setValue(self.settings.min_points)
        self.min_points_spin.valueChanged.connect(
            lambda v: setattr(self.settings, 'min_points', v))
        
        self.max_points_spin = QSpinBox()
        self.max_points_spin.setRange(1, 100)
        self.max_points_spin.setValue(self.settings.max_points)
        self.max_points_spin.valueChanged.connect(
            lambda v: setattr(self.settings, 'max_points', v))
        
        hbox.addWidget(QLabel("Number of data points per series:"))
        hbox.addWidget(QLabel("Minimum:"))
        hbox.addWidget(self.min_points_spin)
        hbox.addWidget(QLabel("Maximum:"))
        hbox.addWidget(self.max_points_spin)
        hbox.addStretch()
        self.layout.addLayout(hbox)
        
        # Error bars
        self.add_section("Setting and Options for the Error Bars")
        
        self.error_bars_cb = QCheckBox("Enable error bars")
        self.error_bars_cb.setChecked(self.settings.add_error_bars)
        self.error_bars_cb.stateChanged.connect(
            lambda s: setattr(self.settings, 'add_error_bars', s == Qt.CheckState.Checked.value))
        self.layout.addWidget(self.error_bars_cb)
        
        error_layout = QHBoxLayout()
        self.error_min_spin = QDoubleSpinBox()
        self.error_min_spin.setRange(0.1, 100)
        self.error_min_spin.setValue(self.settings.error_min)
        self.error_min_spin.valueChanged.connect(
            lambda v: setattr(self.settings, 'error_min', v))
        
        self.error_max_spin = QDoubleSpinBox()
        self.error_max_spin.setRange(0.1, 100)
        self.error_max_spin.setValue(self.settings.error_max)
        self.error_max_spin.valueChanged.connect(
            lambda v: setattr(self.settings, 'error_max', v))
        
        error_layout.addWidget(QLabel("Error range:"))
        error_layout.addWidget(QLabel("Min:"))
        error_layout.addWidget(self.error_min_spin)
        error_layout.addWidget(QLabel("Max:"))
        error_layout.addWidget(self.error_max_spin)
        error_layout.addStretch()
        self.layout.addLayout(error_layout)
        
        self.symmetric_cb = QCheckBox("Symmetric error bars")
        self.symmetric_cb.setChecked(self.settings.symmetric_bar)
        self.symmetric_cb.stateChanged.connect(
            lambda s: setattr(self.settings, 'symmetric_bar', s == Qt.CheckState.Checked.value))
        self.layout.addWidget(self.symmetric_cb)
        
        # Noise distribution
        self.add_section("Selection of the Noise Distribution Function")
        self.noise_list = QListWidget()
        self.noise_list.setSelectionMode(QListWidget.SelectionMode.MultiSelection)
        for noise in ['normal', 'uniform', 'triangular']:
            item = QListWidgetItem(noise)
            self.noise_list.addItem(item)
            if noise in self.settings.noise_distribution_choice:
                item.setSelected(True)
        self.noise_list.itemSelectionChanged.connect(self.update_noise)
        self.layout.addWidget(self.noise_list)
        
        # Color mode
        self.add_section("Color Settings for Data points")
        self.color_mode_combo = QComboBox()
        self.color_mode_combo.addItems(self.settings.black_color_selection)
        self.color_mode_combo.setCurrentText('color_only')
        self.color_mode_combo.currentTextChanged.connect(
            lambda t: setattr(self.settings, 'black_color_selection', [t]))
        self.add_setting("Color mode:", self.color_mode_combo)
        
        # Add stretch to push content to top
        self.layout.addStretch()
        
    def update_markers(self):
        """Update selected markers in settings"""
        selected = [item.text() for item in self.marker_list.selectedItems()]
        self.settings.markers = selected
        
    def update_noise(self):
        """Update selected noise distributions in settings"""
        selected = [item.text() for item in self.noise_list.selectedItems()]
        self.settings.noise_distribution_choice = selected

class AxisGridSettingsTab(SettingsTab):
    def __init__(self, settings):
        super().__init__(settings)
        self.init_ui()
        
    def init_ui(self):
        # Axis ranges
        self.add_section("Axis and Scale Configuration")
        
        x_layout = QHBoxLayout()
        self.x_min_spin = QDoubleSpinBox()
        self.x_min_spin.setRange(-1000, 1000)
        self.x_min_spin.setValue(self.settings.x_min)
        self.x_min_spin.valueChanged.connect(
            lambda v: setattr(self.settings, 'x_min', v))
        
        self.x_max_spin = QDoubleSpinBox()
        self.x_max_spin.setRange(-1000, 1000)
        self.x_max_spin.setValue(self.settings.x_max)
        self.x_max_spin.valueChanged.connect(
            lambda v: setattr(self.settings, 'x_max', v))
        
        x_layout.addWidget(QLabel("X-axis:"))
        x_layout.addWidget(QLabel("Min:"))
        x_layout.addWidget(self.x_min_spin)
        x_layout.addWidget(QLabel("Max:"))
        x_layout.addWidget(self.x_max_spin)
        x_layout.addStretch()
        self.layout.addLayout(x_layout)
        
        y_layout = QHBoxLayout()
        self.y_min_spin = QDoubleSpinBox()
        self.y_min_spin.setRange(0.01, 1000)
        self.y_min_spin.setValue(self.settings.y_min)
        self.y_min_spin.valueChanged.connect(
            lambda v: setattr(self.settings, 'y_min', v))
        
        self.y_max_spin = QDoubleSpinBox()
        self.y_max_spin.setRange(0.01, 1000)
        self.y_max_spin.setValue(self.settings.y_max)
        self.y_max_spin.valueChanged.connect(
            lambda v: setattr(self.settings, 'y_max', v))
        
        y_layout.addWidget(QLabel("Y-axis:"))
        y_layout.addWidget(QLabel("Min:"))
        y_layout.addWidget(self.y_min_spin)
        y_layout.addWidget(QLabel("Max:"))
        y_layout.addWidget(self.y_max_spin)
        y_layout.addStretch()
        self.layout.addLayout(y_layout)
        
        # NEW: Allow semilog scale option
        self.semilog_cb = QCheckBox("Allow for semilog scales?")
        self.semilog_cb.setChecked(self.settings.authorize_semilog)
        self.semilog_cb.stateChanged.connect(
            lambda s: setattr(self.settings, 'authorize_semilog', 
                             s == Qt.CheckState.Checked.value))
        self.layout.addWidget(self.semilog_cb)
        
        # Font and color
        self.add_section("Font and Color")
        
        self.font_size_spin = QSpinBox()
        self.font_size_spin.setRange(6, 36)
        self.font_size_spin.setValue(self.settings.base_font_size)
        self.font_size_spin.valueChanged.connect(
            lambda v: setattr(self.settings, 'base_font_size', v))
        self.add_setting("Base font size:", self.font_size_spin)
        
        self.colormap_combo = QComboBox()
        self.colormap_combo.addItems(['viridis', 'plasma', 'inferno', 'magma', 'cividis', 
                                    'Pastel1', 'Pastel2', 'Paired', 'Accent', 'Dark2', 
                                    'Set1', 'Set2', 'Set3', 'tab10', 'tab20', 'tab20b', 'tab20c'])
        self.colormap_combo.setCurrentText(self.settings.color_map)
        self.colormap_combo.currentTextChanged.connect(
            lambda t: setattr(self.settings, 'color_map', t))
        self.add_setting("Color map:", self.colormap_combo)
        
        # Grid configuration
        self.add_section("Grid Configuration")
        
        self.grid_combo = QComboBox()
        self.grid_combo.addItems(self.settings.grid_customization)
        self.grid_combo.setCurrentText('standard_grid')
        self.grid_combo.currentTextChanged.connect(
            lambda t: setattr(self.settings, 'grid_customization', [t]))
        self.add_setting("Grid display:", self.grid_combo)
        
        self.grid_style_combo = QComboBox()
        self.grid_style_combo.addItems(self.settings.grid_style_options)
        self.grid_style_combo.setCurrentText('both')
        self.grid_style_combo.currentTextChanged.connect(
            lambda t: setattr(self.settings, 'grid_style_options', [t]))
        self.add_setting("Grid style:", self.grid_style_combo)
        
        # FIX 2: Change grid line style to multi-select list
        self.add_setting("Grid line style:", QLabel("Select one or more line styles"))
        self.grid_line_list = QListWidget()
        self.grid_line_list.setSelectionMode(QListWidget.SelectionMode.MultiSelection)
        for style in ['-', '--', ':', '-.']:
            item = QListWidgetItem(style)
            self.grid_line_list.addItem(item)
            if style in self.settings.grid_linestyle_options:
                item.setSelected(True)
        self.grid_line_list.itemSelectionChanged.connect(self.update_grid_line_styles)
        self.layout.addWidget(self.grid_line_list)
        
        self.minor_ticks_cb = QCheckBox("Enable minor ticks")
        self.minor_ticks_cb.setChecked(self.settings.add_minor_tick)
        self.minor_ticks_cb.stateChanged.connect(
            lambda s: setattr(self.settings, 'add_minor_tick', s == Qt.CheckState.Checked.value))
        self.layout.addWidget(self.minor_ticks_cb)
        
        # Label positioning
        self.add_section("Label Positioning")
        
        self.y_rotation_cb = QCheckBox("Rotate Y-axis label")
        self.y_rotation_cb.setChecked(self.settings.y_label_rotation)
        self.y_rotation_cb.stateChanged.connect(
            lambda s: setattr(self.settings, 'y_label_rotation', s == Qt.CheckState.Checked.value))
        self.layout.addWidget(self.y_rotation_cb)
        
        self.custom_pos_cb = QCheckBox("Custom label positioning")
        self.custom_pos_cb.setChecked(self.settings.label_positioning)
        self.custom_pos_cb.stateChanged.connect(
            lambda s: setattr(self.settings, 'label_positioning', s == Qt.CheckState.Checked.value))
        self.layout.addWidget(self.custom_pos_cb)
        
        # Add stretch to push content to top
        self.layout.addStretch()
        
    def update_grid_line_styles(self):
        """Update selected grid line styles in settings"""
        selected = [item.text() for item in self.grid_line_list.selectedItems()]
        self.settings.grid_linestyle_options = selected

class DataGenerationSettingsTab(SettingsTab):
    def __init__(self, settings):
        super().__init__(settings)
        self.init_ui()
        
    def init_ui(self):
        # Mathematical curve
        self.add_section("Generation of Random Data Points")
        
        self.math_curve_cb = QCheckBox("Avoid overlap of the ramdomly generated points")
        self.math_curve_cb.setChecked(self.settings.mathematical_curve)
        self.math_curve_cb.stateChanged.connect(
            lambda s: setattr(self.settings, 'mathematical_curve', s == Qt.CheckState.Checked.value))
        self.layout.addWidget(self.math_curve_cb)
        
        self.tolerance_spin = QDoubleSpinBox()
        self.tolerance_spin.setRange(0.1, 10)
        self.tolerance_spin.setValue(self.settings.coordinate_tolerance)
        self.tolerance_spin.valueChanged.connect(
            lambda v: setattr(self.settings, 'coordinate_tolerance', v))
        self.add_setting("Coordinate tolerance:", self.tolerance_spin)
        
        # Time series patterns
        self.add_section("Generation of Data Points following Predefined Time Series Patterns")
        self.time_series_cb = QCheckBox("Generate time series patterns")
        self.time_series_cb.setChecked(self.settings.generate_time_series_patterns)
        # FIX 1: Properly connect checkbox to setting
        self.time_series_cb.stateChanged.connect(
            lambda s: setattr(self.settings, 'generate_time_series_patterns', s == Qt.CheckState.Checked.value))
        self.time_series_cb.stateChanged.connect(self.toggle_time_series)
        self.layout.addWidget(self.time_series_cb)
        
        # NEW: Display trend lines checkbox
        self.display_trend_cb = QCheckBox("Display Trend Lines")
        self.display_trend_cb.setChecked(self.settings.represent_trend_type_selection)
        self.display_trend_cb.stateChanged.connect(
            lambda s: setattr(self.settings, 'represent_trend_type_selection', s == Qt.CheckState.Checked.value))
        self.display_trend_cb.stateChanged.connect(self.toggle_trend_display)
        self.display_trend_cb.setEnabled(self.settings.generate_time_series_patterns)
        self.layout.addWidget(self.display_trend_cb)
        
        # Trend types
        trend_group = QGroupBox("Trend Types")
        trend_layout = QVBoxLayout()
        self.trend_list = QListWidget()
        self.trend_list.setSelectionMode(QListWidget.SelectionMode.MultiSelection)
        for trend in self.settings.trend_type_selection:
            item = QListWidgetItem(trend)
            self.trend_list.addItem(item)
            item.setSelected(True)
        self.trend_list.itemSelectionChanged.connect(self.update_trends)
        trend_layout.addWidget(self.trend_list)
        trend_group.setLayout(trend_layout)
        self.layout.addWidget(trend_group)
        
        # Trend line style
        line_group = QGroupBox("Trend Line Styles")
        line_layout = QVBoxLayout()
        self.line_list = QListWidget()
        self.line_list.setSelectionMode(QListWidget.SelectionMode.MultiSelection)
        for style in self.settings.customize_trend_type_selection:
            item = QListWidgetItem(style)
            self.line_list.addItem(item)
            item.setSelected(True)
        self.line_list.itemSelectionChanged.connect(self.update_line_styles)
        line_layout.addWidget(self.line_list)
        line_group.setLayout(line_layout)
        self.layout.addWidget(line_group)
        
        # PK Profile Parameters
        self.pk_group = QGroupBox("PK Profile Parameters")
        self.pk_group.setEnabled(False)  # Disabled by default
        pk_layout = QFormLayout()
        
        # Peak position range
        self.pk_peak_min_spin = QDoubleSpinBox()
        self.pk_peak_min_spin.setRange(0.1, 0.9)
        self.pk_peak_min_spin.setValue(self.settings.pk_peak_pos_range[0])
        self.pk_peak_min_spin.valueChanged.connect(self.update_pk_range)
        
        self.pk_peak_max_spin = QDoubleSpinBox()
        self.pk_peak_max_spin.setRange(0.1, 0.9)
        self.pk_peak_max_spin.setValue(self.settings.pk_peak_pos_range[1])
        self.pk_peak_max_spin.valueChanged.connect(self.update_pk_range)
        pk_layout.addRow("Peak position range:", self.create_min_max_widget(
            self.pk_peak_min_spin, self.pk_peak_max_spin))
        
        # Peak value range
        self.pk_value_min_spin = QDoubleSpinBox()
        self.pk_value_min_spin.setRange(0.1, 0.9)
        self.pk_value_min_spin.setValue(self.settings.pk_peak_value_range[0])
        self.pk_value_min_spin.valueChanged.connect(self.update_pk_range)
        
        self.pk_value_max_spin = QDoubleSpinBox()
        self.pk_value_max_spin.setRange(0.1, 0.9)
        self.pk_value_max_spin.setValue(self.settings.pk_peak_value_range[1])
        self.pk_value_max_spin.valueChanged.connect(self.update_pk_range)
        pk_layout.addRow("Peak value range:", self.create_min_max_widget(
            self.pk_value_min_spin, self.pk_value_max_spin))
        
        # Growth rate range
        self.growth_min_spin = QDoubleSpinBox()
        self.growth_min_spin.setRange(0.01, 1.0)
        self.growth_min_spin.setValue(self.settings.pk_growth_rate_range[0])
        self.growth_min_spin.valueChanged.connect(self.update_pk_range)
        
        self.growth_max_spin = QDoubleSpinBox()
        self.growth_max_spin.setRange(0.01, 1.0)
        self.growth_max_spin.setValue(self.settings.pk_growth_rate_range[1])
        self.growth_max_spin.valueChanged.connect(self.update_pk_range)
        pk_layout.addRow("Growth rate range:", self.create_min_max_widget(
            self.growth_min_spin, self.growth_max_spin))
        
        # Decay rate range
        self.decay_min_spin = QDoubleSpinBox()
        self.decay_min_spin.setRange(0.01, 1.0)
        self.decay_min_spin.setValue(self.settings.pk_decay_rate_range[0])
        self.decay_min_spin.valueChanged.connect(self.update_pk_range)
        
        self.decay_max_spin = QDoubleSpinBox()
        self.decay_max_spin.setRange(0.01, 1.0)
        self.decay_max_spin.setValue(self.settings.pk_decay_rate_range[1])
        self.decay_max_spin.valueChanged.connect(self.update_pk_range)
        pk_layout.addRow("Decay rate range:", self.create_min_max_widget(
            self.decay_min_spin, self.decay_max_spin))
        
        # Steady state range
        self.steady_min_spin = QDoubleSpinBox()
        self.steady_min_spin.setRange(0.01, 0.5)
        self.steady_min_spin.setValue(self.settings.pk_steady_state_range[0])
        self.steady_min_spin.valueChanged.connect(self.update_pk_range)
        
        self.steady_max_spin = QDoubleSpinBox()
        self.steady_max_spin.setRange(0.01, 0.5)
        self.steady_max_spin.setValue(self.settings.pk_steady_state_range[1])
        self.steady_max_spin.valueChanged.connect(self.update_pk_range)
        pk_layout.addRow("Steady state range:", self.create_min_max_widget(
            self.steady_min_spin, self.steady_max_spin))
        
        self.pk_group.setLayout(pk_layout)
        self.layout.addWidget(self.pk_group)
        
        # Add stretch to push content to top
        self.layout.addStretch()
        
        # Set initial state for trend display
        self.toggle_trend_display()
        
    def create_min_max_widget(self, min_spin, max_spin):
        """Create a widget with min and max spinboxes"""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.addWidget(QLabel("Min:"))
        layout.addWidget(min_spin)
        layout.addWidget(QLabel("Max:"))
        layout.addWidget(max_spin)
        layout.addStretch()
        layout.setContentsMargins(0, 0, 0, 0)
        return widget
        
    def toggle_time_series(self, state):
        """Enable/disable time series options"""
        enabled = state == Qt.CheckState.Checked.value
        self.trend_list.setEnabled(enabled)
        self.display_trend_cb.setEnabled(enabled)
        self.toggle_trend_display()
        self.pk_group.setEnabled(enabled and 'Pharmacokinetic Profile' in [
            item.text() for item in self.trend_list.selectedItems()])
        
    def toggle_trend_display(self):
        """Enable/disable trend line styles based on display checkbox"""
        display_enabled = self.display_trend_cb.isChecked()
        time_series_enabled = self.time_series_cb.isChecked()
        self.line_list.setEnabled(display_enabled and time_series_enabled)
        
    def update_trends(self):
        """Update selected trend types in settings"""
        selected = [item.text() for item in self.trend_list.selectedItems()]
        self.settings.trend_type_selection = selected
        self.pk_group.setEnabled('Pharmacokinetic Profile' in selected)
        
    def update_line_styles(self):
        """Update selected line styles in settings"""
        selected = [item.text() for item in self.line_list.selectedItems()]
        self.settings.customize_trend_type_selection = selected
        
    def update_pk_range(self):
        """Update PK profile ranges in settings"""
        self.settings.pk_peak_pos_range = (
            self.pk_peak_min_spin.value(), self.pk_peak_max_spin.value()
        )
        self.settings.pk_peak_value_range = (
            self.pk_value_min_spin.value(), self.pk_value_max_spin.value()
        )
        self.settings.pk_growth_rate_range = (
            self.growth_min_spin.value(), self.growth_max_spin.value()
        )
        self.settings.pk_decay_rate_range = (
            self.decay_min_spin.value(), self.decay_max_spin.value()
        )
        self.settings.pk_steady_state_range = (
            self.steady_min_spin.value(), self.steady_max_spin.value()
        )

class GenerationThread(QThread):
    """Thread for running the plot generation"""
    progress_updated = pyqtSignal(int, str)
    image_generated = pyqtSignal(str)
    log_message = pyqtSignal(str)  # New signal for log messages
    finished = pyqtSignal()
    
    def __init__(self, settings):
        super().__init__()
        self.settings = settings
        self.stopped = False
        
    def run(self):
        """Run the generation process"""
        generator = ScatterGenerator(self.settings)
        
        # Create output directory if it doesn't exist
        os.makedirs(self.settings.output_dir, exist_ok=True)
        
        for i in range(self.settings.num_images):
            if self.stopped:
                break
                
            plot_number = i + 1
            self.progress_updated.emit(
                int((i+1)/self.settings.num_images*100), 
                f"Generating plot {plot_number}/{self.settings.num_images}"
            )
            
            # Create scatter plot
            (fig, all_series, all_errors, color_mode, dpi, bbox_pad,
             log_messages, x_ticks_major, x_ticks_minor, 
             y_ticks_major, y_ticks_minor) = generator.create_scatter_plot(plot_number)
            
            # Emit log messages
            for message in log_messages:
                self.log_message.emit(message)
            
            # Save temporary image
            temp_filename = os.path.join(
                self.settings.output_dir, 
                f'temp_scatter_plot_{plot_number:03d}.png'
            )
            img_filename = os.path.join(
                self.settings.output_dir, 
                f'scatter_plot_{plot_number:03d}.{self.settings.output_format}'
            )
            
            # Remove existing files if they exist
            for fpath in [temp_filename, img_filename]:
                if os.path.exists(fpath):
                    os.remove(fpath)
            
            # Save with customized parameters
            fig.savefig(temp_filename, dpi=dpi, bbox_inches='tight', pad_inches=bbox_pad)
            plt.close(fig)
            
            # Apply vintage effects if enabled
            if (self.settings.vintage_bw_image and 
                color_mode == 'bw_only' and 
                random.random() < 0.7):
                try:
                    final_img = generator.apply_vintage_effects(temp_filename, self.settings.vintage_intensity)
                    final_img.save(img_filename)
                    # Remove temporary file after successful vintage effect
                    if os.path.exists(temp_filename):
                        os.remove(temp_filename)
                except Exception as e:
                    self.log_message.emit(f"Error when applying vintage effects: {e}")
                    # Fallback to original if vintage fails
                    os.replace(temp_filename, img_filename)
            else:
                # Just move the temporary file to final name
                os.replace(temp_filename, img_filename)
            
            # Save data files
            generator.save_data_files(plot_number, all_series, all_errors)
            
            # Save tick files
            generator.save_tick_files(plot_number, x_ticks_major, x_ticks_minor, 
                                     y_ticks_major, y_ticks_minor)
            
            # Emit log messages for file paths
            self.log_message.emit(f"Image saved: {img_filename}")
            for series_idx in range(len(all_series)):
                data_file = f'scatter_plot_data_{plot_number:03d}_series_{series_idx+1}.txt'
                self.log_message.emit(f"Data saved: {data_file}")
                if self.settings.add_error_bars:
                    error_file = f'error_bar_value__plot_data_{plot_number:03d}_series_{series_idx+1}.txt'
                    self.log_message.emit(f"Error data saved: {error_file}")
            
            # Emit log messages for tick files
            if x_ticks_major:
                self.log_message.emit(f"X-axis major ticks saved: tick_x_major_{plot_number:03d}.txt")
            if x_ticks_minor:
                self.log_message.emit(f"X-axis minor ticks saved: tick_x_minor_{plot_number:03d}.txt")
            if y_ticks_major:
                self.log_message.emit(f"Y-axis major ticks saved: tick_y_major_{plot_number:03d}.txt")
            if y_ticks_minor:
                self.log_message.emit(f"Y-axis minor ticks saved: tick_y_minor_{plot_number:03d}.txt")
            
            # Emit signal with the generated image path
            self.image_generated.emit(img_filename)
            
        self.log_message.emit(f"Successfully generated {self.settings.num_images} plots in '{self.settings.output_dir}'")
        self.finished.emit()
        
    def stop(self):
        """Stop the generation process"""
        self.stopped = True

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.settings = ScatterGeneratorSettings()
        self.settings.update_calculated_properties()
        self.init_ui()
        
    def init_ui(self):
        self.setWindowTitle("Automated Generator of Customized Scatter Plots")
        #self.setWindowIcon(QIcon("LOGO-1.png"))
        self.setMinimumSize(1000, 700)
        
        # Create central widget and main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        # Create splitter for settings and preview
        splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(splitter)
        
        # Settings panel (left)
        settings_panel = QWidget()
        settings_layout = QVBoxLayout(settings_panel)
        
        # Create tab widget for settings
        self.tabs = QTabWidget()
        self.tabs.addTab(GeneralSettingsTab(self.settings), "General Setting")
        self.tabs.addTab(DataPointsSettingsTab(self.settings), "Representation of the Data Points")
        self.tabs.addTab(AxisGridSettingsTab(self.settings), "Axis, Scale and Grid Configuration")
        self.tabs.addTab(DataGenerationSettingsTab(self.settings), "Data Generation Methods")
        
        settings_layout.addWidget(self.tabs)
        
        # Preview panel (right)
        preview_panel = QWidget()
        preview_layout = QVBoxLayout(preview_panel)
        
        # Preview label
        self.preview_label = QLabel()
        self.preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_label.setMinimumSize(400, 300)
        self.preview_label.setStyleSheet("background-color: #f0f0f0; border: 1px solid #cccccc;")
        self.preview_label.setText("Preview will appear here")
        
        # Scroll area for preview
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setWidget(self.preview_label)
        
        preview_layout.addWidget(QLabel("<b>Generated Plot Preview</b>"))
        preview_layout.addWidget(scroll_area)
        
        # Add panels to splitter
        splitter.addWidget(settings_panel)
        splitter.addWidget(preview_panel)
        splitter.setSizes([400, 600])
        
        # Create a horizontal layout for the bottom part (status and outputs)
        bottom_layout = QHBoxLayout()
        
        # Left: Status and Progression
        status_group = QGroupBox("Status and Progression of the Generation")
        status_layout = QVBoxLayout()
        status_layout.addWidget(QLabel("<b>Current Status: </b>"))
        self.status_label = QLabel("Ready to proceed.")
        status_layout.addWidget(self.status_label)
        status_layout.addWidget(QLabel("<b>Progression: </b>"))
        self.progress_bar = QProgressBar()
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setRange(0, 100)
        status_layout.addWidget(self.progress_bar)
        status_group.setLayout(status_layout)
        
        # Right: Prompt Outputs
        output_group = QGroupBox("Prompt Outputs")
        output_layout = QVBoxLayout()
        self.output_text = QTextEdit()
        self.output_text.setReadOnly(True)
        self.output_text.setStyleSheet("font-family: monospace;")
        output_layout.addWidget(self.output_text)
        output_group.setLayout(output_layout)
        
        # Add the two group boxes to the bottom layout
        bottom_layout.addWidget(status_group)
        bottom_layout.addWidget(output_group)
        
        # Add the bottom layout to the main layout
        main_layout.addLayout(bottom_layout)
        
        # Redirect stdout and stderr to the output text widget
        sys.stdout = OutputStream(self.output_text)
        sys.stderr = OutputStream(self.output_text)
        
        # Control buttons
        button_layout = QHBoxLayout()
        
        self.start_btn = QPushButton(QIcon("control-power.png"),"   Start Image Generation")
        self.start_btn.clicked.connect(self.start_generation)
        button_layout.addWidget(self.start_btn)
        
        self.stop_btn = QPushButton(QIcon("control-stop-square.png"),"   Stop Image Generation")
        self.stop_btn.clicked.connect(self.stop_generation)
        self.stop_btn.setEnabled(False)
        button_layout.addWidget(self.stop_btn)
        
        save_btn = QPushButton(QIcon("control-skip-090.png"),"   Save Settings")
        save_btn.clicked.connect(self.save_settings)
        button_layout.addWidget(save_btn)
        
        load_btn = QPushButton(QIcon("control-skip-270.png"),"   Load Settings")
        load_btn.clicked.connect(self.load_settings)
        button_layout.addWidget(load_btn)
        
        main_layout.addLayout(button_layout)
        
        # Initialize generation thread
        self.generation_thread = None
        
    def start_generation(self):
        """Start the plot generation process"""
        # Clear the output text widget
        self.output_text.clear()
        
        # Validate settings
        if not self.validate_settings():
            return
            
        # Confirm with user
        reply = QMessageBox.question(
            self, 
            "Confirm Action",
            f"Begin to generate {self.settings.num_images} scatter plots?\n",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply != QMessageBox.StandardButton.Yes:
            return
            
        # Create and start generation thread
        self.generation_thread = GenerationThread(self.settings)
        self.generation_thread.progress_updated.connect(self.update_progress)
        self.generation_thread.image_generated.connect(self.update_preview)
        self.generation_thread.log_message.connect(self.output_text.append)  # Connect log messages
        self.generation_thread.finished.connect(self.generation_finished)
        
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.tabs.setEnabled(False)
        
        self.generation_thread.start()
        
    def stop_generation(self):
        """Stop the generation process"""
        if self.generation_thread and self.generation_thread.isRunning():
            self.generation_thread.stop()
            self.stop_btn.setEnabled(False)
            self.status_label.setText("Stopping generation...")
            
    def generation_finished(self):
        """Clean up after generation completes"""
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.tabs.setEnabled(True)
        self.status_label.setText("Generation completed")
        
    def update_progress(self, value, message):
        """Update progress bar and status"""
        self.progress_bar.setValue(value)
        self.status_label.setText(message)
        
    def update_preview(self, image_path):
        """Update the preview with the generated image"""
        pixmap = QPixmap(image_path)
        if not pixmap.isNull():
            # Scale pixmap to fit label while maintaining aspect ratio
            scaled_pixmap = pixmap.scaled(
                self.preview_label.width(), 
                self.preview_label.height(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            self.preview_label.setPixmap(scaled_pixmap)
        
    def validate_settings(self):
        """Validate settings before starting generation"""
        # Check output directory
        if not os.path.exists(self.settings.output_dir):
            try:
                os.makedirs(self.settings.output_dir, exist_ok=True)
            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Invalid Directory",
                    f"Cannot create output directory:\n{self.settings.output_dir}\n\n{str(e)}"
                )
                return False
                
        # Check min/max values
        if self.settings.min_points > self.settings.max_points:
            QMessageBox.warning(
                self,
                "Invalid Settings",
                "The minimum number of points cannot be greater than the maximum number of points"
            )
            return False
            
        if self.settings.min_number_data_series > self.settings.max_number_data_series:
            QMessageBox.warning(
                self,
                "Invalid Settings",
                "The minimum number of data series cannot be greater than the maximum number of data series"
            )
            return False
            
        if self.settings.error_min > self.settings.error_max:
            QMessageBox.warning(
                self,
                "Invalid Settings",
                "Minimum error cannot be greater than maximum error"
            )
            return False
            
        # Check that at least one marker is selected
        if not self.settings.markers:
            QMessageBox.warning(
                self,
                "Invalid Settings",
                "At least one marker type must be selected"
            )
            return False
            
        # Check that at least one trend type is selected
        if (self.settings.generate_time_series_patterns and 
            not self.settings.trend_type_selection):
            QMessageBox.warning(
                self,
                "Invalid Settings",
                "At least one trend type must be selected"
            )
            return False
            
        # NEW: Check trend line styles if displaying trend lines
        if (self.settings.generate_time_series_patterns and 
            self.settings.represent_trend_type_selection and 
            not self.settings.customize_trend_type_selection):
            QMessageBox.warning(
                self,
                "Invalid Settings",
                "At least one trend line style must be selected when displaying trend lines"
            )
            return False
            
        return True
        
    def save_settings(self):
        """Save current settings to a JSON file"""
        file_path, _ = QFileDialog.getSaveFileName(
            self, 
            "Save Settings", 
            "", 
            "JSON Files (*.json)"
        )
        
        if file_path:
            # Extract settings to save
            settings_dict = {
                attr: getattr(self.settings, attr) 
                for attr in dir(self.settings) 
                if not callable(getattr(self.settings, attr)) and not attr.startswith("__")
            }
            
            # Remove calculated properties
            for key in ['x_buffer', 'y_buffer_linear', 'y_buffer_log', 
                       'x_min_safe_linear', 'x_max_safe_linear', 
                       'y_min_safe_linear', 'y_max_safe_linear',
                       'y_min_safe_log', 'y_max_safe_log']:
                settings_dict.pop(key, None)
            
            # Save to file
            try:
                with open(file_path, 'w') as f:
                    json.dump(settings_dict, f, indent=2)
                QMessageBox.information(
                    self,
                    "Settings Saved",
                    f"Settings saved to:\n{file_path}"
                )
            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Save Error",
                    f"Failed to save settings:\n{str(e)}"
                )
                
    def load_settings(self):
        """Load settings from a JSON file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, 
            "Load Settings", 
            "", 
            "JSON Files (*.json)"
        )
        
        if file_path:
            try:
                with open(file_path, 'r') as f:
                    settings_dict = json.load(f)
                
                # Apply loaded settings
                for key, value in settings_dict.items():
                    if hasattr(self.settings, key):
                        setattr(self.settings, key, value)
                
                # Update calculated properties
                self.settings.update_calculated_properties()
                
                # Refresh UI
                self.tabs.deleteLater()
                self.tabs = QTabWidget()
                self.tabs.addTab(GeneralSettingsTab(self.settings), "General Setting")
                self.tabs.addWidget(DataPointsSettingsTab(self.settings), "Representation of the Data Points")
                self.tabs.addWidget(AxisGridSettingsTab(self.settings), "Axis, Scale and Grid Configuration")
                self.tabs.addWidget(DataGenerationSettingsTab(self.settings), "Data Generation Methods")
                
                # Find the splitter and replace the settings widget
                central_layout = self.centralWidget().layout()
                splitter = central_layout.itemAt(0).widget()
                splitter.replaceWidget(0, self.tabs)
                
                QMessageBox.information(
                    self,
                    "Settings Loaded",
                    f"Settings loaded from:\n{file_path}"
                )
            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Load Error",
                    f"Failed to load settings:\n{str(e)}"
                )

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()

    sys.exit(app.exec())

