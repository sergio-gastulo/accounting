import pandas as pd
import matplotlib.pyplot as plt
from typing import Optional
from pathlib import Path
from matplotlib.dates import mdates
from .custom_dictionaries import CustomDictionaries
from ..plot.functions import sql_to_pd

class DataPlotter:

    def __init__(self, db_path: Path, dictionary: CustomDictionaries):
        self.df = sql_to_pd(db_path)
        self.period = pd.Timestamp.today().to_period('M')
        self.dictionary = dictionary

        plt.style.use('dark_background')
        plt.rcParams['font.family'] = 'monospace'
        plt.rcParams['font.size'] = 12