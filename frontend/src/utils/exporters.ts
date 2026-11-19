export interface ExportColumn {
  header: string;
  key: string;
}

function triggerDownload(blob: Blob, filename: string): void {
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = filename;
  document.body.appendChild(anchor);
  anchor.click();
  document.body.removeChild(anchor);
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}

export async function exportToExcel(
  title: string,
  columns: ExportColumn[],
  rows: Array<Record<string, unknown>>,
  filenameBase: string
): Promise<void> {
  const { default: ExcelJS } = await import("exceljs");
  const wb = new ExcelJS.Workbook();
  wb.creator = "SAJONA ADE";
  const ws = wb.addWorksheet(title.slice(0, 30));

  ws.columns = columns.map((c) => ({ header: c.header, key: c.key, width: 20 }));
  ws.getRow(1).font = { bold: true };
  for (const row of rows) {
    const normalized: Record<string, string | number> = {};
    for (const col of columns) {
      const val = row[col.key];
      normalized[col.key] = val === null || val === undefined ? "" : String(val);
    }
    ws.addRow(normalized);
  }
  const buffer = await wb.xlsx.writeBuffer();
  const blob = new Blob([buffer], {
    type: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
  });
  triggerDownload(blob, `${filenameBase}.xlsx`);
}

export function exportToText(
  title: string,
  columns: ExportColumn[],
  rows: Array<Record<string, unknown>>,
  filenameBase: string
): void {
  const lines: string[] = [
    `SAJONA ADE - ${title}`,
    `Generado: ${new Date().toLocaleString("es-CO")}`,
    "=".repeat(72),
    columns.map((c) => c.header).join("\t|\t"),
    "-".repeat(72),
  ];
  for (const row of rows) {
    lines.push(
      columns
        .map((c) => {
          const val = row[c.key];
          return val === null || val === undefined ? "" : String(val);
        })
        .join("\t|\t")
    );
  }
  const blob = new Blob([lines.join("\n")], { type: "text/plain;charset=utf-8" });
  triggerDownload(blob, `${filenameBase}.txt`);
}

export async function exportToPdf(
  title: string,
  columns: ExportColumn[],
  rows: Array<Record<string, unknown>>,
  filenameBase: string
): Promise<void> {
  const [{ default: jsPDF }, { default: autoTable }] = await Promise.all([
    import("jspdf"),
    import("jspdf-autotable"),
  ]);
  const doc = new jsPDF({
    orientation: rows.length > 0 && columns.length > 5 ? "landscape" : "portrait",
  });
  doc.setFontSize(14);
  doc.text(`SAJONA ADE — ${title}`, 14, 16);
  doc.setFontSize(9);
  doc.text(`Generado: ${new Date().toLocaleString("es-CO")} (Trazabilidad Lotes)`, 14, 22);

  autoTable(doc, {
    startY: 28,
    head: [columns.map((c) => c.header)],
    body: rows.map((r) =>
      columns.map((c) => {
        const val = r[c.key];
        return val === null || val === undefined ? "" : String(val);
      })
    ),
    styles: { fontSize: 8, cellPadding: 2 },
    headStyles: { fillColor: [153, 27, 27], textColor: 255 },
  });

  doc.save(`${filenameBase}.pdf`);
}
