from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from io import BytesIO

# ─── Excel Styles ────────────────────────────────────────────────────────────

HEADER_FONT = Font(name="Calibri", bold=True, color="FFFFFF", size=11)
HEADER_FILL = PatternFill(start_color="2F5496", end_color="2F5496", fill_type="solid")
HEADER_ALIGNMENT = Alignment(horizontal="center", vertical="center", wrap_text=True)

DATA_FONT = Font(name="Calibri", size=10)
DATA_ALIGNMENT = Alignment(horizontal="center", vertical="center")

THIN_BORDER = Border(
    left=Side(style="thin"),
    right=Side(style="thin"),
    top=Side(style="thin"),
    bottom=Side(style="thin"),
)

def apply_header_style(ws, row, num_cols):
    for col in range(1, num_cols + 1):
        cell = ws.cell(row=row, column=col)
        cell.font = HEADER_FONT
        cell.fill = HEADER_FILL
        cell.alignment = HEADER_ALIGNMENT
        cell.border = THIN_BORDER

def apply_data_style(cell, center=True):
    cell.font = DATA_FONT
    cell.alignment = DATA_ALIGNMENT if center else Alignment(horizontal="left", vertical="center")
    cell.border = THIN_BORDER

def auto_width(ws):
    for col_cells in ws.columns:
        max_length = 0
        col_letter = get_column_letter(col_cells[0].column)
        for cell in col_cells:
            if cell.value:
                length = len(str(cell.value))
                if length > max_length:
                    max_length = length
        ws.column_dimensions[col_letter].width = min(max(max_length + 3, 10), 40)

def generate_user_report(usuario, fichajes, ausencias):
    """
    Genera un reporte Excel con la información de un usuario.
    fichajes: lista de objetos Fichaje
    ausencias: lista de objetos SolicitudAusencia
    """
    wb = Workbook()
    
    # 1. Fichajes
    ws_f = wb.active
    ws_f.title = "Fichajes"
    headers_f = ["Fecha", "Entrada", "Salida", "Pausa (min)", "Motivo"]
    ws_f.append(headers_f)
    apply_header_style(ws_f, 1, len(headers_f))
    
    for f in fichajes:
        row = [
            f.fecha.strftime("%d/%m/%Y"),
            f.hora_entrada.strftime("%H:%M") if f.hora_entrada else "",
            f.hora_salida.strftime("%H:%M") if f.hora_salida else "",
            f.pausa or 0,
            f.motivo_rectificacion or ""
        ]
        ws_f.append(row)
        for i, cell in enumerate(ws_f[ws_f.max_row], 1):
            apply_data_style(cell)
            
    auto_width(ws_f)
    
    # 2. Ausencias
    ws_a = wb.create_sheet("Ausencias")
    headers_a = ["Inicio", "Fin", "Días", "Motivo", "Estado"]
    ws_a.append(headers_a)
    apply_header_style(ws_a, 1, len(headers_a))
    
    for a in ausencias:
        row = [
            a.fecha_inicio.strftime("%d/%m/%Y"),
            a.fecha_fin.strftime("%d/%m/%Y"),
            a.dias_solicitados,
            a.motivo or "",
            a.estado
        ]
        ws_a.append(row)
        for i, cell in enumerate(ws_a[ws_a.max_row], 1):
            apply_data_style(cell)
            
    auto_width(ws_a)
    
    output = BytesIO()
    wb.save(output)
    output.seek(0)
    return output
