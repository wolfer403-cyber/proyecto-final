import sys
import os
import json
from datetime import datetime
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QLineEdit, QComboBox, QPushButton, QTableWidget, QTableWidgetItem,
    QMessageBox, QHeaderView, QFrame, QInputDialog, QDialog, QTabWidget
)
from PyQt5.QtCore import Qt

# Importación de Matplotlib para PyQt5
import matplotlib
matplotlib.use('Qt5Agg')
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure


# ==============================================================================
# MODELO: Lógica de negocio y persistencia
# ==============================================================================
class GestorGastos:
    def __init__(self, ruta_archivo: str = "data/gastos.json", ruta_categorias: str = "data/categorias.json"):
        self.ruta_archivo = ruta_archivo
        self.ruta_categorias = ruta_categorias
        self.transacciones = []
        self.categorias_defecto = [
            "🐜 Gasto Hormiga (Café, Snacks, Vicios)",
            "🛒 Mercado / Alimentación Básica",
            "🚗 Transporte / Gasolina",
            "💡 Servicios / Cuentas Fijas"
        ]
        self._asegurar_directorio()
        self.cargar_datos()
        self.cargar_categorias()

    def _asegurar_directorio(self):
        for ruta in [self.ruta_archivo, self.ruta_categorias]:
            directorio = os.path.dirname(ruta)
            if directorio and not os.path.exists(directorio):
                os.makedirs(directorio, exist_ok=True)

    def cargar_datos(self):
        if os.path.exists(self.ruta_archivo):
            try:
                with open(self.ruta_archivo, "r", encoding="utf-8") as f:
                    self.transacciones = json.load(f)
            except Exception:
                self.transacciones = []
        else:
            self.transacciones = []

    def guardar_datos(self):
        with open(self.ruta_archivo, "w", encoding="utf-8") as f:
            json.dump(self.transacciones, f, ensure_ascii=False, indent=4)

    def cargar_categorias(self) -> list:
        if os.path.exists(self.ruta_categorias):
            try:
                with open(self.ruta_categorias, "r", encoding="utf-8") as f:
                    self.categorias = json.load(f)
            except Exception:
                self.categorias = self.categorias_defecto.copy()
        else:
            self.categorias = self.categorias_defecto.copy()
            self.guardar_categorias()
        return self.categorias

    def guardar_categorias(self):
        with open(self.ruta_categorias, "w", encoding="utf-8") as f:
            json.dump(self.categorias, f, ensure_ascii=False, indent=4)

    def agregar_categoria_personalizada(self, nueva_cat: str) -> bool:
        if nueva_cat and nueva_cat not in self.categorias:
            self.categorias.append(nueva_cat)
            self.guardar_categorias()
            return True
        return False

    def eliminar_categoria_personalizada(self, cat_eliminar: str) -> bool:
        if cat_eliminar in self.categorias:
            self.categorias.remove(cat_eliminar)
            self.guardar_categorias()
            return True
        return False

    def agregar_transaccion(self, monto: float, categoria: str, descripcion: str, es_ingreso: bool = False) -> dict:
        nueva_t = {
            "id": int(datetime.now().timestamp() * 1000),
            "monto": monto,
            "categoria": "💵 Ingreso / Presupuesto" if es_ingreso else categoria,
            "descripcion": descripcion,
            "es_ingreso": es_ingreso,
            "fecha": datetime.now().strftime("%Y-%m-%d %H:%M")
        }
        self.transacciones.append(nueva_t)
        self.guardar_datos()
        return nueva_t

    def eliminar_transaccion_por_index(self, index_reverse: int):
        index_real = len(self.transacciones) - 1 - index_reverse
        if 0 <= index_real < len(self.transacciones):
            self.transacciones.pop(index_real)
            self.guardar_datos()

    def obtener_presupuesto_total(self) -> float:
        return sum(t["monto"] for t in self.transacciones if t.get("es_ingreso", False) or "Ingreso" in t["categoria"])

    def obtener_gastos_totales(self) -> float:
        return sum(t["monto"] for t in self.transacciones if not t.get("es_ingreso", False) and "Ingreso" not in t["categoria"])

    def obtener_fuga_hormiga(self) -> float:
        return sum(t["monto"] for t in self.transacciones if "Hormiga" in t["categoria"])

    def obtener_disponible(self) -> float:
        return self.obtener_presupuesto_total() - self.obtener_gastos_totales()

    def obtener_desglose_gastos_por_categoria(self) -> dict:
        desglose = {}
        for t in self.transacciones:
            if not t.get("es_ingreso", False) and "Ingreso" not in t["categoria"]:
                cat = t["categoria"].split("(")[0].strip()
                desglose[cat] = desglose.get(cat, 0.0) + t["monto"]
        return desglose

    def reiniciar_datos(self):
        self.transacciones = []
        self.guardar_datos()


