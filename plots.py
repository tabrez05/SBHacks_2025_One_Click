import matplotlib.pyplot as plt
import pandas as pd

def create_visualization(data):
    plt.figure(figsize=(10, 6))
    plt.plot(data)
    plt.savefig('static/plots/visualization.png')
