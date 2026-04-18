# -*- coding: utf-8 -*-
import requests
from bs4 import BeautifulSoup
import time
import logging
import concurrent.futures

# Konfiguracja logowania
logging.basicConfig(level=logging.INFO, format='%(message)s')

def download_site(url):
    """
    Pobiera treść strony i wyciąga tytuły wydarzeń.
    Funkcja jest przystosowana do pracy w wielu wątkach.
    """
    titles_from_site: list[str] = []
    try:
        # requests.get rozmawia z siecią - to operacja I/O-bound
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        event_links = soup.select('.item__link h3')
        
        for item in event_links:
            title = item.text.strip()
            # Logowanie z informacją o wątku (opcjonalnie)
            logging.info(f"  [OK] Pobrano: {title[:50]}...")
            titles_from_site.append(title)
            
    except Exception as e:
        logging.error(f"  [BŁĄD] Nie udało się pobrać {url}: {e}")
        
    return titles_from_site

def download_all_sites_threaded(sites):
    """
    Pobiera dane ze wszystkich stron równolegle przy użyciu puli wątków.
    """
    all_titles = []
    # ThreadPoolExecutor zarządza wątkami za nas
    # max_workers=5 oznacza, że naraz pobieramy 5 stron
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        # executor.map rozdziela zadania pobierania stron na dostępne wątki
        results = executor.map(download_site, sites)
        
        for titles in results:
            all_titles.extend(titles)
            
    return all_titles

if __name__ == "__main__":
    date_str = "2026-03-20"
    base_url = "https://www.krakow.pl/kalendarium/1919,shw"
    sites = [f"{base_url},{date_str},{i},day.html" for i in range(5)]
    
    logging.info(f"--- ROZPOCZĘCIE POBIERANIA WIELOWĄTKOWEGO (5 stron) ---")
    start_time = time.time()
    
    # Wywołanie wersji wielowątkowej
    all_titles = download_all_sites_threaded(sites)
    
    end_time = time.time()
    duration = end_time - start_time
    
    logging.info(f"--- ZAKOŃCZONO ---")
    logging.info(f"Łącznie pobrano tytułów: {len(all_titles)}")
    print("\nPierwsze 10 tytułów (Threading):")
    for i, title in enumerate(all_titles[:10], 1):
        print(f"{i}. {title}")
        
    logging.info(f"\nCzas wykonania wielowątkowego: {duration:.2f} sekund")
