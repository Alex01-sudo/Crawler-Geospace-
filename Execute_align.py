import os
import time
from pathlib import Path
from dotenv import load_dotenv

from Retrieval_Task.Retrieval_System import RetrievalSystem


load_dotenv()

def main():
    Spider = RetrievalSystem()
    Spider.align_task()   


if __name__ == "__main__":
    main()