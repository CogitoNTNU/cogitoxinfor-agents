from PyPDF2 import PdfReader

def pdf_to_text(pdf_path, txt_output_path):
    """
    Extract all text from a PDF file and save it as a single string in a text file.
    :param pdf_path: Path to the source PDF file.
    :param txt_output_path: Path to the output text file.
    """
    text_content = ""

    with open(pdf_path, 'rb') as pdf_file:
        reader = PdfReader(pdf_file)
        
        # Loop through all pages in the PDF, but skip the first two
        for index, page in enumerate(reader.pages):
            # Skip first two pages (indices 0 and 1)
            if index < 2:
                continue
            
            page_text = page.extract_text()
            if page_text:
                text_content += page_text + "\n"

    # Write the extracted text to the output text file
    with open(txt_output_path, 'w', encoding='utf-8') as text_file:
        text_file.write(text_content)

if __name__ == "__main__":
    # Example usage
    pdf_to_text("../data/pdffile.pdf", "output.txt")