from Retrieval_Task.Retrieval_System import RetrievalSystem
import argparse


#[40.7128, -74.0060]



def main():   
    
    parser = argparse.ArgumentParser(description="Retrieval System")
    parser.add_argument("--query", nargs=2, type=float, required=True, help="Query Latitude and Longitude")
    parser.add_argument("--RankFun", type=str, required=True, choices=["121", "122", "123", "124"], help="Which ranking function to use (121, 122, 123, 124)")
    args = parser.parse_args()
    R_sys = RetrievalSystem()
    R_sys.define_index()
    R_sys.print_images(query=args.query, label=args.RankFun) 
    
    
    
if __name__ == "__main__":
    main()