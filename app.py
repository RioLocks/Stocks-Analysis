# Installation des bibliothèques nécessaires
# !pip install yfinance pandas requests scikit-learn

import yfinance as yf
import pandas as pd
import requests
import json
from sklearn.preprocessing import StandardScaler


index = "Nasdaq-100"

# Fonction pour obtenir les composants de l'indice à partir de Wikipedia
def get_components():
    url = "https://en.wikipedia.org/wiki/NASDAQ-100"
    response = requests.get(url)
    if response.status_code == 200:
        tables = pd.read_html(response.text)
        df = tables[4]
        return df['Ticker'].tolist()
    else:
        print("Erreur lors de la récupération des composants de l'indice")
        return []

# Fonction pour télécharger les données fondamentales
def get_fundamental_data(ticker):
    stock = yf.Ticker(ticker)
    
    # Récupérer les informations générales
    info = stock.info
    
    return {
        'info': info
    }

# Fonction pour collecter les données fondamentales pour tous les tickers
def collect_data(tickers):
    data = []
    for ticker in tickers:
        try:
            ticker_data = get_fundamental_data(ticker)
            data.append((ticker, ticker_data))
        except Exception as e:
            print(f"Erreur lors de la collecte des données de {ticker}: {e}")
    return data

# Fonction pour analyser les données fondamentales et attribuer un score selon une stratégie
def analyze_fundamentals(data, strategy):
    criteria_list = list(strategy.keys())
    criteria_list.remove('objectif')
    
    rows = []
    for ticker, ticker_data in data:
        info = ticker_data['info']
        row = {'Ticker': ticker}
        for criterion in criteria_list:
            row[criterion] = info.get(criterion, None)
        rows.append(row)
    
    df = pd.DataFrame(rows, columns=['Ticker'] + criteria_list)
    
    # Remplacer les valeurs NaN par 0 ou une valeur par défaut
    df.fillna(0, inplace=True)
    
    # Normaliser les critères (en utilisant StandardScaler pour les z-scores)
    scaler = StandardScaler()
    df[criteria_list] = scaler.fit_transform(df[criteria_list].astype(float))
    
    # Ajuster les poids des critères
    weights = {criterion: weight for criterion, weight in strategy.items() if criterion != 'objectif'}
    
    # Calculer le score en pondérant les critères
    df['Score'] = sum(df[criterion] * weight for criterion, weight in weights.items())
    
    return df

# Fonction principale pour analyser les composants de l'indice selon plusieurs stratégies
def global_analysis(strategies):
    tickers = get_components()
    data = collect_data(tickers)
    
    for strategy_name, strategy in strategies.items():
        result_df = analyze_fundamentals(data, strategy)
        # Sauvegarder les résultats dans un fichier CSV par stratégie
        result_df.to_csv(f'data/{index}/{strategy_name}.csv', index=False)
        print(f"Résultats de l'analyse pour la stratégie '{strategy_name}' enregistrés dans {index}/{strategy_name}.csv")

# Charger les stratégies depuis le fichier JSON
with open(r'data\utils\strategies.json', 'r') as f:
    strategies = json.load(f)

# Analyser les composants du S&P 500 selon les stratégies
global_analysis(strategies)
