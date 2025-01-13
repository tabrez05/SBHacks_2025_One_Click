import os
from anthropic import Anthropic

class SycamoreAI:
    def __init__(self):
        self.client = Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))
    
    def analyze_text(self, text):
        return {'analysis': 'Completed'}
