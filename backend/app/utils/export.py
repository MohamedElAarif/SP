import pandas as pd
import json
import csv
import io
from typing import Dict, List, Any
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from fastapi.responses import StreamingResponse

def export_to_csv(data: Dict[str, Any]) -> StreamingResponse:
    """Export scraped data to CSV format"""
    # Flatten the data for CSV export
    rows = []
    max_length = max(len(values) if isinstance(values, list) else 1 for values in data.values() if values != "_metadata")
    
    for i in range(max_length):
        row = {}
        for key, values in data.items():
            if key == "_metadata":
                continue
            if isinstance(values, list):
                row[key] = values[i] if i < len(values) else ""
            else:
                row[key] = values if i == 0 else ""
        rows.append(row)
    
    # Create CSV
    output = io.StringIO()
    if rows:
        fieldnames = list(rows[0].keys())
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    
    # Return as streaming response
    output.seek(0)
    return StreamingResponse(
        io.BytesIO(output.getvalue().encode('utf-8')),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=scraped_data.csv"}
    )

def export_to_json(data: Dict[str, Any]) -> StreamingResponse:
    """Export scraped data to JSON format"""
    json_data = json.dumps(data, indent=2, default=str)
    return StreamingResponse(
        io.BytesIO(json_data.encode('utf-8')),
        media_type="application/json",
        headers={"Content-Disposition": "attachment; filename=scraped_data.json"}
    )

def export_to_pdf(data: Dict[str, Any]) -> StreamingResponse:
    """Export scraped data to PDF format"""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    story = []
    
    # Add title
    title = Paragraph("Scraped Data Report", styles['Title'])
    story.append(title)
    story.append(Spacer(1, 12))
    
    # Add metadata if available
    if "_metadata" in data:
        metadata = data["_metadata"]
        meta_text = f"URL: {metadata.get('url', 'N/A')}<br/>"
        meta_text += f"Timestamp: {metadata.get('timestamp', 'N/A')}<br/>"
        meta_text += f"Fields: {', '.join(metadata.get('scraped_fields', []))}"
        meta_para = Paragraph(meta_text, styles['Normal'])
        story.append(meta_para)
        story.append(Spacer(1, 12))
    
    # Create table data
    table_data = []
    max_length = max(len(values) if isinstance(values, list) else 1 for values in data.values() if values != "_metadata")
    
    # Add headers
    headers = [key for key in data.keys() if key != "_metadata"]
    table_data.append(headers)
    
    # Add data rows
    for i in range(max_length):
        row = []
        for key in headers:
            values = data[key]
            if isinstance(values, list):
                row.append(values[i] if i < len(values) else "")
            else:
                row.append(str(values) if i == 0 else "")
        table_data.append(row)
    
    # Create table
    if table_data:
        table = Table(table_data)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 14),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        story.append(table)
    
    # Build PDF
    doc.build(story)
    buffer.seek(0)
    
    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=scraped_data.pdf"}
    )

def export_to_excel(data: Dict[str, Any]) -> StreamingResponse:
    """Export scraped data to Excel format"""
    # Flatten the data for Excel export
    rows = []
    max_length = max(len(values) if isinstance(values, list) else 1 for values in data.values() if values != "_metadata")
    
    for i in range(max_length):
        row = {}
        for key, values in data.items():
            if key == "_metadata":
                continue
            if isinstance(values, list):
                row[key] = values[i] if i < len(values) else ""
            else:
                row[key] = values if i == 0 else ""
        rows.append(row)
    
    # Create DataFrame
    df = pd.DataFrame(rows)
    
    # Create Excel file
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Scraped Data', index=False)
    
    output.seek(0)
    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=scraped_data.xlsx"}
    )
