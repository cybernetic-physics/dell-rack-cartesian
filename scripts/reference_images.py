from pathlib import Path
from pypdf import PdfReader

reader = PdfReader("research/xe9680-technical-guide.pdf")
for page_number in (10, 12):
    for i, image in enumerate(reader.pages[page_number - 1].images):
        dest = Path(f"research/dell-page-{page_number}-{i}.{image.name.rsplit('.', 1)[-1]}")
        dest.write_bytes(image.data)
        print(dest)
