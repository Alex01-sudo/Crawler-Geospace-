from Retrieval_Task.Retrieval_System import RetrievalSystem






def main():   
    
    R_sys = RetrievalSystem()
    R_sys.define_index()
    R_sys.print_images([40.7128, -74.0060])  
    
    
    
if __name__ == "__main__":
    main()