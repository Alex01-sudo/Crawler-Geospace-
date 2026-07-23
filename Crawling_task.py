
from dotenv import load_dotenv
from Software_Crawler.Spider import GraphSpider

load_dotenv()

def main():
    Spider = GraphSpider()
    Spider.execute_crawl()   


if __name__ == "__main__":
    main()
    





