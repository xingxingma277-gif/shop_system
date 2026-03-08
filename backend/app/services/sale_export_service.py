from __future__ import annotations

import os
import tempfile
from pathlib import Path
from io import BytesIO
from sqlmodel import Session
from app.core.errors import NotFoundError, BadRequestError
from app.models import Sale, Customer
from app.services import sale_service


def _set_cell_value(ws, r, c, val):
    """安全地向单元格写入数据，完美兼容并保护合并单元格(MergedCell)"""
    cell = ws.cell(row=r, column=c)
    if type(cell).__name__ == 'MergedCell':
        for merged_range in ws.merged_cells.ranges:
            if cell.coordinate in merged_range:
                ws.cell(row=merged_range.min_row, column=merged_range.min_col, value=val)
                return
    else:
        cell.value = val


def export_sale_excel(session: Session, *, sale_id: int, template_path: str | None = None) -> tuple[bytes, str, str]:
    exists = session.get(Sale, sale_id)
    if not exists:
        raise NotFoundError("单据不存在")
    sale = sale_service.get_sale(session, sale_id)

    try:
        from openpyxl import Workbook, load_workbook
    except ImportError:
        raise BadRequestError("请安装 openpyxl 库")

    current_dir = Path(__file__).resolve().parent
    backend_dir = current_dir.parent.parent
    root_dir = backend_dir.parent

    possible_paths = [
        Path(template_path) if template_path else None,
        backend_dir / "打印模板.xlsx",
        root_dir / "打印模板.xlsx",
        Path("打印模板.xlsx")
    ]

    path_to_use = None
    for p in possible_paths:
        if p and p.exists():
            path_to_use = p
            break

    if not path_to_use:
        raise BadRequestError("找不到【打印模板.xlsx】，请确认该文件已上传")

    wb = load_workbook(path_to_use)
    ws = wb.active

    customer = session.get(Customer, sale.customer_id) if getattr(sale, 'customer_id', None) else None
    customer_phone = getattr(sale, "contact_phone_snapshot", None)
    if not customer_phone and customer:
        customer_phone = getattr(customer, "phone", None) or getattr(customer, "mobile", None) or getattr(customer,
                                                                                                          "contact_phone",
                                                                                                          None)
    customer_phone = customer_phone or "-"

    sale_date_str = sale.sale_date.strftime("%Y-%m-%d %H:%M")

    for r in range(1, 15):
        for c in range(1, 15):
            cell = ws.cell(row=r, column=c)
            if type(cell).__name__ == 'MergedCell':
                continue

            val = str(cell.value or "").strip()
            # 兼容D列与H列偏移填入
            if val in ["单号：", "单号"]:
                _set_cell_value(ws, r, c + 2, sale.sale_no)
            elif val in ["日期：", "日期"]:
                _set_cell_value(ws, r, c + 2, sale_date_str)
            elif val in ["客户名称：", "客户名称", "客户"]:
                _set_cell_value(ws, r, c + 2, sale.customer_name)
            elif val in ["电话：", "电话", "联系电话：", "联系电话"]:
                _set_cell_value(ws, r, c + 2, customer_phone)

    start_row = 12
    col_map = {}
    for r in range(1, 20):
        for c in range(1, 15):
            cell = ws.cell(row=r, column=c)
            if type(cell).__name__ == 'MergedCell':
                continue
            val = str(cell.value or "").strip()
            if val == "序号":
                col_map['index'] = c
                start_row = r + 1
            elif val in ["名称", "品名", "商品名称"]:
                col_map['name'] = c
            elif val in ["规格", "SKU"]:
                col_map['sku'] = c
            elif val == "数量":
                col_map['qty'] = c
            elif val == "单位":
                col_map['unit'] = c
            elif val == "单价":
                col_map['price'] = c

        if 'index' in col_map and 'name' in col_map:
            break

    for idx, it in enumerate(sale.items):
        r = start_row + idx
        if 'index' in col_map: _set_cell_value(ws, r, col_map['index'], idx + 1)
        if 'name' in col_map: _set_cell_value(ws, r, col_map['name'], it.product_name)
        if 'sku' in col_map: _set_cell_value(ws, r, col_map['sku'], it.sku or "")
        if 'qty' in col_map: _set_cell_value(ws, r, col_map['qty'], float(it.qty))
        if 'unit' in col_map: _set_cell_value(ws, r, col_map['unit'], it.unit or "")
        if 'price' in col_map: _set_cell_value(ws, r, col_map['price'], float(it.unit_price))

    bio = BytesIO()
    wb.save(bio)
    return bio.getvalue(), 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', 'xlsx'


def export_sale_pdf(session: Session, *, sale_id: int, template_path: str | None = None) -> bytes:
    """导出 PDF 功能：利用系统的 Excel 软件将填好的数据直接转换为完美的 PDF"""
    excel_bytes, _, _ = export_sale_excel(session, sale_id=sale_id, template_path=template_path)

    try:
        import win32com.client
        import pythoncom
    except ImportError:
        raise BadRequestError("请在 backend 目录下运行 pip install pywin32 以支持 PDF 转换")

    # 将数据写入系统临时文件
    fd_xlsx, temp_xlsx = tempfile.mkstemp(suffix=".xlsx")
    with os.fdopen(fd_xlsx, 'wb') as f:
        f.write(excel_bytes)

    temp_pdf = temp_xlsx.replace(".xlsx", ".pdf")

    try:
        pythoncom.CoInitialize()
        # 必须使用 DispatchEx，它会强制启动一个全新的 Excel 进程，防止和您当前正在打开的 Excel 互相卡死干扰
        excel = win32com.client.DispatchEx("Excel.Application")
        excel.Visible = False
        excel.DisplayAlerts = False

        abs_xlsx = os.path.abspath(temp_xlsx)
        abs_pdf = os.path.abspath(temp_pdf)

        wb = excel.Workbooks.Open(abs_xlsx)
        wb.ExportAsFixedFormat(0, abs_pdf)  # 0 代表输出为 PDF
        wb.Close(False)
        excel.Quit()
    except Exception as e:
        raise BadRequestError(f"PDF转换失败，请确认后台 Excel 进程未卡死: {str(e)}")
    finally:
        pythoncom.CoUninitialize()

    # 读取转换好的 PDF 数据，并且立刻【清理销毁临时垃圾文件】，保护服务器硬盘
    try:
        with open(temp_pdf, "rb") as f:
            pdf_bytes = f.read()
    except FileNotFoundError:
        raise BadRequestError("未能成功生成 PDF 文件")
    finally:
        if os.path.exists(temp_xlsx):
            try:
                os.remove(temp_xlsx)
            except:
                pass
        if os.path.exists(temp_pdf):
            try:
                os.remove(temp_pdf)
            except:
                pass

    return pdf_bytes