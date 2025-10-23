import os
from pathlib import Path
from pypdf import PdfReader, PdfWriter
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

IMPORT_DIR = Path("/app/import-doppelseitig")
OUTPUT_DIR = Path("/app/import")
PROCESSED_DIR = IMPORT_DIR / "processed"

def merge_pdfs():
    """
    Scans the import directory for PDF files, merges each pair (front and back scans),
    and saves the merged PDF to the output directory. Processed files are moved to
    a 'processed' subdirectory.
    """
    PROCESSED_DIR.mkdir(exist_ok=True)

    try:
        # Get all PDF files and sort them by modification time
        pdfs = sorted(
            [p for p in IMPORT_DIR.glob("*.pdf") if p.is_file()],
            key=os.path.getmtime
        )
    except Exception as e:
        logging.error(f"Error reading files from {IMPORT_DIR}: {e}")
        return

    if len(pdfs) < 2:
        logging.info("Waiting for at least two PDF files to process.")
        return

    logging.info(f"Found {len(pdfs)} PDF files to process.")

    # Process files in pairs
    for i in range(0, len(pdfs) - (len(pdfs) % 2), 2):
        front_pdf_path = pdfs[i]
        back_pdf_path = pdfs[i+1]

        logging.info(f"Processing pair: {front_pdf_path.name} (front) and {back_pdf_path.name} (back)")

        try:
            front_reader = PdfReader(front_pdf_path)
            back_reader = PdfReader(back_pdf_path)
            writer = PdfWriter()

            # The scanner scans back pages in reverse order, so we just need to interleave.
            # If the scanner would not reverse them, we would need:
            # reversed_back_pages = list(reversed(back_reader.pages))
            
            num_front_pages = len(front_reader.pages)
            num_back_pages = len(back_reader.pages)
            
            # The scanner produces back pages in reverse order, so we need to reverse them back
            # to get the correct reading order.
            # e.g., scanner produces [P4, P2] from a stack of 2 back pages. We reverse to [P2, P4].
            back_pages_reversed = list(back_reader.pages)
            back_pages_reversed.reverse()

            num_front_pages = len(front_reader.pages)
            num_back_pages_processed = len(back_pages_reversed) # Renamed for clarity

            # Interleave pages
            for i in range(max(num_front_pages, num_back_pages_processed)):
                if i < num_front_pages:
                    writer.add_page(front_reader.pages[i])
                if i < num_back_pages_processed:
                    writer.add_page(back_pages_reversed[i])

            logging.info(f"PdfWriter contains {len(writer.pages)} pages before writing to file.")

            output_filename = f"duplex_{front_pdf_path.stem}.pdf"
            output_path = OUTPUT_DIR / output_filename

            with open(output_path, "wb") as f_out:
                writer.write(f_out)
            
            logging.info(f"Successfully merged files into {output_path}")

            # Move processed files
            front_pdf_path.rename(PROCESSED_DIR / front_pdf_path.name)
            back_pdf_path.rename(PROCESSED_DIR / back_pdf_path.name)
            logging.info(f"Moved original files to {PROCESSED_DIR}")

        except Exception as e:
            logging.error(f"Error processing pair {front_pdf_path.name} and {back_pdf_path.name}: {e}")
            # Decide on an error strategy: move to an error folder, or leave them?
            # For now, we leave them and log the error.

if __name__ == "__main__":
    merge_pdfs()
