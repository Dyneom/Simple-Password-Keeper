

import logs
import random
import spk_theme

class SpkTheme():
    #TODO : change the default config to be in a file
    _default_config = """background {
    background-color: #202020;
    color : #c0c0c0;
}

password_background { 
    background-color: #606060;
    border-radius: 10px;
    height: 20%;
    width: 100%;
}

password_name {
    background-color: #202020;
    border-radius: 10px;
    padding: 6px;
    margin:10px;
    width:25%
}

show_button { 
    background-color: #202020;
    border-radius: 10px;
    border: 1px solid #ccc;
    padding: 6px;
    margin: 10px;
    width:33%
}
edit_button { 
    background-color: #202020;
    border-radius: 10px;
    border: 1px solid #ccc;
    padding: 6px;
    margin:10px;
    width:33%
}

supr_button { 
    background-color: #202020;
    border-radius: 10px;
    border: 1px solid #ccc;
    padding: 6px;
    margin:10px;
    width:33% 
} 

supr_button_hover {
    background-color: #f0c0c0; 
    color: black
}

password { 
    background-color: #404040;
    border-radius: 10px;
    padding: 6px;
    margin:10px;
    width: 100%
}
password_warning { 
    background-color: #b90101;
    border-radius: 10px;
    padding: 6px;
    margin:10px;
    width: 100%
}

font {
    font: Verdana;
    size : 15
}

global = fusion

dialog_password_main = background-color: #505050; border-radius: 1px; padding: 10px; margin:10px; width: 100%; height:20%
dialog_password_message = background-color: #202020; color : #c0c0c0; padding: 10px; border-radius: 5px
dialog_password_password = background-color: #202020; color : #c0c0c0; padding: 10px; border-radius: 5px
dialog_password_buttons = background-color: #202020; color : #c0c0c0; padding: 10px; border-radius: 5px


dialog_wrong_character = background-color: #505050; border-radius: 1px; padding: 10px; margin:10px; width: 100%; height:20%
dialog_wrong_character_button = background-color: #505050; border-radius: 1px; padding: 10px; margin:10px; width: 100%; height:20%
        
    """


    def __init__(self,config_file_dir,settings : spk_theme.ConfigDicts):
        self.logger = logs.Logger(display=settings.to_settings("logs"),write_in_file=False,name="theme")
        self.logger.add("Theme Class created",self.logger.success)
        with open(config_file_dir,"r",encoding="utf8") as f:
            contents = f.read()        
        self.config = self.parse(contents)  
        self.default_config = self.parse(self._default_config)
  

    def parse(self,content):
        d={}
        def tree(all_c,line):
            for i in range(len(all_c)-line):
                if all_c[i+line].find("}") != -1:
                    line_end = i+line
                    break
            else :
                self.logger.add("Invalid config at line {line}. Found no corresponding curly braces",self.logger.warning)
                return line+1
            
            name = all_c[line].split("{")[0].strip()
            content_to_parse = all_c[line+1:line_end]
            content_to_parse += all_c[line_end].split("}")[0] 
            
            sub_args_dict : dict = {}
            for s in content_to_parse: # s in the string at line ...
                for sub_string in s.split(";"): 
                    s_b2 = sub_string.strip()
                    if s_b2 != "":
                        arg = s_b2.split(":")
                        if len(arg) == 2 :
                            key , value = arg
                            sub_args_dict[key.strip()] = value.strip()            
            d[name] = sub_args_dict
            return line_end+1
        def line(all_c,line):
            l = all_c[line].split("=")
            if len(l) != 2:
                self.logger.add(f"Invalid config at line {line} found : {l}",self.logger.warning)
                return line+1
             
            sub_d = {}
            
            for sb in l[1].split(";"): 
                if sb == [""] : 
                    self.logger.add(f"Invalid config at line {line}. Empty value after equal",self.logger.warning)     
                            
                elif sb.strip().find(":") == -1: # a single word                    
                    sub_d[l[0].strip()] = sb.strip()
                    break
                arg = sb.split(":")
                if len(arg) == 2:
                    k,v=arg
                    sub_d[k.strip()] = v.strip()
                    
                elif  arg != [""]:                    
                    self.logger.add(f"Invalid config at line {line}. Found : {arg}",self.logger.warning)
                    

            d[l[0].strip()] =  sub_d
            return line+1
                
        content = content.split("\n")      

        line_counter = 0
        while line_counter<len(content):
            is_braces = content[line_counter].find("{") != -1
            is_equal_char = content[line_counter].find("=") != -1
            if is_braces and is_equal_char:
                self.logger.add(f"Wrong config at line {line_counter}. Found '=' and '{"{"}' on the same line",self.logger.warning)      
                line_counter += 1
            elif is_braces :
                line_counter = tree(content,line_counter)
            elif is_equal_char : 
                line_counter = line(content,line_counter)
            else:
                line_counter +=1
        
        return d            

    def get(self,value):
        if self.config.get(value) != None: 
            return ConfigDicts(self.config.get(value)) 
        elif self.default_config.get(value) != None: 
            return ConfigDicts(self.default_config.get(value))
        return ""

    def get_list(self,value): 
        if self.config.get(value) != None: 
            return (self.config.get(value))
        elif self.default_config.get(value) != None: 
            return self.default_config.get(value).split(";") # /!\ to change 
        return [] 
 
def print_dict(d):
    for i in d:
        print(f"\033[33m{i} \033[0m: {d[i]}")  



class ConfigDicts(dict):

    def __init__(self,d,default : dict = {}):
        self.dict = d 
        self.default :dict = default  
        super().__init__(d)

    def __str__(self) -> str:
        s = ""
        for u,v in self.dict.items(): 
            s += f" {u} : {v};"

        return s
    
    def __add__(a,b):
        if isinstance(a,ConfigDicts) and isinstance(b,ConfigDicts) :
            return ConfigDicts(   dict( a.to_list() + b.to_list() ) )
        raise ValueError(f"The two arguments do not have the same type")
    
    def __dict__(self):
        return self.dict
   
    def to_list(self):
        return list(self.dict.items())
    
    def to_config(self):
        return str(self)
    
    def __mul__(self,value):
        if isinstance(value,tuple) and len(value) == 2 and isinstance(value[0],str) and isinstance(value[1],str) and len(value[1]) > 0 :            
            return self + ConfigDicts({ value[0] : value[1]})
        return self
    
    def to_settings(self,val):
        corresponding_val = self.dict.get(val)
        if isinstance(corresponding_val,(str,bool,int)):
            return corresponding_val 
        
        corresponding_val = self.default.get(val) # checking defaults /!\ defaults need to be set externaly
        if isinstance(corresponding_val,(str,bool,int)):
            return corresponding_val 
                
        return f"spk_no_name{random.random()}" # if the config is wrong the dirs will be messy (?)
    



if __name__ == "__main__"  :
    theme = SpkTheme("spk.conf")    
    font = dict(theme.get("global"))
    print("font : ",font)  
    #print("all : ",theme.config)
    #print(str(y))