import io
import csv
from datetime import datetime
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from sqlalchemy.orm import Session

from backend.app.models.models import Reserva, ProdutoPrincipal, Mimo, Numero, Comprovante


def generate_reservations_export(db: Session, status_filter: str = None, format_type: str = "csv") -> tuple[bytes, str, str]:
    """
    Exports reservations to CSV or Excel.
    """
    query = db.query(Reserva).join(Numero, Reserva.numero_id == Numero.id).order_by(Numero.numero.asc())
    if status_filter:
        query = query.filter(Reserva.status == status_filter)
    
    reservas = query.all()

    headers = [
        "Número", "Status", "Nome Convidado", "WhatsApp", "Nome Público Autorizado",
        "Presente Principal", "Forma Presente", "Preço Presente (R$)", "Status Comprovante Presente",
        "Mimo Complementar", "Forma Mimo", "Preço Mimo (R$)", "Status Comprovante Mimo",
        "Total Pix (R$)", "Data Reserva", "Prazo Expiração", "Data Confirmação"
    ]

    rows = []
    for r in reservas:
        num_str = f"{r.numero.numero:02d}"
        pres_comp = next((c for c in r.comprovantes if c.tipo_item == "presente"), None)
        mimo_comp = next((c for c in r.comprovantes if c.tipo_item == "mimo"), None)

        rows.append([
            num_str,
            r.status.capitalize(),
            r.nome_convidado,
            r.whatsapp,
            "Sim" if r.autoriza_nome_publico else "Não",
            r.numero.produto_principal.nome if r.numero.produto_principal else "N/A",
            "Amazon" if r.forma_presente == "amazon" else "Loja Física" if r.forma_presente == "local" else "Pix",
            f"{r.preco_presente_reserva:.2f}",
            pres_comp.status.replace("_", " ").title() if pres_comp else "Pendente",
            r.mimo.nome if r.mimo else "N/A",
            "Amazon" if r.forma_mimo == "amazon" else "Loja Física" if r.forma_mimo == "local" else "Pix",
            f"{r.preco_mimo_reserva:.2f}",
            mimo_comp.status.replace("_", " ").title() if mimo_comp else "Pendente",
            f"{r.valor_pix_total:.2f}",
            r.criada_em.strftime("%d/%m/%Y %H:%M") if r.criada_em else "",
            r.expira_em.strftime("%d/%m/%Y %H:%M") if r.expira_em else "",
            r.confirmada_em.strftime("%d/%m/%Y %H:%M") if r.confirmada_em else "",
        ])

    filename_prefix = f"reservas_{status_filter}" if status_filter else "todas_as_reservas"
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")

    if format_type == "csv":
        output = io.StringIO()
        writer = csv.writer(output, delimiter=";")
        writer.writerow(headers)
        writer.writerows(rows)
        return output.getvalue().encode("utf-8-sig"), f"{filename_prefix}_{timestamp}.csv", "text/csv"

    # Excel format
    wb = Workbook()
    ws = wb.active
    ws.title = "Reservas"

    header_font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
    header_fill = PatternFill(start_color="42677D", end_color="42677D", fill_type="solid")
    center_align = Alignment(horizontal="center", vertical="center")

    ws.append(headers)
    for cell in ws[1]:
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = center_align

    for row_data in rows:
        ws.append(row_data)

    # Adjust column widths
    for col in ws.columns:
        max_len = max(len(str(cell.value or "")) for cell in col)
        col_letter = col[0].column_letter
        ws.column_dimensions[col_letter].width = max(max_len + 3, 12)

    excel_buffer = io.BytesIO()
    wb.save(excel_buffer)
    excel_buffer.seek(0)
    return excel_buffer.getvalue(), f"{filename_prefix}_{timestamp}.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


def generate_pix_report(db: Session, format_type: str = "csv") -> tuple[bytes, str, str]:
    """
    Exports detailed Pix contribution report.
    """
    reservas = (
        db.query(Reserva)
        .join(Numero, Reserva.numero_id == Numero.id)
        .filter(Reserva.valor_pix_total > 0)
        .order_by(Reserva.status.asc(), Numero.numero.asc())
        .all()
    )

    headers = [
        "Número", "Status Geral", "Convidado", "WhatsApp",
        "Item(ns) em Pix", "Valor Total Pix (R$)",
        "Comprovante Presente", "Comprovante Mimo",
        "Data da Reserva", "Data da Confirmação"
    ]

    rows = []
    total_confirmado = 0.0
    total_pendente = 0.0

    for r in reservas:
        itens_pix = []
        if r.forma_presente == "pix":
            itens_pix.append(f"Presente (R$ {r.preco_presente_reserva:.2f})")
        if r.forma_mimo == "pix":
            itens_pix.append(f"Mimo (R$ {r.preco_mimo_reserva:.2f})")

        if r.status == "confirmada":
            total_confirmado += r.valor_pix_total
        elif r.status == "reservada":
            total_pendente += r.valor_pix_total

        pres_comp = next((c for c in r.comprovantes if c.tipo_item == "presente"), None)
        mimo_comp = next((c for c in r.comprovantes if c.tipo_item == "mimo"), None)

        rows.append([
            f"{r.numero.numero:02d}",
            r.status.capitalize(),
            r.nome_convidado,
            r.whatsapp,
            " + ".join(itens_pix),
            f"{r.valor_pix_total:.2f}",
            pres_comp.status.replace("_", " ").title() if pres_comp else "Pendente",
            mimo_comp.status.replace("_", " ").title() if mimo_comp else "Pendente",
            r.criada_em.strftime("%d/%m/%Y %H:%M") if r.criada_em else "",
            r.confirmada_em.strftime("%d/%m/%Y %H:%M") if r.confirmada_em else "",
        ])

    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    filename = f"relatorio_pix_{timestamp}"

    if format_type == "csv":
        output = io.StringIO()
        writer = csv.writer(output, delimiter=";")
        writer.writerow(headers)
        writer.writerows(rows)
        writer.writerow([])
        writer.writerow(["", "", "", "TOTAL PIX CONFIRMADO:", f"R$ {total_confirmado:.2f}"])
        writer.writerow(["", "", "", "TOTAL PIX PENDENTE (RESERVAS):", f"R$ {total_pendente:.2f}"])
        return output.getvalue().encode("utf-8-sig"), f"{filename}.csv", "text/csv"

    wb = Workbook()
    ws = wb.active
    ws.title = "Relatório Pix"

    header_font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
    header_fill = PatternFill(start_color="A9B8A0", end_color="A9B8A0", fill_type="solid")

    ws.append(headers)
    for cell in ws[1]:
        cell.font = header_font
        cell.fill = header_fill

    for row in rows:
        ws.append(row)

    ws.append([])
    ws.append(["", "", "", "TOTAL PIX CONFIRMADO:", f"R$ {total_confirmado:.2f}"])
    ws.append(["", "", "", "TOTAL PIX PENDENTE (RESERVAS):", f"R$ {total_pendente:.2f}"])

    for col in ws.columns:
        max_len = max(len(str(cell.value or "")) for cell in col)
        col_letter = col[0].column_letter
        ws.column_dimensions[col_letter].width = max(max_len + 3, 12)

    excel_buffer = io.BytesIO()
    wb.save(excel_buffer)
    excel_buffer.seek(0)
    return excel_buffer.getvalue(), f"{filename}.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
