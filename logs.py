import datetime 
import os
display = False
write_in_file = True





class Logger():

    information="Information"
    success="Success"     
    warning="Warning"
    error="Error"
    critical_error="Critical Error"
    shutdown_error="Shutdown Error"    

    def __init__(self,display=False,write_in_file=False,name="log"):
        self.display=display
        self.write_in_file=write_in_file        
        self.name=name

        try :        
            with open(".count_logs"+self.name+".txt") as f:
                self.counter = int(f.read())
        except :
            self.counter = 0
            with open(".count_logs"+self.name+".txt","w") as f:
                f.write(str(self.counter))


    def add(self, message, rank="information") -> None:    
        """Log Handler 

        Ranks :
        - Success
        - Information 
        - Warning
        - Error
        - Critical Error
        - Shutdown Error"""

        
        def rank_display(rank:str):
            rank = rank.lower()

            match rank:
                case "information" : 
                    return ""
                
                case "warning" :
                    return "\033[33mWarning : "
                
                case "error" : 
                    return "\033[31mError : "
                
                case "critical error" : 
                    return "\033[41mCRITICAL ERROR : "
                
                case "shutdown error" :
                    return "\033[42m\033[1mSHUTDOWN ERROR :"
                
                case "success" : 
                    return "\033[32mSuccess : "
                
            return "\033[36m The rank doesn't exist : "
        
        def rank__html_color(rank:str): #inner function
            rank = rank.lower()

            match rank:
                case "information" : 
                    return "style=\"\""
                
                case "warning" :
                    return "style=\"color :orange;\""
                
                case "error" : 
                    return "style=\"color : red;\""
                
                case "critical error" : 
                    return "style=\"color : white;background-color:red;\""
                
                case "shutdown error" :
                    return "style=\"color :white ;background-color:black;\""
                
                case "success" : 
                    return "style=\"color : white;background-color:green\""
                
            return ""

        def rank__html_comment(rank:str): #inner function to help
            rank = rank.lower()

            match rank:
                case "information" : 
                    return " "
                
                case "warning" :
                    return "Warning : "
                
                case "error" : 
                    return "Error : "
                
                case "critical error" : 
                    return "CRITICAL ERROR : "
                
                case "shutdown error" :
                    return "SHUTDOWN ERROR : "
                
                case "success" : 
                    return "Success : "
                
            return "NON-EXISTANT RANK  : "
        

        
        
        if self.display : 
            print(f'{datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S:%f")[:-3]} -> {self.name} | {rank_display(rank)+message}\033[0m')

        if self.write_in_file:
            try:
                if os.stat(self.name+str(self.counter)+".html").st_size>1_000_000:
                    self.counter+=1
                    with open(".count_logs"+self.name+".txt","w",encoding="utf8") as f:
                        f.write(str(self.counter))
            except:
                with open(self.name+str(self.counter)+".html","w") as f3:
                    f3.write("<body style=\"font-family:arial,verdana;\">")
                
            
            with open(self.name+str(self.counter)+".html","a",encoding="utf8") as f2:
                f2.write("</br><span "+rank__html_color(rank)+">"+datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S:%f")[:-3]+"   "+rank__html_comment(rank)+message+"</span>")






   
if __name__=="__main__":
    l=Logger()

