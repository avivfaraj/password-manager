# Import packages
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib.pdfencrypt import StandardEncryption
from reportlab.lib import styles
def PDF(ls, password):

	# style = styles()
	# style.
	# Encrypt Definition - Document is printable (canPrint = 1)
	enc=StandardEncryption(password,canPrint=1)

	# Create document with encryption
	doc = SimpleDocTemplate("password.pdf", pagesize=letter, encrypt = enc)
	
	# Container for the 'Flowable' objects
	elements = []

	# First row (Titles)
	P0 = Paragraph('''<para align=center spaceb=3><b>Application</b></para>''')
	P1 = Paragraph('''<para align=center spaceb=3><b>Username</b></para>''')
	P2 = Paragraph('''<para align=center spaceb=3><b>Password</b></para>''')
	P3 = Paragraph('''<para align=center spaceb=3><b>Time Modified</b></para>''')
	P4 = Paragraph('''<para align=center spaceb=3><b>Date Modified</b></para>''')

	# Data as list of rows (lists)
	data = [[P0, P1, P2, P3, P4]]

	# Insert rows into data  
	for item in ls:
		data.append(item)

	# Create Table 
	t=Table(data)

	# Define Style of the table
	t.setStyle(TableStyle([('ALIGN',(0,0),(-1,-1),'CENTER'),('INNERGRID', (0,1), (-1,-1), 0.25, colors.black),
	('BOX', (0,1), (-1,-1), 0.25, colors.black),('BACKGROUND',(0,0),(4,0),colors.skyblue)]))

	for i in range(len(data)):
		if i % 2 == 0 and i != 0:
			t.setStyle(TableStyle([('BACKGROUND',(0,i),(4,i),colors.lightgrey)]))


	# Append table to container
	elements.append(t)

	try:
		# Write the document to disk
		doc.build(elements)
		return True
	except Exception:
		return False

