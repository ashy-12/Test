import io
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Table, TableStyle, Spacer, KeepTogether
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from django.utils import timezone


def generate_report_card_pdf(student):
    """
    Generates an official PDF report card / transcript for a student using ReportLab.
    Returns a BytesIO buffer containing the PDF bytes.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36
    )

    styles = getSampleStyleSheet()

    # Custom styles
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=18,
        leading=22,
        alignment=TA_CENTER,
        textColor=colors.HexColor('#1e3a8a')
    )

    subtitle_style = ParagraphStyle(
        'DocSubTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=10,
        leading=14,
        alignment=TA_CENTER,
        textColor=colors.HexColor('#475569')
    )

    section_heading = ParagraphStyle(
        'SectionHeading',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=12,
        leading=16,
        textColor=colors.HexColor('#1e3a8a'),
        spaceAfter=6
    )

    cell_bold = ParagraphStyle(
        'CellBold',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=9,
        leading=12,
        textColor=colors.HexColor('#1e293b')
    )

    cell_normal = ParagraphStyle(
        'CellNormal',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=12,
        textColor=colors.HexColor('#334155')
    )

    cell_center = ParagraphStyle(
        'CellCenter',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=12,
        alignment=TA_CENTER,
        textColor=colors.HexColor('#334155')
    )

    cell_header = ParagraphStyle(
        'CellHeader',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=9,
        leading=12,
        alignment=TA_CENTER,
        textColor=colors.white
    )

    elements = []

    # 1. Institutional Header Banner
    header_content = [
        [Paragraph("INSTITUTE OF TECHNOLOGY & MANAGEMENT SCIENCES", title_style)],
        [Paragraph("OFFICIAL ACADEMIC TRANSCRIPT & REPORT CARD &bull; ACADEMIC YEAR 2025&ndash;2026", subtitle_style)],
    ]
    header_table = Table(header_content, colWidths=[540])
    header_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
        ('TOPPADDING', (0, 0), (-1, -1), 2),
    ]))
    elements.append(header_table)
    elements.append(Spacer(1, 14))

    # Divider bar
    divider = Table([['']], colWidths=[540], rowHeights=[3])
    divider.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#2563eb')),
    ]))
    elements.append(divider)
    elements.append(Spacer(1, 14))

    # 2. Student Details Section
    elements.append(Paragraph("STUDENT IDENTIFICATION", section_heading))

    enrollment_str = student.enrollment_date.strftime('%B %d, %Y') if student.enrollment_date else 'N/A'
    dob_str = student.date_of_birth.strftime('%B %d, %Y') if student.date_of_birth else 'N/A'

    student_info_data = [
        [
            Paragraph("<b>Full Name:</b>", cell_bold),
            Paragraph(student.full_name, cell_normal),
            Paragraph("<b>Roll Number:</b>", cell_bold),
            Paragraph(student.roll_number, cell_normal),
        ],
        [
            Paragraph("<b>Department / Course:</b>", cell_bold),
            Paragraph(student.course, cell_normal),
            Paragraph("<b>Enrollment Date:</b>", cell_bold),
            Paragraph(enrollment_str, cell_normal),
        ],
        [
            Paragraph("<b>Email Address:</b>", cell_bold),
            Paragraph(student.email, cell_normal),
            Paragraph("<b>Gender / DOB:</b>", cell_bold),
            Paragraph(f"{student.gender} / {dob_str}", cell_normal),
        ],
    ]

    info_table = Table(student_info_data, colWidths=[120, 150, 120, 150])
    info_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f8fafc')),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#cbd5e1')),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
    ]))
    elements.append(info_table)
    elements.append(Spacer(1, 16))

    # 3. Academic Grades Table
    elements.append(Paragraph("ACADEMIC PERFORMANCE", section_heading))

    grades = student.grades.select_related('subject').all()
    grade_table_data = [
        [
            Paragraph("Subject Code", cell_header),
            Paragraph("Subject Title", cell_header),
            Paragraph("Marks", cell_header),
            Paragraph("Max", cell_header),
            Paragraph("Score %", cell_header),
            Paragraph("Grade", cell_header),
            Paragraph("Remarks", cell_header),
        ]
    ]

    total_obtained = 0.0
    total_max = 0.0

    if grades.exists():
        for g in grades:
            pct = (float(g.marks_obtained) / float(g.max_marks) * 100) if g.max_marks > 0 else 0
            total_obtained += float(g.marks_obtained)
            total_max += float(g.max_marks)
            grade_table_data.append([
                Paragraph(g.subject.code, cell_center),
                Paragraph(g.subject.name, cell_normal),
                Paragraph(f"{g.marks_obtained:.1f}", cell_center),
                Paragraph(f"{g.max_marks:.1f}", cell_center),
                Paragraph(f"{pct:.1f}%", cell_center),
                Paragraph(f"<b>{g.grade_letter}</b>", cell_center),
                Paragraph(g.remarks or "Pass", cell_center),
            ])

        overall_pct = (total_obtained / total_max * 100) if total_max > 0 else 0
        overall_grade = 'A+' if overall_pct >= 90 else ('A' if overall_pct >= 80 else ('B' if overall_pct >= 70 else ('C' if overall_pct >= 60 else ('D' if overall_pct >= 50 else 'F'))))
        
        # Summary Row
        grade_table_data.append([
            Paragraph("<b>TOTAL / CUMULATIVE</b>", cell_bold),
            Paragraph(f"<b>{grades.count()} Subjects Evaluated</b>", cell_bold),
            Paragraph(f"<b>{total_obtained:.1f}</b>", cell_bold),
            Paragraph(f"<b>{total_max:.1f}</b>", cell_bold),
            Paragraph(f"<b>{overall_pct:.1f}%</b>", cell_bold),
            Paragraph(f"<b>{overall_grade}</b>", cell_bold),
            Paragraph("<b>Passed</b>" if overall_pct >= 50 else "<b>Needs Improvement</b>", cell_bold),
        ])
    else:
        grade_table_data.append([
            Paragraph("-", cell_center),
            Paragraph("No exam grades recorded for this student yet.", cell_normal),
            Paragraph("-", cell_center),
            Paragraph("-", cell_center),
            Paragraph("-", cell_center),
            Paragraph("-", cell_center),
            Paragraph("-", cell_center),
        ])

    grades_table = Table(grade_table_data, colWidths=[75, 160, 50, 50, 60, 50, 95])
    grades_table_style = [
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e3a8a')),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#cbd5e1')),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
    ]

    # Alternating row colors
    for r in range(1, len(grade_table_data) - (1 if grades.exists() else 0)):
        if r % 2 == 0:
            grades_table_style.append(('BACKGROUND', (0, r), (-1, r), colors.HexColor('#f8fafc')))

    if grades.exists():
        # Highlight total row
        grades_table_style.append(('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#e2e8f0')))

    grades_table.setStyle(TableStyle(grades_table_style))
    elements.append(grades_table)
    elements.append(Spacer(1, 16))

    # 4. Attendance Summary Section
    elements.append(Paragraph("ATTENDANCE RECORD", section_heading))

    att_summary = student.attendance_summary
    att_pct = att_summary['percentage']
    att_status = "ELIGIBLE (>=75%)" if att_pct >= 75 else "SHORTAGE (<75%)"
    att_status_color = colors.HexColor('#16a34a') if att_pct >= 75 else colors.HexColor('#dc2626')

    att_data = [
        [
            Paragraph("<b>Total Lectures Scheduled:</b>", cell_bold),
            Paragraph(str(att_summary['total']), cell_center),
            Paragraph("<b>Classes Attended:</b>", cell_bold),
            Paragraph(f"{att_summary['present']} (Late: {att_summary['late']})", cell_center),
        ],
        [
            Paragraph("<b>Classes Absent:</b>", cell_bold),
            Paragraph(str(att_summary['absent']), cell_center),
            Paragraph("<b>Attendance Percentage:</b>", cell_bold),
            Paragraph(f"<b>{att_pct}%</b> &mdash; {att_status}", cell_center),
        ],
    ]

    att_table = Table(att_data, colWidths=[150, 120, 150, 120])
    att_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f8fafc')),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#cbd5e1')),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
    ]))
    elements.append(att_table)
    elements.append(Spacer(1, 30))

    # 5. Signatures and Verification Block (Keep Together)
    date_now_str = timezone.now().strftime('%B %d, %Y')
    footer_data = [
        [
            Paragraph(f"Date of Issue: <b>{date_now_str}</b><br/><font size='8' color='#64748b'>System Generated Official Transcript</font>", cell_normal),
            Paragraph("<font size='8' color='#64748b'>[ OFFICIAL SEAL ]</font><br/><b>Office of the Registrar</b>", cell_center),
            Paragraph("____________________________<br/><b>Controller of Examinations</b><br/><font size='8' color='#64748b'>Authorized Signature</font>", cell_center),
        ]
    ]

    footer_table = Table(footer_data, colWidths=[180, 180, 180])
    footer_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    elements.append(KeepTogether(footer_table))

    # Build the document
    doc.build(elements)
    buffer.seek(0)
    return buffer
