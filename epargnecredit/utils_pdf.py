from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
from reportlab.platypus import Table
from reportlab.platypus import TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Image

from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.pdfbase import pdfmetrics

import os
from django.conf import settings


def generer_recu_pdf(versement):

    filepath = os.path.join(
        settings.MEDIA_ROOT,
        f"recu_{versement.numero_recu}.pdf"
    )

    doc = SimpleDocTemplate(filepath)
    elements = []

    pdfmetrics.registerFont(UnicodeCIDFont('STSong-Light'))

    styles = getSampleStyleSheet()

    elements.append(Paragraph("<b>REÇU DE VERSEMENT - YaayESS</b>", styles["Title"]))
    elements.append(Spacer(1, 0.5 * inch))

    data = [
        ["Numéro reçu", versement.numero_recu],
        ["Membre", versement.member.user.nom],
        ["Groupe", versement.member.group.nom],
        ["Montant", f"{versement.montant} FCFA"],
        ["Date", versement.date_validation.strftime("%d/%m/%Y %H:%M")],
    ]

    table = Table(data, colWidths=[200, 250])
    table.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 1, colors.grey)
    ]))

    elements.append(table)

    doc.build(elements)

    return filepath