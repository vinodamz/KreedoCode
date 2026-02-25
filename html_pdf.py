import os
from weasyprint import HTML

class PdfConverter:
    """
    A reusable class to convert HTML content to a PDF file.

    This class provides methods to generate a PDF from an HTML string,
    a local HTML file, or a remote URL. It uses WeasyPrint as the
    conversion engine.
    """

    def __init__(self):
        """Initializes the PdfConverter."""
        print("PdfConverter initialized. Using WeasyPrint engine.")

    def from_string(self, html_string: str, output_path: str):
        """
        Converts an HTML string to a PDF file.

        Args:
            html_string (str): The HTML content as a string.
            output_path (str): The path where the PDF file will be saved.

        Returns:
            bool: True if conversion was successful, False otherwise.
        """
        try:
            print(f"Converting HTML string to {output_path}...")
            # The base_url is necessary to resolve relative paths for images, CSS, etc.
            # For a simple string, the current directory '.' is a sensible default.
            base_url = os.path.dirname(output_path) or '.'
            HTML(string=html_string, base_url=base_url).write_pdf(output_path)
            print(f"Successfully created {output_path}")
            return True
        except Exception as e:
            print(f"Error converting HTML string to PDF: {e}")
            return False

    def from_file(self, input_path: str, output_path: str):
        """
        Converts a local HTML file to a PDF file.

        Args:
            input_path (str): The path to the source HTML file.
            output_path (str): The path where the PDF file will be saved.

        Returns:
            bool: True if conversion was successful, False otherwise.
        """
        try:
            print(f"Converting file {input_path} to {output_path}...")
            HTML(filename=input_path).write_pdf(output_path)
            print(f"Successfully created {output_path}")
            return True
        except FileNotFoundError:
            print(f"Error: The input file '{input_path}' was not found.")
            return False
        except Exception as e:
            print(f"Error converting HTML file to PDF: {e}")
            return False

    def from_url(self, url: str, output_path: str):
        """
        Converts a web page from a URL to a PDF file.

        Args:
            url (str): The URL of the web page to convert.
            output_path (str): The path where the PDF file will be saved.

        Returns:
            bool: True if conversion was successful, False otherwise.
        """
        try:
            print(f"Converting URL {url} to {output_path}...")
            HTML(url=url).write_pdf(output_path)
            print(f"Successfully created {output_path}")
            return True
        except Exception as e:
            print(f"Error converting URL to PDF: {e}")
            return False

# --- Example of how to use the class ---
if __name__ == "__main__":
    # 1. Create an instance of the converter
    converter = PdfConverter()

    # 2. Create a sample HTML file for testing
    

    # --- Use Case 1: Convert from a local file ---
    converter.from_file('alankrita_june24.html', 'alankrita_june24.pdf')

   