from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib.pdfencrypt import StandardEncryption
from reportlab.lib.styles import getSampleStyleSheet


class PDFExporter:
    """Create encrypted PDF exports of a user's credentials.

    Parameters
    ----------
    credentials : iterable
        Sequence of credential objects to include in the exported PDF.
    password : str
        Password used to encrypt the generated PDF.
    output_path : str, optional
        Destination path for the generated PDF file. The default is ``password.pdf``.
    """

    def export(self, credentials, password, output_path="password.pdf"):
        """Write a password-protected PDF export for a credential list.

        Parameters
        ----------
        credentials : iterable
            Credential objects to include in the export.
        password : str
            Password used to secure the PDF archive.
        output_path : str, optional
            File path for the exported PDF. The default is ``password.pdf``.

        Returns
        -------
        pathlib.Path
            Path to the written PDF file.

        Raises
        ------
        ValueError
            If the PDF password is empty.
        """
        if not password:
            raise ValueError("A PDF password is required")

        path = Path(output_path).expanduser()
        document = SimpleDocTemplate(
            str(path),
            pagesize=letter,
            encrypt=StandardEncryption(password, canPrint=1),
            title="Password Manager Export",
        )

        styles = getSampleStyleSheet()
        data = [[
            Paragraph("<b>Application</b>", styles["Normal"]),
            Paragraph("<b>Username</b>", styles["Normal"]),
            Paragraph("<b>Password</b>", styles["Normal"]),
            Paragraph("<b>Time Modified</b>", styles["Normal"]),
            Paragraph("<b>Date Modified</b>", styles["Normal"]),
        ]]

        data += [
            [c.application, c.username, c.password, c.time_modified, c.date_modified]
            for c in credentials
        ]

        table = Table(data, repeatRows=1)
        table.setStyle(TableStyle([
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("GRID", (0, 0), (-1, -1), 0.25, colors.black),
            ("BACKGROUND", (0, 0), (-1, 0), colors.skyblue),
        ]))

        document.build([table])
        return path
