import re

class PIIAnonymizerAdapter:
    def __init__(self):
        self.dni_pattern = re.compile(r'\b\d{8}\b')
        self.email_pattern = re.compile(r'[\w\.-]+@[\w\.-]+\.\w+')

    def anonymize(self, text: str) -> str:
        if not text:
            return ""
        text = self.dni_pattern.sub('[DNI_ANONIMIZADO]', text)
        text = self.email_pattern.sub('[EMAIL_ANONIMIZADO]', text)
        return text
    