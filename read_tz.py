"""Read TZ document"""
from docx import Document

doc = Document('/Users/sayatkasabulatov/Documents/My-first-project/Техническое_задание_Телеграм_бот.docx')

for paragraph in doc.paragraphs:
    if paragraph.text.strip():
        print(paragraph.text)
