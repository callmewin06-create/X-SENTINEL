# X-SENTINEL

Semantic cross-view consistency for backdoor detection in PE malware classifiers.

## Setup
pip install lightgbm shap scikit-learn pandas numpy streamlit

## Data
Download EMBER2018 (feature version 2) from github.com/elastic/ember
and extract to `data/`. Not tracked by Git.

## Structure
- attack/      poisoning and triggers
- detection/   M1-M5 (TADR, STRIP, cross-view)
- evaluation/  metrics, experiments E0-E5