# ==============================================================================
# VENTANA DE GRÁFICOS (MATPLOTLIB)
# ==============================================================================
class VentanaGraficos(QDialog):
    def __init__(self, gestor: GestorGastos, parent=None):
        super().__init__(parent)
        self.gestor = gestor
        self.setWindowTitle("Análisis Visual de Gastos y Fuga Hormiga")
        self.resize(800, 500)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        fig = Figure(figsize=(8, 5), facecolor='#1e1e2e')
        canvas = FigureCanvas(fig)
        layout.addWidget(canvas)

        desglose = self.gestor.obtener_desglose_gastos_por_categoria()
        presupuesto = self.gestor.obtener_presupuesto_total()
        gastos_totales = self.gestor.obtener_gastos_totales()
        hormiga = self.gestor.obtener_fuga_hormiga()

        ax1 = fig.add_subplot(121)
        ax1.set_facecolor('#1e1e2e')
        if desglose and sum(desglose.values()) > 0:
            labels = list(desglose.keys())
            values = list(desglose.values())
            colors = ['#f38ba8', '#89b4fa', '#a6e3a1', '#f9e2af', '#cba6f7', '#fab387']
            ax1.pie(
                values, labels=labels, autopct='%1.1f%%',
                startangle=140, colors=colors[:len(values)],
                textprops=dict(color="#cdd6f4")
            )
            ax1.set_title("Distribución de Gastos", color="#89b4fa", fontsize=12, fontweight='bold')
        else:
            ax1.text(0.5, 0.5, "Sin datos de gastos", color="#cdd6f4", ha='center', va='center')
            ax1.set_title("Distribución de Gastos", color="#89b4fa")

        ax2 = fig.add_subplot(122)
        ax2.set_facecolor('#181825')
        categorias = ['Presupuesto', 'Gastos Tot.', 'Fuga Hormiga']
        valores = [presupuesto, gastos_totales, hormiga]
        colores_barras = ['#a6e3a1', '#f38ba8', '#fab387']

        bars = ax2.bar(categorias, valores, color=colores_barras)
        ax2.set_title("Resumen General ($)", color="#89b4fa", fontsize=12, fontweight='bold')
        ax2.tick_params(colors='#cdd6f4')
        ax2.spines['bottom'].set_color('#45475a')
        ax2.spines['top'].set_color('#1e1e2e')
        ax2.spines['right'].set_color('#1e1e2e')
        ax2.spines['left'].set_color('#45475a')

        for bar in bars:
            yval = bar.get_height()
            ax2.text(bar.get_x() + bar.get_width()/2, yval + 0.1, f"${yval:.1f}", ha='center', va='bottom', color='#cdd6f4')

        fig.tight_layout()
        canvas.draw()


