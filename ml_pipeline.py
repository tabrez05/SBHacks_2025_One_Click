from sentence_transformers import SentenceTransformer
import numpy as np

class MLPipeline:
    def __init__(self):
        self.model = SentenceTransformer('all-mpnet-base-v2')
    
    def process(self, text):
        return self.model.encode(text)
