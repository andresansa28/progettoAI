from html import escape
from zipfile import ZIP_DEFLATED, ZipFile

from config import DAYS, SHIFT_NAMES


WEEKDAY_NAMES = [
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
    "Sunday",
]


def _cell_reference(row_index, column_index):
    column_name = ""
    current = column_index

    while current:
        current, remainder = divmod(current - 1, 26)
        column_name = chr(65 + remainder) + column_name

    return f"{column_name}{row_index}"


def _worksheet_xml(rows):
    xml_rows = []

    for row_index, row in enumerate(rows, start=1):
        cells = []
        for column_index, value in enumerate(row, start=1):
            reference = _cell_reference(row_index, column_index)
            text = escape(str(value))
            cells.append(
                f'<c r="{reference}" t="inlineStr"><is><t>{text}</t></is></c>'
            )

        xml_rows.append(f'<row r="{row_index}">{"".join(cells)}</row>')

    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
        '<sheetData>'
        f'{"".join(xml_rows)}'
        "</sheetData>"
        "</worksheet>"
    )


def _content_types_xml():
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
        '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
        '<Default Extension="xml" ContentType="application/xml"/>'
        '<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>'
        '<Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>'
        '<Override PartName="/xl/worksheets/sheet2.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>'
        "</Types>"
    )


def _root_relationships_xml():
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>'
        "</Relationships>"
    )


def _workbook_xml():
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
        'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
        "<sheets>"
        '<sheet name="Calendar" sheetId="1" r:id="rId1"/>'
        '<sheet name="By worker" sheetId="2" r:id="rId2"/>'
        "</sheets>"
        "</workbook>"
    )


def _workbook_relationships_xml():
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/>'
        '<Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet2.xml"/>'
        "</Relationships>"
    )


def _assigned_workers_for_shift(solver, shifts, lavoratori, day_index, shift_id):
    workers = []

    for worker_id in range(lavoratori):
        if solver.value(shifts[(worker_id, day_index, shift_id)]):
            workers.append(f"Worker {worker_id}")

    return ", ".join(workers)


def _calendar_rows(solver, shifts, lavoratori, giorni, turni):
    rows = [["Date", "Weekday"] + [SHIFT_NAMES[shift_id] for shift_id in range(turni)]]

    for day_index, current_day in enumerate(DAYS[:giorni]):
        row = [
            current_day.isoformat(),
            WEEKDAY_NAMES[current_day.weekday()],
        ]

        for shift_id in range(turni):
            row.append(
                _assigned_workers_for_shift(
                    solver, shifts, lavoratori, day_index, shift_id
                )
            )

        rows.append(row)

    return rows


def _worker_rows(solver, shifts, lavoratori, giorni, turni):
    rows = [["Worker", "Date", "Weekday", "Shift"]]

    for worker_id in range(lavoratori):
        for day_index, current_day in enumerate(DAYS[:giorni]):
            assigned_shift_names = []

            for shift_id in range(turni):
                if solver.value(shifts[(worker_id, day_index, shift_id)]):
                    assigned_shift_names.append(SHIFT_NAMES[shift_id])

            rows.append(
                [
                    f"Worker {worker_id}",
                    current_day.isoformat(),
                    WEEKDAY_NAMES[current_day.weekday()],
                    ", ".join(assigned_shift_names) or "Rest",
                ]
            )

    return rows


def export_schedule_to_excel(
    solver,
    shifts,
    lavoratori,
    giorni,
    turni,
    output_path="calendario_turni_1.xlsx",
):
    calendar_rows = _calendar_rows(solver, shifts, lavoratori, giorni, turni)
    worker_rows = _worker_rows(solver, shifts, lavoratori, giorni, turni)

    with ZipFile(output_path, "w", ZIP_DEFLATED) as xlsx_file:
        xlsx_file.writestr("[Content_Types].xml", _content_types_xml())
        xlsx_file.writestr("_rels/.rels", _root_relationships_xml())
        xlsx_file.writestr("xl/workbook.xml", _workbook_xml())
        xlsx_file.writestr("xl/_rels/workbook.xml.rels", _workbook_relationships_xml())
        xlsx_file.writestr("xl/worksheets/sheet1.xml", _worksheet_xml(calendar_rows))
        xlsx_file.writestr("xl/worksheets/sheet2.xml", _worksheet_xml(worker_rows))

    return output_path