# ==============================================================================
# VISTA Y CONTROLADOR PRINCIPAL
# ==============================================================================
class VentanaPrincipal(QMainWindow):
    def __init__(self, gestor: GestorGastos):
        super().__init__()
        self.gestor = gestor
        self.setWindowTitle("Gestor de Gastos Hormiga & Presupuesto")
        self.setMinimumSize(980, 680)

        self.init_ui()
        self.actualizar_interfaz()

    def init_ui(self):
        widget_central = QWidget()
        self.setCentralWidget(widget_central)
        layout_principal = QVBoxLayout(widget_central)

        lbl_titulo = QLabel("🛡️ Control Financiero & Fuga de Capital (Gastos Hormiga)")
        lbl_titulo.setObjectName("lbl_titulo")
        lbl_titulo.setAlignment(Qt.AlignCenter)
        layout_principal.addWidget(lbl_titulo)

        layout_medio = QHBoxLayout()

        frame_form = QFrame()
        frame_form.setObjectName("card")
        layout_form = QVBoxLayout(frame_form)

        self.tabs = QTabWidget()
        self.tabs.setObjectName("tabs_form")

        tab_gasto = QWidget()
        layout_gasto = QVBoxLayout(tab_gasto)

        self.txt_monto_gasto = QLineEdit()
        self.txt_monto_gasto.setPlaceholderText("Monto Gasto ($) Ej: 2.50")
        layout_gasto.addWidget(self.txt_monto_gasto)

        layout_cat = QHBoxLayout()
        self.combo_categoria = QComboBox()
        self.actualizar_combo_categorias()
        layout_cat.addWidget(self.combo_categoria)

        btn_add_cat = QPushButton("➕")
        btn_add_cat.setToolTip("Agregar categoría personalizada")
        btn_add_cat.setFixedWidth(30)
        btn_add_cat.setObjectName("btn_add_cat")
        btn_add_cat.clicked.connect(self.agregar_categoria_dialogo)
        layout_cat.addWidget(btn_add_cat)

        btn_del_cat = QPushButton("➖")
        btn_del_cat.setToolTip("Eliminar categoría seleccionada")
        btn_del_cat.setFixedWidth(30)
        btn_del_cat.setObjectName("btn_del_cat")
        btn_del_cat.clicked.connect(self.eliminar_categoria_dialogo)
        layout_cat.addWidget(btn_del_cat)

        layout_gasto.addLayout(layout_cat)

        self.txt_desc_gasto = QLineEdit()
        self.txt_desc_gasto.setPlaceholderText("Descripción (Ej: Café de la tarde)")
        layout_gasto.addWidget(self.txt_desc_gasto)

        btn_guardar_gasto = QPushButton("💸 Registrar Gasto")
        btn_guardar_gasto.setObjectName("btn_guardar")
        btn_guardar_gasto.clicked.connect(self.agregar_gasto)
        layout_gasto.addWidget(btn_guardar_gasto)

        self.tabs.addTab(tab_gasto, "💸 Registrar Gasto")

        tab_ingreso = QWidget()
        layout_ingreso = QVBoxLayout(tab_ingreso)

        self.txt_monto_ingreso = QLineEdit()
        self.txt_monto_ingreso.setPlaceholderText("Monto Ingreso ($) Ej: 100.00")
        layout_ingreso.addWidget(self.txt_monto_ingreso)

        self.txt_desc_ingreso = QLineEdit()
        self.txt_desc_ingreso.setPlaceholderText("Origen (Ej: Salario quincenal)")
        layout_ingreso.addWidget(self.txt_desc_ingreso)

        btn_guardar_ingreso = QPushButton("💵 Cargar Presupuesto")
        btn_guardar_ingreso.setObjectName("btn_ingreso")
        btn_guardar_ingreso.clicked.connect(self.agregar_ingreso)
        layout_ingreso.addWidget(btn_guardar_ingreso)

        self.tabs.addTab(tab_ingreso, "💵 Cargar Presupuesto")
        layout_form.addWidget(self.tabs)

        btn_reset = QPushButton("🗑️ Reiniciar Todo")
        btn_reset.setObjectName("btn_reset")
        btn_reset.clicked.connect(self.reiniciar_todo)
        layout_form.addWidget(btn_reset)

        layout_medio.addWidget(frame_form, stretch=5)

        frame_metrics = QFrame()
        frame_metrics.setObjectName("card")
        layout_metrics = QVBoxLayout(frame_metrics)

        self.lbl_presupuesto = QLabel("Presupuesto Total: $0.00")
        self.lbl_gastos = QLabel("Gastos Totales: $0.00")
        self.lbl_disponible = QLabel("Disponible: $0.00")
        self.lbl_disponible.setObjectName("lbl_disponible")
        self.lbl_hormiga = QLabel("🚨 Fuga Hormiga: $0.00 (0.0%)")
        self.lbl_hormiga.setObjectName("lbl_hormiga")

        layout_metrics.addWidget(self.lbl_presupuesto)
        layout_metrics.addWidget(self.lbl_gastos)
        layout_metrics.addWidget(self.lbl_disponible)
        layout_metrics.addWidget(self.lbl_hormiga)

        btn_graficos = QPushButton("📊 Ver Gráficos de Análisis")
        btn_graficos.setObjectName("btn_graficos")
        btn_graficos.clicked.connect(self.abrir_graficos)
        layout_metrics.addWidget(btn_graficos)

        layout_medio.addWidget(frame_metrics, stretch=5)
        layout_principal.addLayout(layout_medio)

        self.tabla = QTableWidget()
        self.tabla.setColumnCount(5)
        self.tabla.setHorizontalHeaderLabels(["Fecha", "Categoría", "Descripción", "Monto", "Acción"])
        
        header = self.tabla.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        
        layout_principal.addWidget(self.tabla)

    def actualizar_combo_categorias(self):
        self.combo_categoria.clear()
        self.combo_categoria.addItems(self.gestor.categorias)

    def agregar_categoria_dialogo(self):
        nueva_cat, ok = QInputDialog.getText(self, "Nueva Categoría", "Nombre de la categoría:")
        if ok and nueva_cat.strip():
            nombre_cat = nueva_cat.strip()
            if self.gestor.agregar_categoria_personalizada(nombre_cat):
                self.actualizar_combo_categorias()
                self.combo_categoria.setCurrentText(nombre_cat)
                QMessageBox.information(self, "Éxito", f"Categoría '{nombre_cat}' agregada.")
            else:
                QMessageBox.warning(self, "Atención", "La categoría ya existe.")

    def eliminar_categoria_dialogo(self):
        cat_actual = self.combo_categoria.currentText()
        if not cat_actual:
            return
        respuesta = QMessageBox.question(
            self, "Eliminar Categoría",
            f"¿Deseas eliminar la categoría '{cat_actual}' de la lista?",
            QMessageBox.Yes | QMessageBox.No
        )
        if respuesta == QMessageBox.Yes:
            if self.gestor.eliminar_categoria_personalizada(cat_actual):
                self.actualizar_combo_categorias()
                QMessageBox.information(self, "Eliminada", "Categoría eliminada.")

    def agregar_gasto(self):
        monto_str = self.txt_monto_gasto.text().strip()
        desc = self.txt_desc_gasto.text().strip()
        categoria = self.combo_categoria.currentText()

        if not monto_str or not desc:
            QMessageBox.warning(self, "Atención", "Ingresa un monto y una descripción.")
            return

        try:
            monto = float(monto_str)
            if monto <= 0:
                QMessageBox.warning(self, "Atención", "El monto debe ser positivo.")
                return
        except ValueError:
            QMessageBox.critical(self, "Error", "Ingresa un número válido.")
            return

        self.gestor.agregar_transaccion(monto, categoria, desc, es_ingreso=False)
        self.txt_monto_gasto.clear()
        self.txt_desc_gasto.clear()
        self.actualizar_interfaz()

    def agregar_ingreso(self):
        monto_str = self.txt_monto_ingreso.text().strip()
        desc = self.txt_desc_ingreso.text().strip() or "Ingreso / Presupuesto"

        if not monto_str:
            QMessageBox.warning(self, "Atención", "Ingresa un monto.")
            return

        try:
            monto = float(monto_str)
            if monto <= 0:
                QMessageBox.warning(self, "Atención", "El monto debe ser positivo.")
                return
        except ValueError:
            QMessageBox.critical(self, "Error", "Ingresa un número válido.")
            return

        self.gestor.agregar_transaccion(monto, "💵 Ingreso / Presupuesto", desc, es_ingreso=True)
        self.txt_monto_ingreso.clear()
        self.txt_desc_ingreso.clear()
        self.actualizar_interfaz()

    def eliminar_registro(self, row_index: int):
        respuesta = QMessageBox.question(
            self, "Confirmar",
            "¿Deseas eliminar este registro de manera permanente?",
            QMessageBox.Yes | QMessageBox.No
        )
        if respuesta == QMessageBox.Yes:
            self.gestor.eliminar_transaccion_por_index(row_index)
            self.actualizar_interfaz()

    def abrir_graficos(self):
        dialog = VentanaGraficos(self.gestor, self)
        dialog.exec_()

    def actualizar_interfaz(self):
        presupuesto = self.gestor.obtener_presupuesto_total()
        gastos = self.gestor.obtener_gastos_totales()
        disponible = self.gestor.obtener_disponible()
        hormiga = self.gestor.obtener_fuga_hormiga()

        porcentaje = (hormiga / presupuesto * 100) if presupuesto > 0 else 0.0

        self.lbl_presupuesto.setText(f"Presupuesto Total: ${presupuesto:.2f}")
        self.lbl_gastos.setText(f"Gastos Totales: ${gastos:.2f}")
        
        if disponible < 0:
            self.lbl_disponible.setText(f"Disponible: ${disponible:.2f} (En Déficit)")
            self.lbl_disponible.setStyleSheet("color: #f38ba8;")
        else:
            self.lbl_disponible.setText(f"Disponible: ${disponible:.2f}")
            self.lbl_disponible.setStyleSheet("color: #a6e3a1;")

        self.lbl_hormiga.setText(f"🚨 Fuga Hormiga: ${hormiga:.2f} ({porcentaje:.1f}%)")

        self.tabla.setRowCount(0)
        for row, t in enumerate(reversed(self.gestor.transacciones)):
            self.tabla.insertRow(row)
            self.tabla.setItem(row, 0, QTableWidgetItem(t["fecha"]))
            self.tabla.setItem(row, 1, QTableWidgetItem(t["categoria"].split("(")[0].strip()))
            self.tabla.setItem(row, 2, QTableWidgetItem(t["descripcion"]))
            
            monto_item = QTableWidgetItem(f"${t['monto']:.2f}")
            if t.get("es_ingreso", False) or "Ingreso" in t["categoria"]:
                monto_item.setForeground(Qt.green)
            else:
                monto_item.setForeground(Qt.red)
            self.tabla.setItem(row, 3, monto_item)

            btn_eliminar = QPushButton("❌ Eliminar")
            btn_eliminar.setObjectName("btn_eliminar_item")
            btn_eliminar.clicked.connect(lambda _, r=row: self.eliminar_registro(r))
            self.tabla.setCellWidget(row, 4, btn_eliminar)

    def reiniciar_todo(self):
        respuesta = QMessageBox.question(
            self, "Confirmación", 
            "¿Estás seguro de reiniciar todo el historial?",
            QMessageBox.Yes | QMessageBox.No
        )
        if respuesta == QMessageBox.Yes:
            self.gestor.reiniciar_datos()
            self.actualizar_interfaz()


