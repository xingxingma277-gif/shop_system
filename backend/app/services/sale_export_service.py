from __future__ import annotations

from io import BytesIO
from pathlib import Path
import html

from sqlmodel import Session

from app.core.errors import NotFoundError
from app.models import Sale
from app.services import sale_service


def _export_spreadsheet_xml(sale) -> bytes:
    rows = []
    rows.append('<Row><Cell><Data ss:Type="String">销售清单</Data></Cell></Row>')
    rows.append(f'<Row><Cell><Data ss:Type="String">单号</Data></Cell><Cell><Data ss:Type="String">{html.escape(sale.sale_no)}</Data></Cell></Row>')
    rows.append(f'<Row><Cell><Data ss:Type="String">日期</Data></Cell><Cell><Data ss:Type="String">{html.escape(sale.sale_date.isoformat().replace("+00:00", "Z"))}</Data></Cell></Row>')
    rows.append(f'<Row><Cell><Data ss:Type="String">客户</Data></Cell><Cell><Data ss:Type="String">{html.escape(sale.customer_name)}</Data></Cell></Row>')
    rows.append('<Row/>')
    rows.append('<Row><Cell><Data ss:Type="String">序号</Data></Cell><Cell><Data ss:Type="String">商品</Data></Cell><Cell><Data ss:Type="String">SKU</Data></Cell><Cell><Data ss:Type="String">单位</Data></Cell><Cell><Data ss:Type="String">数量</Data></Cell><Cell><Data ss:Type="String">单价</Data></Cell><Cell><Data ss:Type="String">金额</Data></Cell></Row>')
    for idx, it in enumerate(sale.items, start=1):
        rows.append(
            f'<Row><Cell><Data ss:Type="Number">{idx}</Data></Cell>'
            f'<Cell><Data ss:Type="String">{html.escape(it.product_name)}</Data></Cell>'
            f'<Cell><Data ss:Type="String">{html.escape(it.sku or "")}</Data></Cell>'
            f'<Cell><Data ss:Type="String">{html.escape(it.unit or "")}</Data></Cell>'
            f'<Cell><Data ss:Type="Number">{float(it.qty)}</Data></Cell>'
            f'<Cell><Data ss:Type="Number">{float(it.unit_price)}</Data></Cell>'
            f'<Cell><Data ss:Type="Number">{float(it.line_total)}</Data></Cell></Row>'
        )
    rows.append(f'<Row><Cell><Data ss:Type="String">合计</Data></Cell><Cell/><Cell/><Cell/><Cell/><Cell/><Cell><Data ss:Type="Number">{float(sale.total_amount)}</Data></Cell></Row>')

    content = f'''<?xml version="1.0"?>
<?mso-application progid="Excel.Sheet"?>
<Workbook xmlns="urn:schemas-microsoft-com:office:spreadsheet"
 xmlns:o="urn:schemas-microsoft-com:office:office"
 xmlns:x="urn:schemas-microsoft-com:office:excel"
 xmlns:ss="urn:schemas-microsoft-com:office:spreadsheet">
 <Worksheet ss:Name="销售清单">
  <Table>
   {''.join(rows)}
  </Table>
 </Worksheet>
</Workbook>'''
    return content.encode('utf-8')


def _try_openpyxl_export(sale, template_path: str | None) -> bytes | None:
    try:
        from openpyxl import Workbook, load_workbook
    except Exception:
        return None

    if template_path and Path(template_path).exists():
        wb = load_workbook(template_path)
    else:
        wb = Workbook()
        ws = wb.active
        ws.title = "销售清单"
        ws["A1"] = "销售清单"

    ws = wb.active
    # replace title and placeholders
    for row in ws.iter_rows():
        for cell in row:
            if isinstance(cell.value, str) and "报价单" in cell.value:
                cell.value = cell.value.replace("报价单", "销售清单")
            if isinstance(cell.value, str):
                cell.value = (
                    cell.value
                    .replace("{{title}}", "销售清单")
                    .replace("{{sale_no}}", sale.sale_no)
                    .replace("{{sale_date}}", sale.sale_date.isoformat().replace("+00:00", "Z"))
                    .replace("{{customer_name}}", sale.customer_name)
                    .replace("{{total_amount}}", f"{sale.total_amount:.2f}")
                )

    # label fill
    for r in range(1, min(ws.max_row + 1, 50)):
        key = str(ws.cell(r, 1).value or "").strip()
        if key in {"单号", "订单编号"}:
            ws.cell(r, 2, sale.sale_no)
        elif key in {"日期", "开单日期"}:
            ws.cell(r, 2, sale.sale_date.isoformat().replace("+00:00", "Z"))
        elif key in {"客户", "客户名称"}:
            ws.cell(r, 2, sale.customer_name)
        elif key in {"合计", "总计"}:
            ws.cell(r, 2, float(sale.total_amount))

    start = max(12, ws.max_row + 2)
    for idx, it in enumerate(sale.items, start=1):
        row = start + idx - 1
        ws.cell(row, 1, idx)
        ws.cell(row, 2, it.product_name)
        ws.cell(row, 3, it.sku or "")
        ws.cell(row, 4, it.unit or "")
        ws.cell(row, 5, float(it.qty))
        ws.cell(row, 6, float(it.unit_price))
        ws.cell(row, 7, float(it.line_total))

    bio = BytesIO()
    wb.save(bio)
    return bio.getvalue()


def export_sale_excel(session: Session, *, sale_id: int, template_path: str | None = None):
    exists = session.get(Sale, sale_id)
    if not exists:
        raise NotFoundError("单据不存在")
    sale = sale_service.get_sale(session, sale_id)

    content = _try_openpyxl_export(sale, template_path)
    if content is not None:
        return content, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', 'xlsx'

    # fallback to Excel-readable XML when openpyxl is unavailable in runtime
    content = _export_spreadsheet_xml(sale)
    return content, 'application/vnd.ms-excel', 'xml'
