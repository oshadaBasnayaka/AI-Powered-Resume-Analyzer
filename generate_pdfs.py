import pandas as pd
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.utils import simpleSplit
import os

# Create a directory to store the generated test PDFs
os.makedirs("Kaggle_Test_PDFs", exist_ok=True)

# Read the Kaggle CSV file (Change the filename here if it's different)
csv_file = "UpdatedResumeDataSet.csv"

try:
    df = pd.read_csv(csv_file)
    print("CSV successfully loaded. Starting PDF generation...")

    # Take the first 50 resumes from the dataset and generate 50 PDFs
    for index, row in df.head(50).iterrows():
        # 'Resume' is the column name containing the text in the Kaggle CSV
        text = str(row['Resume'])

        pdf_filename = f"Kaggle_Test_PDFs/Candidate_Resume_{index + 1}.pdf"

        c = canvas.Canvas(pdf_filename, pagesize=letter)
        textobject = c.beginText(40, 750)
        textobject.setFont("Helvetica", 10)

        # Wrap the text to fit within the page width
        lines = simpleSplit(text, "Helvetica", 10, 500)

        # Limit to about 60 lines so the text doesn't overflow the page boundaries
        for line in lines[:60]:
            textobject.textLine(line)

        c.drawText(textobject)
        c.save()
        print(f" Created: {pdf_filename}")

    print("\nSuccess! All 50 PDFs generated successfully.")
    print("You can now select these files from the 'Kaggle_Test_PDFs' folder for the Recruiter Bulk Upload.")

except FileNotFoundError:
    print(f"Error: The file '{csv_file}' was not found. Please make sure it is in the same folder as this script.")
except Exception as e:
    print(f"An error occurred: {e}")