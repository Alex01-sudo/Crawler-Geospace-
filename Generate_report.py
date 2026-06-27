import os
import time
from pathlib import Path
from dotenv import load_dotenv

from Retrieval_Task.Report_generator import ReportGenerator


load_dotenv()

def main():
    generator = ReportGenerator()
    generator.generate_report()


if __name__ == "__main__":
    main()