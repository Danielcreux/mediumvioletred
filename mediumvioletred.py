import os
import sys
import glob
import json
import tempfile
import subprocess
import shutil
import time
from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QFont, QIcon, QColor
from bs4 import BeautifulSoup

# Configuración inicial
FONT_NAME = "MyCustomFont"
ICON_COLOR = "#3498db"

class FontGeneratorApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Generador de Fuentes Personalizadas")
        self.setGeometry(100, 100, 900, 600)
        self.setStyleSheet(self.get_stylesheet())

        self.svg_folder = ""
        self.html_file = ""
        self.temp_dir = tempfile.mkdtemp()

        self.init_ui()  # Inicializar la UI primero, define self.console

        self.fontforge_path = self.find_fontforge()  # Ahora se puede usar self.console
        self.check_dependencies()

        
    def get_stylesheet(self):
        return f"""
            QMainWindow {{
                background-color: #2c3e50;
                color: #ecf0f1;
            }}
            QWidget {{
                background-color: #2c3e50;
                color: #ecf0f1;
                font-family: 'Segoe UI';
            }}
            QPushButton {{
                background-color: {ICON_COLOR};
                color: white;
                border-radius: 5px;
                padding: 8px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: #2980b9;
            }}
            QLineEdit, QListWidget {{
                background-color: #34495e;
                color: #ecf0f1;
                border: 1px solid {ICON_COLOR};
                border-radius: 5px;
                padding: 5px;
            }}
            QLabel {{
                font-weight: bold;
                font-size: 12px;
            }}
            QGroupBox {{
                border: 1px solid {ICON_COLOR};
                border-radius: 8px;
                margin-top: 10px;
                font-weight: bold;
                padding-top: 15px;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                subcontrol-position: top center;
                padding: 0 5px;
            }}
            QTextEdit {{
                background-color: #1e2a38;
                color: #bdc3c7;
                border: 1px solid #34495e;
                border-radius: 5px;
            }}
        """
        
    def find_fontforge(self):
        # Buscar FontForge en las ubicaciones comunes
        possible_paths = [
            "/usr/bin/fontforge",
            "/usr/local/bin/fontforge",
            "C:/Program Files (x86)/FontForgeBuilds/bin/fontforge.exe",
            "C:/Program Files/FontForgeBuilds/bin/fontforge.exe"
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                self.log_message(f"✅ FontForge encontrado en: {path}")
                return path
                
        self.log_message("⚠️ FontForge no encontrado. Necesario para generar fuentes.")
        return None
        
    def check_dependencies(self):
        try:
            from bs4 import BeautifulSoup
            self.log_message("✅ BeautifulSoup4 está instalado")
        except ImportError:
            self.log_message("⚠️ Instalando BeautifulSoup4...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", "beautifulsoup4"])
            
    def log_message(self, message):
        self.console.append(message)
        QApplication.processEvents()
        
    def select_svg_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Seleccionar Carpeta SVG")
        if folder:
            svg_files = glob.glob(os.path.join(folder, "*.svg"))
            if svg_files:
                self.svg_folder = folder
                self.svg_path_edit.setText(folder)
                self.generate_btn.setEnabled(bool(self.fontforge_path))
                self.log_message(f"📂 Carpeta SVG seleccionada: {folder} ({len(svg_files)} archivos)")
            else:
                self.log_message("❌ No se encontraron archivos SVG en la carpeta")
                self.generate_btn.setEnabled(False)
                
    def select_html_file(self):
        file, _ = QFileDialog.getOpenFileName(
            self, 
            "Seleccionar Archivo", 
            "", 
            "Archivos Web (*.html *.php *.htm)"
        )
        if file:
            self.html_file = file
            self.file_path_edit.setText(file)
            self.load_html_tags()
            self.log_message(f"📄 Archivo seleccionado: {file}")
            
    def load_html_tags(self):
        self.tags_list.clear()
        try:
            with open(self.html_file, 'r', encoding='utf-8') as f:
                content = f.read()
                soup = BeautifulSoup(content, 'html.parser')
                tags = set([tag.name for tag in soup.find_all()])
                
                for tag in sorted(tags):
                    if len(tag) > 0:
                        self.tags_list.addItem(tag)
                        
                self.modify_btn.setEnabled(True)
                self.log_message(f"🏷️ Etiquetas encontradas: {len(tags)}")
                
        except Exception as e:
            self.log_message(f"❌ Error al cargar archivo: {str(e)}")
            self.modify_btn.setEnabled(False)
            
    def generate_font(self):
        if not self.svg_folder:
            self.log_message("❌ Primero selecciona una carpeta SVG")
            return
            
        output_file, _ = QFileDialog.getSaveFileName(
            self,
            "Guardar Fuente TTF",
            FONT_NAME + ".ttf",
            "TrueType Font (*.ttf)"
        )
        
        if not output_file:
            return
            
        self.log_message("⏳ Generando fuente...")
        QApplication.processEvents()
        
        try:
            # Crear archivo de script de FontForge corregido
            script_path = os.path.join(self.temp_dir, "generate_font.pe")
            with open(script_path, 'w') as f:
                f.write(self.generate_fontforge_script(output_file))
            
            svg_files = sorted(glob.glob(os.path.join(self.svg_folder, "*.svg")))
            result = subprocess.run(
                [self.fontforge_path, "-script", script_path] + svg_files,
                capture_output=True,
                text=True
            )

            
            if result.returncode == 0:
                self.log_message(f"✅ Fuente generada exitosamente: {output_file}")
                self.log_message("⚠️ Nota: Los archivos SVG deben tener nombres Unicode (ej: U+0041.svg)")
            else:
                self.log_message(f"❌ Error al generar fuente: {result.stderr}")
                
        except Exception as e:
            self.log_message(f"❌ Error crítico: {str(e)}")
            
    def generate_fontforge_script(self, output_file):
            """Genera un script de FontForge que crea una fuente desde archivos SVG con nombres como 'a.svg' o 'b.svg'"""
            return f"""
        # Crear una nueva fuente
        New()

        # Configurar metadatos de la fuente
        SetFontNames("{FONT_NAME}", "{FONT_NAME}", "{FONT_NAME}", "Regular")
        SetTTFName(0x409, 1, "{FONT_NAME}")
        SetTTFName(0x409, 2, "Regular")
        SetTTFName(0x409, 3, "{FONT_NAME}")
        SetTTFName(0x409, 4, "{FONT_NAME}")
        SetTTFName(0x409, 5, "Version 1.0")

        # Configurar unidades
        ScaleToEm(1000)

        # Iterar sobre los archivos pasados como argumentos
        foreach($argv)
            Open($1)
            SelectAll()
            Copy()
            Close()

            # Obtener el nombre base del archivo (sin extensión)
            filename = FileName($1)
            base = FileBaseName(filename)

            # Obtener código Unicode del primer carácter del nombre
            Select(CharToUnicode(substr(base, 0, 1)))
            Paste()
            SetWidth(600)
            SelectNone()
        endloop

        # Guardar la fuente
        Generate("{output_file.replace('\\\\', '/')}")
        Close()
        Quit(0)
        """

            
    def modify_html(self):
        if not self.html_file:
            self.log_message("❌ Primero selecciona un archivo HTML/PHP")
            return
            
        selected_tags = [item.text() for item in self.tags_list.selectedItems()]
        if not selected_tags:
            self.log_message("❌ Selecciona al menos una etiqueta")
            return
        backup_file = None  # Definirlo antes por seguridad

        try:
            # Leer y modificar el HTML
            with open(self.html_file, 'r', encoding='utf-8') as f:
                content = f.read()

            soup = BeautifulSoup(content, 'html.parser')

            # Agregar CSS embebido
            css = f"""
            @font-face {{
                font-family: '{FONT_NAME}';
                src: url('{FONT_NAME}.ttf') format('truetype');
                font-weight: normal;
                font-style: normal;
            }}

            {', '.join(selected_tags)} {{
                font-family: '{FONT_NAME}', sans-serif;
            }}
            """
            style_tag = soup.new_tag('style')
            style_tag.string = css
            if soup.head:
                soup.head.append(style_tag)
            else:
                head_tag = soup.new_tag('head')
                head_tag.append(style_tag)
                soup.html.insert(0, head_tag)

            # Crear backup
            backup_dir = os.path.join(os.path.dirname(self.html_file), "backups")
            os.makedirs(backup_dir, exist_ok=True)
            base_name = os.path.basename(self.html_file)
            backup_file = os.path.join(backup_dir, base_name)
            shutil.copy2(self.html_file, backup_file)

            # Guardar el HTML modificado
            with open(self.html_file, 'w', encoding='utf-8') as f:
                f.write(str(soup))

            self.log_message(f"✅ Archivo modificado: {self.html_file}")
            self.log_message(f"   Etiquetas actualizadas: {', '.join(selected_tags)}")
            self.log_message(f"   Usando fuente: {FONT_NAME}")
            if backup_file:
                self.log_message(f"   Se creó un backup en: {backup_file}")

        except Exception as e:
            self.log_message(f"❌ Error al modificar archivo: {str(e)}")

            
            
            
            
    def init_ui(self):
        main_widget = QWidget()
        main_layout = QVBoxLayout()
        
        # Header
        header = QLabel("Generador de Fuentes Personalizadas")
        header.setFont(QFont("Arial", 18, QFont.Bold))
        header.setStyleSheet("color: #3498db; margin-bottom: 20px;")
        header.setAlignment(Qt.AlignCenter)
        
        # Sección SVG
        svg_group = QGroupBox("Generar Fuente desde SVG")
        svg_layout = QVBoxLayout()
        
        svg_btn_layout = QHBoxLayout()
        self.svg_path_edit = QLineEdit()
        self.svg_path_edit.setPlaceholderText("Carpeta con archivos SVG...")
        svg_browse_btn = QPushButton("Seleccionar Carpeta")
        svg_browse_btn.clicked.connect(self.select_svg_folder)
        svg_btn_layout.addWidget(self.svg_path_edit)
        svg_btn_layout.addWidget(svg_browse_btn)
        
        tip_label = QLabel("Los archivos SVG deben nombrarse con códigos Unicode (ej: U+0041.svg para 'A')")
        tip_label.setStyleSheet("font-style: italic; color: #95a5a6; font-size: 10px;")
        
        self.generate_btn = QPushButton("Generar Fuente TTF")
        self.generate_btn.clicked.connect(self.generate_font)
        self.generate_btn.setEnabled(False)
        
        svg_layout.addLayout(svg_btn_layout)
        svg_layout.addWidget(tip_label)
        svg_layout.addWidget(self.generate_btn)
        svg_group.setLayout(svg_layout)
        
        # Sección HTML
        html_group = QGroupBox("Modificar Archivo HTML/PHP")
        html_layout = QVBoxLayout()
        
        file_btn_layout = QHBoxLayout()
        self.file_path_edit = QLineEdit()
        self.file_path_edit.setPlaceholderText("Archivo HTML/PHP...")
        file_browse_btn = QPushButton("Seleccionar Archivo")
        file_browse_btn.clicked.connect(self.select_html_file)
        file_btn_layout.addWidget(self.file_path_edit)
        file_btn_layout.addWidget(file_browse_btn)
        
        tags_layout = QHBoxLayout()
        tags_label = QLabel("Etiquetas a modificar:")
        self.tags_list = QListWidget()
        self.tags_list.setSelectionMode(QListWidget.MultiSelection)
        
        tags_layout.addWidget(tags_label)
        tags_layout.addWidget(self.tags_list)
        
        self.modify_btn = QPushButton("Aplicar Cambios")
        self.modify_btn.clicked.connect(self.modify_html)
        self.modify_btn.setEnabled(False)
        
        html_layout.addLayout(file_btn_layout)
        html_layout.addLayout(tags_layout)
        html_layout.addWidget(self.modify_btn)
        html_group.setLayout(html_layout)
        
        # Consola de salida
        console_group = QGroupBox("Mensajes")
        console_layout = QVBoxLayout()
        self.console = QTextEdit()
        self.console.setReadOnly(True)
        console_layout.addWidget(self.console)
        console_group.setLayout(console_layout)
        
        # Agregar componentes al layout principal
        main_layout.addWidget(header)
        main_layout.addWidget(svg_group)
        main_layout.addWidget(html_group)
        main_layout.addWidget(console_group)
        
        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)
        
        # Barra de estado
        self.statusBar().showMessage("Listo")
        
    def closeEvent(self, event):
        # Limpieza al cerrar
        try:
            import shutil
            shutil.rmtree(self.temp_dir)
        except:
            pass
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = FontGeneratorApp()
    window.show()
    sys.exit(app.exec_())