# ==============================================================================
# ESTILOS QCSS ACTUALIZADOS (Controles Oscuros Catppuccin)
# ==============================================================================
ESTILOS_QCSS = """
QWidget {
    background-color: #1e1e2e;
    color: #cad3f5;
    font-family: 'Segoe UI', sans-serif;
    font-size: 13px;
}

#lbl_titulo {
    font-size: 18px;
    font-weight: bold;
    color: #89b4fa;
    padding: 10px;
}

QFrame#card {
    background-color: #181825;
    border-radius: 10px;
    padding: 12px;
}

/* --- ESTILOS DE CASILLAS DE ENTRADA Y SELECCIÓN --- */
QLineEdit, QComboBox {
    background-color: #24273a;
    border: 1px solid #494d64;
    border-radius: 6px;
    padding: 6px 10px;
    color: #cad3f5;
    selection-background-color: #363a4f;
    selection-color: #cad3f5;
}

QLineEdit:focus, QComboBox:focus {
    border: 1px solid #89b4fa;
}

QComboBox QAbstractItemView {
    background-color: #1e1e2e;
    color: #cad3f5;
    selection-background-color: #363a4f;
    selection-color: #cad3f5;
    border: 1px solid #494d64;
}

/* --- PESTAÑAS (TABS) --- */
QTabWidget::pane {
    border: 1px solid #363a4f;
    border-radius: 6px;
    background-color: #181825;
    top: -1px;
}

QTabBar::tab {
    background-color: #24273a;
    color: #a5adcb;
    padding: 8px 12px;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
    margin-right: 2px;
}

QTabBar::tab:selected {
    background-color: #363a4f;
    color: #cad3f5;
    font-weight: bold;
}

/* --- BOTONES --- */
QPushButton#btn_add_cat {
    background-color: #89b4fa;
    color: #181825;
    font-weight: bold;
    border-radius: 6px;
}

QPushButton#btn_del_cat {
    background-color: #ed8796;
    color: #181825;
    font-weight: bold;
    border-radius: 6px;
}

QPushButton#btn_guardar {
    background-color: #ed8796;
    color: #181825;
    font-weight: bold;
    border-radius: 6px;
    padding: 8px;
}

QPushButton#btn_ingreso {
    background-color: #a6da95;
    color: #181825;
    font-weight: bold;
    border-radius: 6px;
    padding: 8px;
}

QPushButton#btn_graficos {
    background-color: #89b4fa;
    color: #181825;
    font-weight: bold;
    border-radius: 6px;
    padding: 8px;
    margin-top: 10px;
}

QPushButton#btn_reset {
    background-color: #363a4f;
    color: #cad3f5;
    border-radius: 6px;
    padding: 6px;
}

QPushButton#btn_eliminar_item {
    background-color: #24273a;
    color: #ed8796;
    border-radius: 4px;
    padding: 3px 8px;
    font-size: 11px;
}

QPushButton#btn_eliminar_item:hover {
    background-color: #ed8796;
    color: #181825;
}

/* --- ETIQUETAS DE RESUMEN --- */
#lbl_disponible {
    font-size: 16px;
    font-weight: bold;
    color: #a6da95;
}

#lbl_hormiga {
    font-size: 14px;
    font-weight: bold;
    color: #f5a97f;
}

/* --- TABLA DE REGISTROS --- */
QTableWidget {
    background-color: #181825;
    gridline-color: #363a4f;
    border-radius: 8px;
}

QHeaderView::section {
    background-color: #24273a;
    color: #cad3f5;
    font-weight: bold;
    padding: 6px;
    border: none;
}
"""

def main():
    app = QApplication(sys.argv)
    app.setStyleSheet(ESTILOS_QCSS)

    gestor = GestorGastos()
    ventana = VentanaPrincipal(gestor)
    ventana.show()

    sys.exit(app.exec_())

if __name__ == "__main__":
    main()