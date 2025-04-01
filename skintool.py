import sys
import os
import numpy as np
from PIL import Image
import imageio
import time
import struct
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, 
                            QPushButton, QLabel, QCheckBox, QFileDialog, 
                            QComboBox, QProgressBar, QMessageBox, QFrame,
                            QGroupBox, QSizePolicy, QSpacerItem, QTabWidget)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont, QIcon, QPixmap

# For Windows dark title bar
try:
    # Windows-specific imports for dark title bar
    from ctypes import windll, c_int, byref, sizeof
    from ctypes.wintypes import HWND, DWORD
except ImportError:
    pass

class App(QWidget):
    def __init__(self):
        super().__init__()

        # Default settings
        self.dark_mode = True
        self.auto_delete = False
        self.folder = None
        self.output_folder = None
        self.alpha_fill = 'white'  # Default alpha fill color (white)
        self.language = 'en'
        self.folder_scan_enabled = True  # Folder scan enabled by default
        self.dds_format = 'DXT5'  # Default DDS format (DXT5 only as requested)
        
        # For tracking file changes
        self.processed_files = set()
        self.last_modification_times = {}
        self.waiting_for_changes = False
        
        # For DDS mipmap generation
        self.mipmap_input_folder = None
        self.mipmap_output_path = None
        self.mipmap_images = []
        self.auto_mip = True
        self.base_size = 4096

        # Translations (offline support)
        self.translations = {
            'en': {
                'select_folder': 'Select Folder (Source)',
                'select_output': 'Select Output Folder (for DDS)',
                'convert': 'Convert PNGs to DDS',
                'dark_mode': 'Dark Mode',
                'delete_pngs': 'Delete PNGs after conversion',
                'source_folder': 'Source Folder: ',
                'output_folder': 'Output Folder: ',
                'language': 'Language',
                'alpha_fill': 'Alpha Fill Color',
                'folder_scan': 'Enable Folder Scan (every 5 seconds)',
                'white': 'White (Air Vehicle)',
                'black': 'Black (Ground Vehicle)',
                'none': 'None',
                'format': 'DDS Format',
                'dxt5': 'DXT5',
                'error_title': 'Error',
                'file_error': 'Error processing file: ',
                'folder_error': 'Please select source and output folders.',
                'conversion_complete': 'Conversion Complete',
                'progress': 'Converting...',
                'settings': 'Settings',
                'folders': 'Folders',
                'conversion': 'Conversion Options',
                'appearance': 'Appearance',
                'app_title': 'SkinTool by FRICODEC',
                'waiting': 'Waiting for file changes...',
                'mipmap_tab': 'DDS Mipmap Generator',
                'skin_tab': 'Skin Converter',
                'mipmap_select_folder': 'Select Mipmap Source Folder',
                'mipmap_select_output': 'Select Mipmap Output File',
                'mipmap_source': 'Mipmap Source Folder: ',
                'mipmap_output': 'Mipmap Output File: ',
                'mipmap_base_size': 'Base Size (Mip 0):',
                'mipmap_auto': 'Auto-complete Mipmap Chain',
                'mipmap_generate': 'Generate DDS with Mipmaps',
                'mipmap_loaded': 'Loaded {0} images for mipmaps.',
                'mipmap_no_images': 'No images found in the selected folder.',
                'mipmap_select_output_first': 'Please select an output file first.',
                'mipmap_select_folder_first': 'Please select a source folder first.',
                'mipmap_success': 'DDS with mipmaps generated successfully!',
                'image_read_error': 'Unable to read image file: ',
                'write_error': 'Error writing output file: '
            },
            'es': {
                'select_folder': 'Seleccionar Carpeta (Fuente)',
                'select_output': 'Seleccionar Carpeta de Salida (para DDS)',
                'convert': 'Convertir PNGs a DDS',
                'dark_mode': 'Modo Oscuro',
                'delete_pngs': 'Eliminar PNGs después de la conversión',
                'source_folder': 'Carpeta de Origen: ',
                'output_folder': 'Carpeta de Salida: ',
                'language': 'Idioma',
                'alpha_fill': 'Color de Relleno Alpha',
                'folder_scan': 'Habilitar Escaneo de Carpeta (cada 5 segundos)',
                'white': 'Blanco (Vehículo Aéreo)',
                'black': 'Negro (Vehículo Terrestre)',
                'none': 'Ninguno',
                'format': 'Formato DDS',
                'dxt5': 'DXT5',
                'error_title': 'Error',
                'file_error': 'Error al procesar el archivo: ',
                'folder_error': 'Por favor seleccione carpetas de origen y destino.',
                'conversion_complete': 'Conversión Completa',
                'progress': 'Convirtiendo...',
                'settings': 'Configuración',
                'folders': 'Carpetas',
                'conversion': 'Opciones de Conversión',
                'appearance': 'Apariencia',
                'app_title': 'SkinTool por FRICODEC',
                'waiting': 'Esperando cambios en los archivos...',
                'mipmap_tab': 'Generador de Mipmaps DDS',
                'skin_tab': 'Conversor de Skin',
                'mipmap_select_folder': 'Seleccionar Carpeta de Origen para Mipmaps',
                'mipmap_select_output': 'Seleccionar Archivo de Salida para Mipmaps',
                'mipmap_source': 'Carpeta de Origen para Mipmaps: ',
                'mipmap_output': 'Archivo de Salida para Mipmaps: ',
                'mipmap_base_size': 'Tamaño Base (Mip 0):',
                'mipmap_auto': 'Completar Cadena de Mipmaps Automáticamente',
                'mipmap_generate': 'Generar DDS con Mipmaps',
                'mipmap_loaded': 'Cargadas {0} imágenes para mipmaps.',
                'mipmap_no_images': 'No se encontraron imágenes en la carpeta seleccionada.',
                'mipmap_select_output_first': 'Por favor seleccione un archivo de salida primero.',
                'mipmap_select_folder_first': 'Por favor seleccione una carpeta de origen primero.',
                'mipmap_success': '¡DDS con mipmaps generado exitosamente!',
                'image_read_error': 'No se puede leer el archivo de imagen: ',
                'write_error': 'Error al escribir el archivo de salida: '
            },
            'fr': {
                'select_folder': 'Sélectionner un Dossier (Source)',
                'select_output': 'Sélectionner un Dossier de Sortie (pour DDS)',
                'convert': 'Convertir les PNG en DDS',
                'dark_mode': 'Mode Sombre',
                'delete_pngs': 'Supprimer les PNG après la conversion',
                'source_folder': 'Dossier Source: ',
                'output_folder': 'Dossier de Sortie: ',
                'language': 'Langue',
                'alpha_fill': 'Couleur de Remplissage Alpha',
                'folder_scan': 'Activer l\'analyse du dossier (toutes les 5 secondes)',
                'white': 'Blanc (Véhicule Aérien)',
                'black': 'Noir (Véhicule Terrestre)',
                'none': 'Aucun',
                'format': 'Format DDS',
                'dxt5': 'DXT5',
                'error_title': 'Erreur',
                'file_error': 'Erreur lors du traitement du fichier: ',
                'folder_error': 'Veuillez sélectionner les dossiers source et de sortie.',
                'conversion_complete': 'Conversion Terminée',
                'progress': 'Conversion en cours...',
                'settings': 'Paramètres',
                'folders': 'Dossiers',
                'conversion': 'Options de Conversion',
                'appearance': 'Apparence',
                'app_title': 'SkinTool par FRICODEC',
                'waiting': 'En attente de modifications de fichiers...',
                'mipmap_tab': 'Générateur de Mipmaps DDS',
                'skin_tab': 'Convertisseur de Skin',
                'mipmap_select_folder': 'Sélectionner Dossier Source pour Mipmaps',
                'mipmap_select_output': 'Sélectionner Fichier de Sortie pour Mipmaps',
                'mipmap_source': 'Dossier Source pour Mipmaps: ',
                'mipmap_output': 'Fichier de Sortie pour Mipmaps: ',
                'mipmap_base_size': 'Taille de Base (Mip 0):',
                'mipmap_auto': 'Compléter Automatiquement la Chaîne de Mipmaps',
                'mipmap_generate': 'Générer DDS avec Mipmaps',
                'mipmap_loaded': '{0} images chargées pour les mipmaps.',
                'mipmap_no_images': 'Aucune image trouvée dans le dossier sélectionné.',
                'mipmap_select_output_first': 'Veuillez d\'abord sélectionner un fichier de sortie.',
                'mipmap_select_folder_first': 'Veuillez d\'abord sélectionner un dossier source.',
                'mipmap_success': 'DDS avec mipmaps généré avec succès !',
                'image_read_error': 'Impossible de lire le fichier image: ',
                'write_error': 'Erreur lors de l\'écriture du fichier de sortie: '
            },
            'zh': {
                'select_folder': '选择文件夹 (源)',
                'select_output': '选择输出文件夹 (DDS)',
                'convert': '转换 PNG 到 DDS',
                'dark_mode': '暗模式',
                'delete_pngs': '转换后删除 PNG',
                'source_folder': '源文件夹: ',
                'output_folder': '输出文件夹: ',
                'language': '语言',
                'alpha_fill': '透明填充颜色',
                'folder_scan': '启用文件夹扫描 (每 5 秒)',
                'white': '白色 (空中载具)',
                'black': '黑色 (地面交通工具)',
                'none': '无',
                'format': 'DDS 格式',
                'dxt5': 'DXT5',
                'error_title': '错误',
                'file_error': '处理文件时出错: ',
                'folder_error': '请选择源文件夹和输出文件夹。',
                'conversion_complete': '转换完成',
                'progress': '转换中...',
                'settings': '设置',
                'folders': '文件夹',
                'conversion': '转换选项',
                'appearance': '外观',
                'app_title': 'SkinTool by FRICODEC',
                'waiting': '等待文件更改...',
                'mipmap_tab': 'DDS Mipmap 生成器',
                'skin_tab': '皮肤转换器',
                'mipmap_select_folder': '选择 Mipmap 源文件夹',
                'mipmap_select_output': '选择 Mipmap 输出文件',
                'mipmap_source': 'Mipmap 源文件夹: ',
                'mipmap_output': 'Mipmap 输出文件: ',
                'mipmap_base_size': '基本尺寸 (Mip 0):',
                'mipmap_auto': '自动完成 Mipmap 链',
                'mipmap_generate': '生成带 Mipmaps 的 DDS',
                'mipmap_loaded': '已加载 {0} 个用于 mipmaps 的图像。',
                'mipmap_no_images': '在选定的文件夹中未找到图像。',
                'mipmap_select_output_first': '请先选择输出文件。',
                'mipmap_select_folder_first': '请先选择源文件夹。',
                'mipmap_success': '已成功生成带有 mipmaps 的 DDS！',
                'image_read_error': '无法读取图像文件: ',
                'write_error': '写入输出文件时出错: '
            },
            'de': {
                'select_folder': 'Ordner Auswählen (Quelle)',
                'select_output': 'Ausgabeverzeichnis wählen (für DDS)',
                'convert': 'Konvertiere PNGs zu DDS',
                'dark_mode': 'Dunkelmodus',
                'delete_pngs': 'PNG nach der Konvertierung löschen',
                'source_folder': 'Quellordner: ',
                'output_folder': 'Ausgabeverzeichnis: ',
                'language': 'Sprache',
                'alpha_fill': 'Alpha-Füllfarbe',
                'folder_scan': 'Ordnerscan aktivieren (alle 5 Sekunden)',
                'white': 'Weiß (Luftfahrzeug)',
                'black': 'Schwarz (Bodenfahrzeug)',
                'none': 'Keiner',
                'format': 'DDS Format',
                'dxt5': 'DXT5',
                'error_title': 'Fehler',
                'file_error': 'Fehler bei der Verarbeitung der Datei: ',
                'folder_error': 'Bitte wählen Sie Quell- und Ausgabeordner aus.',
                'conversion_complete': 'Konvertierung Abgeschlossen',
                'progress': 'Konvertierung läuft...',
                'settings': 'Einstellungen',
                'folders': 'Ordner',
                'conversion': 'Konvertierungsoptionen',
                'appearance': 'Erscheinungsbild',
                'app_title': 'SkinTool von FRICODEC',
                'waiting': 'Warten auf Dateiänderungen...',
                'mipmap_tab': 'DDS Mipmap Generator',
                'skin_tab': 'Skin Konverter',
                'mipmap_select_folder': 'Mipmap Quellordner auswählen',
                'mipmap_select_output': 'Mipmap Ausgabedatei auswählen',
                'mipmap_source': 'Mipmap Quellordner: ',
                'mipmap_output': 'Mipmap Ausgabedatei: ',
                'mipmap_base_size': 'Basisgröße (Mip 0):',
                'mipmap_auto': 'Mipmap-Kette automatisch vervollständigen',
                'mipmap_generate': 'DDS mit Mipmaps generieren',
                'mipmap_loaded': '{0} Bilder für Mipmaps geladen.',
                'mipmap_no_images': 'Keine Bilder im ausgewählten Ordner gefunden.',
                'mipmap_select_output_first': 'Bitte wählen Sie zuerst eine Ausgabedatei aus.',
                'mipmap_select_folder_first': 'Bitte wählen Sie zuerst einen Quellordner aus.',
                'mipmap_success': 'DDS mit Mipmaps erfolgreich generiert!',
                'image_read_error': 'Bilddatei kann nicht gelesen werden: ',
                'write_error': 'Fehler beim Schreiben der Ausgabedatei: '
            },
            
                   'ru': {
                'select_folder': 'Выбрать папку (Источник)',
                'select_output': 'Выбрать папку для сохранения (DDS)',
                'convert': 'Конвертировать PNG в DDS',
                'dark_mode': 'Тёмный режим',
                'delete_pngs': 'Удалять PNG после конвертации',
                'source_folder': 'Исходная папка: ',
                'output_folder': 'Папка для сохранения: ',
                'language': 'Язык',
                'alpha_fill': 'Цвет заливки Alpha',
                'folder_scan': 'Сканировать папку (каждые 5 секунд)',
                'white': 'Белый (Воздушная техника)',
                'black': 'Чёрный (Наземная техника)',
                'none': 'Не выбрано',
                'format': 'Формат DDS',
                'dxt5': 'DXT5',
                'error_title': 'Ошибка',
                'file_error': 'Ошибка обработки файла: ',
                'folder_error': 'Выберите исходную папку и папку для сохранения.',
                'conversion_complete': 'Конвертация завершена',
                'progress': 'Конвертация...',
                'settings': 'Настройки',
                'folders': 'Папки',
                'conversion': 'Опции конвертации',
                'appearance': 'Внешний вид',
                'app_title': 'SkinTool от FRICODEC',
                'waiting': 'Ожидание изменений файлов...',
                'mipmap_tab': 'Генератор DDS Mipmap',
                'skin_tab': 'Конвертер скинов',
                'mipmap_select_folder': 'Выбрать папку для Mipmap',
                'mipmap_select_output': 'Выбрать файл для Mipmap',
                'mipmap_source': 'Папка с Mipmap: ',
                'mipmap_output': 'Файл для Mipmap: ',
                'mipmap_base_size': 'Базовый размер (Mip 0):',
                'mipmap_auto': 'Автозавершение цепочки Mipmap',
                'mipmap_generate': 'Создать DDS с Mipmap'
            }
        }

        self.initUI()
        
        # Set dark title bar if in dark mode
        if self.dark_mode:
            self.set_dark_title_bar()

    def initUI(self):
        # Set application font
        app_font = QFont("Segoe UI", 10)
        QApplication.setFont(app_font)
        
        # Change 2: Updated app title to "SkinTool by FRICODEC"
        self.setWindowTitle(self.translations[self.language]['app_title'])
        self.setGeometry(100, 100, 700, 650)  # Slightly taller to accommodate tabs
        
        # Main layout
        main_layout = QVBoxLayout()
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        # ===== HEADER SECTION =====
        header_layout = QHBoxLayout()
        
        # Language selection
        lang_group = QGroupBox()
        lang_group.setFlat(True)
        lang_layout = QVBoxLayout()
        
        lang_label = QLabel(self.translations[self.language]['language'])
        lang_label.setFont(QFont("Segoe UI", 11, QFont.Bold))
        lang_layout.addWidget(lang_label)
        
        self.lang_combo = QComboBox()
        self.lang_combo.addItems(['English', 'Español', 'Français', '中文', 'Deutsch', 'Русский'])
        self.lang_combo.currentIndexChanged.connect(self.change_language)
        lang_layout.addWidget(self.lang_combo)
        
        lang_group.setLayout(lang_layout)
        header_layout.addWidget(lang_group)
        
        # Appearance toggle
        appearance_group = QGroupBox()
        appearance_group.setFlat(True)
        appearance_layout = QVBoxLayout()
        
        appearance_label = QLabel(self.translations[self.language]['appearance'])
        appearance_label.setFont(QFont("Segoe UI", 11, QFont.Bold))
        appearance_layout.addWidget(appearance_label)
        
        self.mode_checkbox = QCheckBox(self.translations[self.language]['dark_mode'])
        self.mode_checkbox.setChecked(self.dark_mode)
        self.mode_checkbox.stateChanged.connect(self.toggle_mode)
        appearance_layout.addWidget(self.mode_checkbox)
        
        appearance_group.setLayout(appearance_layout)
        header_layout.addWidget(appearance_group)
        
        main_layout.addLayout(header_layout)
        
        # Add separator line
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        main_layout.addWidget(separator)
        
        # Create tab widget
        self.tab_widget = QTabWidget()
        
        # Create tabs
        self.skin_tab = QWidget()
        self.mipmap_tab = QWidget()
        
        # Add tabs to widget
        self.tab_widget.addTab(self.skin_tab, self.translations[self.language]['skin_tab'])
        self.tab_widget.addTab(self.mipmap_tab, self.translations[self.language]['mipmap_tab'])
        
        # Setup Skin Converter Tab
        self.setup_skin_tab()
        
        # Setup Mipmap Generator Tab
        self.setup_mipmap_tab()
        
        # Add tab widget to main layout
        main_layout.addWidget(self.tab_widget)
        
        self.setLayout(main_layout)
        self.apply_language()
        self.apply_theme()
        self.show()

        # Timer for auto scan (checking PNG files every 5 seconds)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.auto_scan_for_png)

        if self.folder_scan_enabled:
            self.timer.start(5000)
            
    def setup_skin_tab(self):
        """Setup the Skin Converter tab"""
        skin_layout = QVBoxLayout()
        
        # ===== FOLDERS SECTION =====
        folders_group = QGroupBox(self.translations[self.language]['folders'])
        folders_group.setFont(QFont("Segoe UI", 11, QFont.Bold))
        folders_layout = QVBoxLayout()
        
        # Source folder selection
        source_layout = QHBoxLayout()
        
        # Updated: Make button width match the longer text (output folder button)
        button_width = 250  # Increased width to accommodate longer text
        
        self.folder_button = QPushButton(self.translations[self.language]['select_folder'])
        self.folder_button.clicked.connect(self.select_folder)
        self.folder_button.setFixedWidth(button_width)
        source_layout.addWidget(self.folder_button)
        
        self.folder_label = QLabel(f"{self.translations[self.language]['source_folder']} {self.translations[self.language]['none']}")
        source_layout.addWidget(self.folder_label, 1)
        folders_layout.addLayout(source_layout)
        
        # Output folder selection
        output_layout = QHBoxLayout()
        self.output_folder_button = QPushButton(self.translations[self.language]['select_output'])
        self.output_folder_button.clicked.connect(self.select_output_folder)
        self.output_folder_button.setFixedWidth(button_width)
        output_layout.addWidget(self.output_folder_button)
        
        self.output_folder_label = QLabel(f"{self.translations[self.language]['output_folder']} {self.translations[self.language]['none']}")
        output_layout.addWidget(self.output_folder_label, 1)
        folders_layout.addLayout(output_layout)
        
        folders_group.setLayout(folders_layout)
        skin_layout.addWidget(folders_group)
        
        # ===== CONVERSION OPTIONS SECTION =====
        options_group = QGroupBox(self.translations[self.language]['conversion'])
        options_group.setFont(QFont("Segoe UI", 11, QFont.Bold))
        options_layout = QVBoxLayout()
        
        # Alpha Fill Color
        alpha_layout = QHBoxLayout()
        alpha_label = QLabel(self.translations[self.language]['alpha_fill'])
        alpha_label.setMinimumWidth(150)
        alpha_layout.addWidget(alpha_label)
        
        self.alpha_fill_combo = QComboBox()
        self.alpha_fill_combo.addItems([self.translations[self.language]['white'], self.translations[self.language]['black']])
        self.alpha_fill_combo.currentIndexChanged.connect(self.change_alpha_fill)
        alpha_layout.addWidget(self.alpha_fill_combo)
        options_layout.addLayout(alpha_layout)
        
        # DDS Format
        format_layout = QHBoxLayout()
        format_label = QLabel(self.translations[self.language]['format'])
        format_label.setMinimumWidth(150)
        format_layout.addWidget(format_label)
        
        self.format_combo = QComboBox()
        self.format_combo.addItem("DXT5")
        format_layout.addWidget(self.format_combo)
        options_layout.addLayout(format_layout)
        
        # Auto-delete option
        self.delete_checkbox = QCheckBox(self.translations[self.language]['delete_pngs'])
        self.delete_checkbox.setChecked(self.auto_delete)
        self.delete_checkbox.stateChanged.connect(self.toggle_delete)
        options_layout.addWidget(self.delete_checkbox)
        
        # Folder scan option
        self.folder_scan_checkbox = QCheckBox(self.translations[self.language]['folder_scan'])
        self.folder_scan_checkbox.setChecked(self.folder_scan_enabled)
        self.folder_scan_checkbox.stateChanged.connect(self.toggle_folder_scan)
        options_layout.addWidget(self.folder_scan_checkbox)
        
        options_group.setLayout(options_layout)
        skin_layout.addWidget(options_group)
        
        # ===== PROGRESS SECTION =====
        progress_group = QGroupBox()
        progress_group.setFlat(True)
        progress_layout = QVBoxLayout()
        
        self.progress_label = QLabel(self.translations[self.language]['progress'])
        self.progress_label.setVisible(False)
        progress_layout.addWidget(self.progress_label)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setAlignment(Qt.AlignCenter)
        progress_layout.addWidget(self.progress_bar)
        
        # Add status label for waiting for file changes
        self.status_label = QLabel("")
        self.status_label.setAlignment(Qt.AlignCenter)
        progress_layout.addWidget(self.status_label)
        
        progress_group.setLayout(progress_layout)
        skin_layout.addWidget(progress_group)
        
        # Add spacer to push content up
        skin_layout.addSpacerItem(QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding))
        
        # ===== CONVERT BUTTON =====
        convert_layout = QHBoxLayout()
        convert_layout.addSpacerItem(QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum))
        
        self.convert_button = QPushButton(self.translations[self.language]['convert'])
        self.convert_button.clicked.connect(self.convert_files)
        self.convert_button.setMinimumSize(200, 50)
        self.convert_button.setFont(QFont("Segoe UI", 12, QFont.Bold))
        convert_layout.addWidget(self.convert_button)
        
        convert_layout.addSpacerItem(QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum))
        skin_layout.addLayout(convert_layout)
        
        self.skin_tab.setLayout(skin_layout)
        
    def setup_mipmap_tab(self):
        """Setup the Mipmap Generator tab"""
        mipmap_layout = QVBoxLayout()
        
        # ===== FOLDERS SECTION =====
        folders_group = QGroupBox(self.translations[self.language]['folders'])
        folders_group.setFont(QFont("Segoe UI", 11, QFont.Bold))
        folders_layout = QVBoxLayout()
        
        # Source folder selection
        source_layout = QHBoxLayout()
        button_width = 250
        
        self.mipmap_folder_button = QPushButton(self.translations[self.language]['mipmap_select_folder'])
        self.mipmap_folder_button.clicked.connect(self.select_mipmap_folder)
        self.mipmap_folder_button.setFixedWidth(button_width)
        source_layout.addWidget(self.mipmap_folder_button)
        
        self.mipmap_folder_label = QLabel(f"{self.translations[self.language]['mipmap_source']} {self.translations[self.language]['none']}")
        source_layout.addWidget(self.mipmap_folder_label, 1)
        folders_layout.addLayout(source_layout)
        
        # Output file selection
        output_layout = QHBoxLayout()
        self.mipmap_output_button = QPushButton(self.translations[self.language]['mipmap_select_output'])
        self.mipmap_output_button.clicked.connect(self.select_mipmap_output)
        self.mipmap_output_button.setFixedWidth(button_width)
        output_layout.addWidget(self.mipmap_output_button)
        
        self.mipmap_output_label = QLabel(f"{self.translations[self.language]['mipmap_output']} {self.translations[self.language]['none']}")
        output_layout.addWidget(self.mipmap_output_label, 1)
        folders_layout.addLayout(output_layout)
        
        folders_group.setLayout(folders_layout)
        mipmap_layout.addWidget(folders_group)
        
        # ===== MIPMAP OPTIONS SECTION =====
        options_group = QGroupBox(self.translations[self.language]['conversion'])
        options_group.setFont(QFont("Segoe UI", 11, QFont.Bold))
        options_layout = QVBoxLayout()
        
        # Base Size
        size_layout = QHBoxLayout()
        size_label = QLabel(self.translations[self.language]['mipmap_base_size'])
        size_label.setMinimumWidth(150)
        size_layout.addWidget(size_label)
        
        self.base_size_combo = QComboBox()
        self.base_size_combo.addItems(["8192", "4096", "2048", "1024", "512"])
        self.base_size_combo.setCurrentIndex(1)  # Default to 4096
        self.base_size_combo.currentTextChanged.connect(self.change_base_size)
        size_layout.addWidget(self.base_size_combo)
        options_layout.addLayout(size_layout)
        
        # Auto-complete mipmap option
        self.auto_mip_checkbox = QCheckBox(self.translations[self.language]['mipmap_auto'])
        self.auto_mip_checkbox.setChecked(self.auto_mip)
        self.auto_mip_checkbox.stateChanged.connect(self.toggle_auto_mip)
        options_layout.addWidget(self.auto_mip_checkbox)
        
        options_group.setLayout(options_layout)
        mipmap_layout.addWidget(options_group)
        
        # ===== PROGRESS SECTION =====
        mipmap_progress_group = QGroupBox()
        mipmap_progress_group.setFlat(True)
        mipmap_progress_layout = QVBoxLayout()
        
        self.mipmap_progress_bar = QProgressBar()
        self.mipmap_progress_bar.setVisible(False)
        self.mipmap_progress_bar.setTextVisible(True)
        self.mipmap_progress_bar.setAlignment(Qt.AlignCenter)
        mipmap_progress_layout.addWidget(self.mipmap_progress_bar)
        
        # Add status label
        self.mipmap_status_label = QLabel("")
        self.mipmap_status_label.setAlignment(Qt.AlignCenter)
        mipmap_progress_layout.addWidget(self.mipmap_status_label)
        
        # Preview area
        self.preview_label = QLabel()
        self.preview_label.setAlignment(Qt.AlignCenter)
        self.preview_label.setMinimumHeight(200)
        mipmap_progress_layout.addWidget(self.preview_label)
        
        mipmap_progress_group.setLayout(mipmap_progress_layout)
        mipmap_layout.addWidget(mipmap_progress_group)
        
        # Add spacer to push content up
        mipmap_layout.addSpacerItem(QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding))
        
        # ===== GENERATE BUTTON =====
        generate_layout = QHBoxLayout()
        generate_layout.addSpacerItem(QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum))
        
        self.generate_button = QPushButton(self.translations[self.language]['mipmap_generate'])
        self.generate_button.clicked.connect(self.generate_mipmap_dds)
        self.generate_button.setMinimumSize(200, 50)
        self.generate_button.setFont(QFont("Segoe UI", 12, QFont.Bold))
        generate_layout.addWidget(self.generate_button)
        
        generate_layout.addSpacerItem(QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum))
        mipmap_layout.addLayout(generate_layout)
        
        self.mipmap_tab.setLayout(mipmap_layout)

    # Function to set Windows dark title bar
    def set_dark_title_bar(self):
        """Set Windows dark title bar if available and in dark mode"""
        if sys.platform == "win32":
            try:
                # Windows 10 1809 or later
                DWMWA_USE_IMMERSIVE_DARK_MODE = 20
                hwnd = int(self.winId())
                
                # Enable dark title bar
                windll.dwmapi.DwmSetWindowAttribute(
                    HWND(hwnd),
                    DWMWA_USE_IMMERSIVE_DARK_MODE,
                    byref(c_int(1)),
                    sizeof(c_int)
                )
            except (AttributeError, OSError, ImportError):
                # Older Windows versions or other errors - just skip this
                pass

    def apply_theme(self):
        if self.dark_mode:
            # Dark theme
            self.setStyleSheet("""
                QWidget {
                    background-color: #2D2D30;
                    color: #FFFFFF;
                    font-family: 'Segoe UI';
                }
                QGroupBox {
                    border: 1px solid #3F3F46;
                    border-radius: 4px;
                    margin-top: 1.5ex;
                    padding-top: 1ex;
                }
                QGroupBox::title {
                    subcontrol-origin: margin;
                    subcontrol-position: top left;
                    padding: 0 5px;
                    color: #FFFFFF;
                }
                QPushButton {
                    background-color: #0078D7;
                    color: white;
                    border: none;
                    border-radius: 4px;
                    padding: 8px 16px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #1C97EA;
                }
                QPushButton:pressed {
                    background-color: #0063B1;
                }
                QComboBox {
                    background-color: #3F3F46;
                    border: 1px solid #555555;
                    border-radius: 4px;
                    padding: 5px;
                    min-width: 6em;
                }
                QComboBox:hover {
                    border: 1px solid #0078D7;
                }
                QComboBox::drop-down {
                    subcontrol-origin: padding;
                    subcontrol-position: top right;
                    width: 15px;
                    border-left-width: 1px;
                    border-left-color: #555555;
                    border-left-style: solid;
                }
                QCheckBox {
                    spacing: 8px;
                }
                QCheckBox::indicator {
                    width: 18px;
                    height: 18px;
                    border: 1px solid #555555;
                    border-radius: 3px;
                }
                QCheckBox::indicator:checked {
                    background-color: #0078D7;
                    border: 1px solid #0078D7;
                }
                QProgressBar {
                    border: 1px solid #555555;
                    border-radius: 4px;
                    text-align: center;
                    height: 20px;
                }
                QProgressBar::chunk {
                    background-color: #0078D7;
                    width: 10px;
                }
                QLabel {
                    color: #FFFFFF;
                }
                QFrame[frameShape="4"] { /* HLine */
                    background-color: #3F3F46;
                    max-height: 1px;
                }
                QTabWidget::pane {
                    border: 1px solid #3F3F46;
                    border-radius: 4px;
                }
                QTabBar::tab {
                    background-color: #252526;
                    color: #FFFFFF;
                    border: 1px solid #3F3F46;
                    border-bottom-color: #3F3F46;
                    border-top-left-radius: 4px;
                    border-top-right-radius: 4px;
                    min-width: 8ex;
                    padding: 8px 12px;
                }
                QTabBar::tab:selected {
                    background-color: #0078D7;
                    border-bottom-color: #0078D7;
                }
                QTabBar::tab:!selected {
                    margin-top: 2px;
                }
            """)
            
            # Set dark title bar
            self.set_dark_title_bar()
            
        else:
            # Light theme
            self.setStyleSheet("""
                QWidget {
                    background-color: #F5F5F5;
                    color: #333333;
                    font-family: 'Segoe UI';
                }
                QGroupBox {
                    border: 1px solid #CCCCCC;
                    border-radius: 4px;
                    margin-top: 1.5ex;
                    padding-top: 1ex;
                }
                QGroupBox::title {
                    subcontrol-origin: margin;
                    subcontrol-position: top left;
                    padding: 0 5px;
                    color: #333333;
                }
                QPushButton {
                    background-color: #0078D7;
                    color: white;
                    border: none;
                    border-radius: 4px;
                    padding: 8px 16px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #1C97EA;
                }
                QPushButton:pressed {
                    background-color: #0063B1;
                }
                QComboBox {
                    background-color: #FFFFFF;
                    border: 1px solid #CCCCCC;
                    border-radius: 4px;
                    padding: 5px;
                    min-width: 6em;
                }
                QComboBox:hover {
                    border: 1px solid #0078D7;
                }
                QComboBox::drop-down {
                    subcontrol-origin: padding;
                    subcontrol-position: top right;
                    width: 15px;
                    border-left-width: 1px;
                    border-left-color: #CCCCCC;
                    border-left-style: solid;
                }
                QCheckBox {
                    spacing: 8px;
                }
                QCheckBox::indicator {
                    width: 18px;
                    height: 18px;
                    border: 1px solid #CCCCCC;
                    border-radius: 3px;
                }
                QCheckBox::indicator:checked {
                    background-color: #0078D7;
                    border: 1px solid #0078D7;
                }
                QProgressBar {
                    border: 1px solid #CCCCCC;
                    border-radius: 4px;
                    text-align: center;
                    height: 20px;
                }
                QProgressBar::chunk {
                    background-color: #0078D7;
                    width: 10px;
                }
                QLabel {
                    color: #333333;
                }
                QFrame[frameShape="4"] { /* HLine */
                    background-color: #CCCCCC;
                    max-height: 1px;
                }
                QTabWidget::pane {
                    border: 1px solid #CCCCCC;
                    border-radius: 4px;
                }
                QTabBar::tab {
                    background-color: #E5E5E5;
                    color: #333333;
                    border: 1px solid #CCCCCC;
                    border-bottom-color: #CCCCCC;
                    border-top-left-radius: 4px;
                    border-top-right-radius: 4px;
                    min-width: 8ex;
                    padding: 8px 12px;
                }
                QTabBar::tab:selected {
                    background-color: #0078D7;
                    color: white;
                    border-bottom-color: #0078D7;
                }
                QTabBar::tab:!selected {
                    margin-top: 2px;
                }
            """)
            
            # Reset Windows title bar to light mode
            if sys.platform == "win32":
                try:
                    # Windows 10 1809 or later
                    DWMWA_USE_IMMERSIVE_DARK_MODE = 20
                    hwnd = int(self.winId())
                    
                    # Disable dark title bar
                    windll.dwmapi.DwmSetWindowAttribute(
                        HWND(hwnd),
                        DWMWA_USE_IMMERSIVE_DARK_MODE,
                        byref(c_int(0)),
                        sizeof(c_int)
                    )
                except (AttributeError, OSError, ImportError):
                    # Older Windows versions or other errors - just skip this
                    pass
        
    def apply_language(self):
        """ Updates the UI with the selected language """
        lang = self.language
        # Update window title - Change 2: Updated app title
        self.setWindowTitle(self.translations[lang]['app_title'])
        
        # Update tab titles
        self.tab_widget.setTabText(0, self.translations[lang]['skin_tab'])
        self.tab_widget.setTabText(1, self.translations[lang]['mipmap_tab'])
        
        # Update skin tab elements
        self.folder_button.setText(self.translations[lang]['select_folder'])
        self.output_folder_button.setText(self.translations[lang]['select_output'])
        self.convert_button.setText(self.translations[lang]['convert'])
        self.mode_checkbox.setText(self.translations[lang]['dark_mode'])
        self.delete_checkbox.setText(self.translations[lang]['delete_pngs'])
        self.folder_scan_checkbox.setText(self.translations[lang]['folder_scan'])
        self.folder_label.setText(f"{self.translations[lang]['source_folder']} {self.folder or self.translations[lang]['none']}")
        self.output_folder_label.setText(f"{self.translations[lang]['output_folder']} {self.output_folder or self.translations[lang]['none']}")
        self.progress_label.setText(self.translations[lang]['progress'])
        
        # Update mipmap tab elements
        self.mipmap_folder_button.setText(self.translations[lang]['mipmap_select_folder'])
        self.mipmap_output_button.setText(self.translations[lang]['mipmap_select_output'])
        self.mipmap_folder_label.setText(f"{self.translations[lang]['mipmap_source']} {self.mipmap_input_folder or self.translations[lang]['none']}")
        self.mipmap_output_label.setText(f"{self.translations[lang]['mipmap_output']} {self.mipmap_output_path or self.translations[lang]['none']}")
        self.auto_mip_checkbox.setText(self.translations[lang]['mipmap_auto'])
        self.generate_button.setText(self.translations[lang]['mipmap_generate'])
        
        # Update status label if it's currently showing waiting message
        if self.status_label.text():
            self.status_label.setText(self.translations[lang]['waiting'])
        
        # Update group box titles
        for box in self.findChildren(QGroupBox):
            if box.title() == self.translations['en']['folders'] or box.title() == self.translations['es']['folders'] or \
               box.title() == self.translations['fr']['folders'] or box.title() == self.translations['zh']['folders'] or \
               box.title() == self.translations['de']['folders']:
                box.setTitle(self.translations[lang]['folders'])
            elif box.title() == self.translations['en']['conversion'] or box.title() == self.translations['es']['conversion'] or \
                 box.title() == self.translations['fr']['conversion'] or box.title() == self.translations['zh']['conversion'] or \
                 box.title() == self.translations['de']['conversion']:
                box.setTitle(self.translations[lang]['conversion'])
        
        # Update Alpha Fill Color dropdown
        self.alpha_fill_combo.clear()
        self.alpha_fill_combo.addItems([self.translations[lang]['white'], self.translations[lang]['black']])
        
        # Find and update all labels by their text content
        for label in self.findChildren(QLabel):
            if label.text() == self.translations['en']['language'] or label.text() == self.translations['es']['language'] or \
               label.text() == self.translations['fr']['language'] or label.text() == self.translations['zh']['language'] or \
               label.text() == self.translations['de']['language']:
                label.setText(self.translations[lang]['language'])
            elif label.text() == self.translations['en']['appearance'] or label.text() == self.translations['es']['appearance'] or \
                 label.text() == self.translations['fr']['appearance'] or label.text() == self.translations['zh']['appearance'] or \
                 label.text() == self.translations['de']['appearance']:
                label.setText(self.translations[lang]['appearance'])
            elif label.text() == self.translations['en']['alpha_fill'] or label.text() == self.translations['es']['alpha_fill'] or \
                 label.text() == self.translations['fr']['alpha_fill'] or label.text() == self.translations['zh']['alpha_fill'] or \
                 label.text() == self.translations['de']['alpha_fill']:
                label.setText(self.translations[lang]['alpha_fill'])
            elif label.text() == self.translations['en']['format'] or label.text() == self.translations['es']['format'] or \
                 label.text() == self.translations['fr']['format'] or label.text() == self.translations['zh']['format'] or \
                 label.text() == self.translations['de']['format']:
                label.setText(self.translations[lang]['format'])
            elif label.text() == self.translations['en']['mipmap_base_size'] or label.text() == self.translations['es']['mipmap_base_size'] or \
                 label.text() == self.translations['fr']['mipmap_base_size'] or label.text() == self.translations['zh']['mipmap_base_size'] or \
                 label.text() == self.translations['de']['mipmap_base_size']:
                label.setText(self.translations[lang]['mipmap_base_size'])

    def change_language(self, index):
        """ Change language based on user selection """
        languages = ['en', 'es', 'fr', 'zh', 'de', 'ru']
        self.language = languages[index]
        self.apply_language()

    def change_alpha_fill(self, index):
        """ Change alpha fill color (White for Air Vehicles, Black for Ground Vehicles) """
        self.alpha_fill = 'white' if index == 0 else 'black'

    def change_base_size(self, size_text):
        """ Change base size for mipmap generation """
        try:
            self.base_size = int(size_text)
        except ValueError:
            self.base_size = 4096

    def toggle_auto_mip(self, state):
        """ Toggle auto-complete mipmap chain """
        self.auto_mip = state == Qt.Checked

    def select_folder(self):
        folder = QFileDialog.getExistingDirectory(self, self.translations[self.language]['select_folder'])
        if folder:
            self.folder = folder
            self.folder_label.setText(f"{self.translations[self.language]['source_folder']} {folder}")
            # Auto-set output folder to match source folder if not already set
            if not self.output_folder:
                self.output_folder = self.folder
                self.output_folder_label.setText(f"{self.translations[self.language]['output_folder']} {folder}")
            
            # Initialize file tracking when folder is selected
            self.update_file_tracking()

    def select_output_folder(self):
        folder = QFileDialog.getExistingDirectory(self, self.translations[self.language]['select_output'])
        if folder:
            self.output_folder = folder
            self.output_folder_label.setText(f"{self.translations[self.language]['output_folder']} {folder}")

    def select_mipmap_folder(self):
        """ Select folder containing images for mipmap generation """
        folder = QFileDialog.getExistingDirectory(self, self.translations[self.language]['mipmap_select_folder'])
        if folder:
            self.mipmap_input_folder = folder
            self.mipmap_folder_label.setText(f"{self.translations[self.language]['mipmap_source']} {folder}")
            
            # Load image files
            self.mipmap_images = sorted([
                os.path.join(folder, f) for f in os.listdir(folder)
                if f.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.tga', '.dds'))
            ])
            
            if self.mipmap_images:
                self.mipmap_status_label.setText(self.translations[self.language]['mipmap_loaded'].format(len(self.mipmap_images)))
                self.show_preview(self.mipmap_images[0])
            else:
                self.mipmap_status_label.setText(self.translations[self.language]['mipmap_no_images'])

    def select_mipmap_output(self):
        """ Select output file for DDS with mipmaps """
        output_path = QFileDialog.getSaveFileName(self, self.translations[self.language]['mipmap_select_output'], 
                                                 "", "DDS Files (*.dds)")[0]
        if output_path:
            if not output_path.lower().endswith('.dds'):
                output_path += '.dds'
            self.mipmap_output_path = output_path
            self.mipmap_output_label.setText(f"{self.translations[self.language]['mipmap_output']} {output_path}")

    def show_preview(self, image_path):
        """ Show a preview of the selected image """
        try:
            img = Image.open(image_path).convert("RGBA")
            img.thumbnail((256, 256))
            img_array = np.array(img)
            height, width, channels = img_array.shape
            
            # Convert to QPixmap for display
            bytesPerLine = channels * width
            qImg = QPixmap.fromImage(
                QImage(img_array.data, width, height, bytesPerLine, QImage.Format_RGBA8888)
            )
            self.preview_label.setPixmap(qImg)
        except Exception as e:
            print(f"Error showing preview: {str(e)}")

    # Change 3: Update file tracking for detecting changes
    def update_file_tracking(self):
        """Update the tracking of files in the source folder"""
        if not self.folder:
            return
            
        try:
            # Track all PNG files and their modification times
            self.last_modification_times = {}
            for file in os.listdir(self.folder):
                if file.endswith('.png'):
                    file_path = os.path.join(self.folder, file)
                    self.last_modification_times[file] = os.path.getmtime(file_path)
        except Exception as e:
            print(f"Error updating file tracking: {str(e)}")

    def check_for_file_changes(self):
        """Check if any files have been added, modified, or deleted"""
        if not self.folder:
            return False
            
        try:
            # Get current PNG files and their modification times
            current_files = {}
            for file in os.listdir(self.folder):
                if file.endswith('.png'):
                    file_path = os.path.join(self.folder, file)
                    current_files[file] = os.path.getmtime(file_path)
            
            # Check for new or modified files
            for file, mtime in current_files.items():
                if file not in self.last_modification_times or mtime > self.last_modification_times[file]:
                    self.last_modification_times = current_files
                    return True
            
            # Check for deleted files
            if len(current_files) != len(self.last_modification_times):
                self.last_modification_times = current_files
                return True
                
            return False
        except Exception as e:
            print(f"Error checking for file changes: {str(e)}")
            return False

    # Change 3: Update convert_files to pause after successful conversion until changes detected
    def convert_files(self):
        if not self.folder or not self.output_folder:
            QMessageBox.warning(self, self.translations[self.language]['error_title'], 
                               self.translations[self.language]['folder_error'])
            return

        try:
            # Find all PNG files in the folder
            png_files = [f for f in os.listdir(self.folder) if f.endswith('.png')]
            
            # Group files by base name
            base_names = set(f.rsplit('_', 1)[0] for f in png_files)
            
            # Track if any files were processed
            files_processed = False
            
            # Set up progress bar
            self.progress_label.setVisible(True)
            self.progress_bar.setVisible(True)
            self.progress_bar.setMinimum(0)
            self.progress_bar.setMaximum(len(base_names))
            self.progress_bar.setValue(0)
            
            # Process each set of textures
            for i, base_name in enumerate(base_names):
                roughness_file = f"{base_name}_Roughness.png"
                normal_file = f"{base_name}_Normal.png"
                metallic_file = f"{base_name}_Metallic.png"
                base_color_file = f"{base_name}_BaseColor.png"

                # Check if all required files exist
                required_files = [base_color_file, metallic_file, normal_file, roughness_file]
                if all(os.path.exists(os.path.join(self.folder, f)) for f in required_files):
                    try:
                        self.generate_dds(base_name, base_color_file, metallic_file, normal_file, roughness_file)
                        files_processed = True
                        
                        if self.auto_delete:
                            self.delete_png_files(base_name)
                    except Exception as e:
                        QMessageBox.warning(self, self.translations[self.language]['error_title'], 
                                          f"{self.translations[self.language]['file_error']} {base_name}\n{str(e)}")
                
                # Update progress bar
                self.progress_bar.setValue(i + 1)
                QApplication.processEvents()  # Keep UI responsive
            
            # Hide progress bar when done
            self.progress_bar.setVisible(False)
            self.progress_label.setVisible(False)
            
            # Show completion message
            if files_processed:
                QMessageBox.information(self, self.translations[self.language]['conversion_complete'], 
                                       f"{len(base_names)} texture sets processed.")
                
                # Change 3: Set waiting state and update file tracking
                self.waiting_for_changes = True
                self.status_label.setText(self.translations[self.language]['waiting'])
                self.status_label.setVisible(True)
                self.update_file_tracking()
                
        except Exception as e:
            QMessageBox.critical(self, self.translations[self.language]['error_title'], str(e))
            self.progress_label.setVisible(False)
            self.progress_bar.setVisible(False)

    def generate_mipmap_dds(self):
        """ Generate DDS file with mipmaps """
        if not self.mipmap_output_path:
            QMessageBox.warning(self, self.translations[self.language]['error_title'], 
                               self.translations[self.language]['mipmap_select_output_first'])
            return
            
        if not self.mipmap_images:
            QMessageBox.warning(self, self.translations[self.language]['error_title'], 
                               self.translations[self.language]['mipmap_select_folder_first'])
            return
            
        try:
            # Show progress
            self.mipmap_progress_bar.setVisible(True)
            self.mipmap_progress_bar.setValue(0)
            
            # Call the mipmap generation function
            self.build_single_dds(self.mipmap_images, self.base_size, self.mipmap_output_path)
            
            # Update progress
            self.mipmap_progress_bar.setValue(100)
            
            # Show success message
            QMessageBox.information(self, self.translations[self.language]['conversion_complete'], 
                                  self.translations[self.language]['mipmap_success'])
        except Exception as e:
            QMessageBox.critical(self, self.translations[self.language]['error_title'], str(e))
        finally:
            # Hide progress bar
            self.mipmap_progress_bar.setVisible(False)

    def build_single_dds(self, image_paths, base_size, output_path):
        """
        Builds a single DDS file with mipmaps from a list of image paths.
        
        Args:
            image_paths: List of paths to images to use as mipmap levels
            base_size: Base size for the highest resolution mipmap
            output_path: Path where the DDS file will be saved
        """
        mipmap_images = []
        
        # Progress calculation
        total_steps = len(image_paths)
        if self.auto_mip:
            # Estimate additional steps for auto-complete
            last_img_path = image_paths[-1]
            try:
                last_size = max(Image.open(last_img_path).size)
                while last_size > 1:
                    last_size = max(1, last_size // 2)
                    total_steps += 1
            except Exception:
                pass
        
        current_step = 0
        
        # Process input images
        for i, path in enumerate(image_paths):
            try:
                img = Image.open(path).convert("RGBA")
            except Exception as e:
                error_msg = f"{self.translations[self.language]['image_read_error']} {path}\n{str(e)}"
                QMessageBox.warning(self, self.translations[self.language]['error_title'], error_msg)
                return

            size = max(1, base_size // (2 ** i))
            img = img.resize((size, size), Image.BOX)
            r, g, b, a = img.split()
            bgra = Image.merge("RGBA", (b, g, r, a))
            mipmap_images.append(bgra)
            
            # Update progress
            current_step += 1
            self.mipmap_progress_bar.setValue(int(current_step / total_steps * 100))
            QApplication.processEvents()

        # Automatically complete mipmap
        if self.auto_mip:
            base = mipmap_images[-1]
            w, h = base.size
            while w > 1 or h > 1:
                w, h = max(1, w // 2), max(1, h // 2)
                mip = base.resize((w, h), Image.BOX)
                mipmap_images.append(mip)
                base = mip
                
                # Update progress
                current_step += 1
                self.mipmap_progress_bar.setValue(int(current_step / total_steps * 100))
                QApplication.processEvents()

        width, height = mipmap_images[0].size
        mip_count = len(mipmap_images)
        pitch = width * 4
        mip_data = b''.join([img.tobytes() for img in mipmap_images])

        ddspf = struct.pack("<I I I I I I I I",
                        32, 0x41, 0, 32,
                        0x00FF0000, 0x0000FF00,
                        0x000000FF, 0xFF000000)

        header = struct.pack("<I I I I I I I 11I 32s I I I I I",
                         124,
                         0x2100F,
                         height, width, pitch, 0, mip_count,
                         *([0] * 11),
                         ddspf,
                         0x401008, 0, 0, 0, 0)

        try:
            with open(output_path, "wb") as f:
                f.write(b'DDS ')
                f.write(header)
                f.write(mip_data)

                actual_size = len(mip_data)
                expected_size = sum([
                    max(1, width // (2**i)) * max(1, height // (2**i)) * 4
                    for i in range(mip_count)
                ])
                if actual_size < expected_size:
                    padding = expected_size - actual_size
                    f.write(b'\x00' * padding)
        except Exception as e:
            error_msg = f"{self.translations[self.language]['write_error']} {output_path}\n{str(e)}"
            raise Exception(error_msg)

    def process_roughness(self, roughness_image_path, level=0.65):
        try:
            roughness = Image.open(os.path.join(self.folder, roughness_image_path))
            r_np = np.array(roughness, dtype=np.uint8)
            r_np = 255 - r_np
            r_np = np.power(r_np.astype(np.float32) / 255.0, 1 / level) * 255.0
            return np.clip(r_np, 0, 255).astype(np.uint8)
        except Exception as e:
            raise Exception(f"Error processing roughness map: {str(e)}")

    def generate_dds(self, base_name, base_color_file, metallic_file, normal_file, roughness_file):
        try:
            base_color = np.array(Image.open(os.path.join(self.folder, base_color_file)))
            metallic = np.array(Image.open(os.path.join(self.folder, metallic_file)))
            normal = np.array(Image.open(os.path.join(self.folder, normal_file)))
            roughness = self.process_roughness(roughness_file)

            self.create_basecolor_dds(base_name, base_color)
            self.create_normal_metallic_roughness_dds(base_name, roughness, normal, metallic)
        except Exception as e:
            raise Exception(f"Error generating DDS files: {str(e)}")

    def create_basecolor_dds(self, base_name, base_color_array):
        try:
            # Apply the selected alpha fill color
            alpha_value = 255 if self.alpha_fill == 'white' else 0
            base_color_with_alpha = np.dstack([base_color_array, np.full(base_color_array.shape[:2], alpha_value, dtype=np.uint8)])

            filename = os.path.join(self.output_folder, f"{base_name}_c.dds")
            # Set DXT5 format (as requested)
            imageio.imwrite(filename, base_color_with_alpha, format='DDS', compress=True, dxgi_format='BC3_UNORM')
        except Exception as e:
            raise Exception(f"Error creating base color DDS: {str(e)}")

    def create_normal_metallic_roughness_dds(self, base_name, roughness, normal, metallic):
        try:
            dds_array = np.dstack([roughness, normal[:, :, 1], metallic, normal[:, :, 0]])
            filename = os.path.join(self.output_folder, f"{base_name}_n.dds")
            # Set DXT5 format (as requested)
            imageio.imwrite(filename, dds_array, format='DDS', compress=True, dxgi_format='BC3_UNORM')
        except Exception as e:
            raise Exception(f"Error creating normal/metallic/roughness DDS: {str(e)}")

    def toggle_mode(self, state):
        self.dark_mode = state == Qt.Checked
        self.apply_theme()

    def toggle_delete(self, state):
        self.auto_delete = state == Qt.Checked

    def toggle_folder_scan(self, state):
        self.folder_scan_enabled = state == Qt.Checked
        if self.folder_scan_enabled:
            self.timer.start(5000)  # Start scanning every 5 seconds
        else:
            self.timer.stop()  # Stop scanning

    # Change 3: Update auto_scan_for_png to check for changes before converting
    def auto_scan_for_png(self):
        """ Automatically scans for new PNG files in the folder every 5 seconds """
        if not self.folder:
            return
            
        try:
            # If we're waiting for changes, check if any files have changed
            if self.waiting_for_changes:
                if self.check_for_file_changes():
                    # Files have changed, we can process again
                    self.waiting_for_changes = False
                    self.status_label.setVisible(False)
                    self.convert_files()
            else:
                # Normal scanning mode - check if there are PNG files to convert
                png_files = [f for f in os.listdir(self.folder) if f.endswith('.png')]
                if png_files:
                    self.convert_files()
        except Exception as e:
            # Silent error handling for background scanning
            print(f"Error during auto scan: {str(e)}")

    def delete_png_files(self, base_name):
        """ Deletes the PNG files after conversion if auto-delete is enabled """
        try:
            png_files = [f"{base_name}_BaseColor.png", f"{base_name}_Metallic.png", 
                        f"{base_name}_Normal.png", f"{base_name}_Roughness.png"]
            for file in png_files:
                file_path = os.path.join(self.folder, file)
                if os.path.exists(file_path):
                    os.remove(file_path)
        except Exception as e:
            raise Exception(f"Error deleting PNG files: {str(e)}")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = App()
    sys.exit(app.exec_())
