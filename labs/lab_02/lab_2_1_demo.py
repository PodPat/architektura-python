# -*- coding: utf-8 -*-
import requests
from bs4 import BeautifulSoup
import time
import logging

# Konfiguracja logowania, aby widzieć postępy w konsoli
logging.basicConfig(level=logging.INFO, format='%(message)s')

def download_site(url):
    """
    Pobiera treść strony i wyciąga tytuły wydarzeń.
    """
    titles_from_site: list[str] = []
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        # Znajdujemy wszystkie linki do wydarzeń, które zawierają nagłówki h3 z tytułami
        event_links = soup.select('.item__link h3')
        
        for item in event_links:
            title = item.text.strip()
            logging.info(f"  [OK] Pobrano: {title[:50]}...")
            titles_from_site.append(title)
            
    except Exception as e:
        logging.error(f"  [BŁĄD] Nie udało się pobrać {url}: {e}")
        
    return titles_from_site

def download_all_sites(sites):
    """
    Pobiera dane ze wszystkich stron po kolei (sekwencyjnie).
    """
    all_titles = []
    for url in sites:
        logging.info(f"Pobieranie strony: {url}")
        titles = download_site(url)
        all_titles.extend(titles)
    return all_titles

if __name__ == "__main__":
    # Dzisiejsza data dla kalendarium
    date_str = "2026-03-20"
    # Przygotowujemy listę 5 stron kalendarza (indeksy 0-4)
    base_url = "https://www.krakow.pl/kalendarium/1919,shw"
    sites = [f"{base_url},{date_str},{i},day.html" for i in range(5)]
    
    logging.info(f"--- ROZPOCZĘCIE POBIERANIA SEKWENCYJNEGO (5 stron) ---")
    start_time = time.time()
    
    all_titles = download_all_sites(sites)
    
    end_time = time.time()
    duration = end_time - start_time
    
    logging.info(f"--- ZAKOŃCZONO ---")
    logging.info(f"Łącznie pobrano tytułów: {len(all_titles)}")
    print("\nPierwsze 10 tytułów:")
    for i, title in enumerate(all_titles[:10], 1):
        print(f"{i}. {title}")
        
    logging.info(f"\nCzas wykonania sekwencyjnego: {duration:.2f} sekund")
