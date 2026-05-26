import logfire
from bs4 import BeautifulSoup

def html_parse(file_path:str):
    """
    Parses an HTML file and extracts its structured content.
    """
    with logfire.span("HTML parssing",filename=file_path):
        try:
            with open(file_path,'r',encoding='utf-8',errors='ignore') as file:
                content = file.read()
            soup = BeautifulSoup(content,"html.parser")

            tags_to_remove = [
                        'script',  
                        'style',   
                        'nav',     
                        'footer',  
                        'header',  
                        'aside'    
                ]

            for script in soup(tags_to_remove):
                script.decompose()

            text = soup.get_text(separator=' ',strip=True)
            lines = (line for line in text.splitlines())
            chunks = (phrase for line in lines for phrase in line.split(" "))
            text_clean = '\n'.join(chunk for chunk in chunks if chunk)
            
            return text_clean

        except Exception as e:
            logfire.error("HTML parser failed")
            raise e
