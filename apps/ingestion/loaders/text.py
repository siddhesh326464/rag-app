import logfire

def parse_text(file_path:str):
    """
    Parses a test configuration or data file from the given path
    """
    with logfire.span("text processing",filename=file_path):
        try:
            with open(file_path, "r",encoding="utf-8",errors='ignore') as f:
                return f.read()
        except Exception as e:
            logfire.error("Text parsed failed")
            raise e
