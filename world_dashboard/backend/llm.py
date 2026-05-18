import ollama
import json

async def summarize_article(article_text: str, title: str = "") -> dict:
    """
    Wysyła tekst artykułu do lokalnego modelu z prośbą o analitykę (bez kategorii, z tłumaczeniem tytułu).
    """
    # Obsługa artykułów za paywallem (brak tekstu)
    if not article_text.strip():
        article_text_prompt = "BRAK TREŚCI. ZGADNIJ LOKACJĘ I WYGENERUJ ZDANIA STRESZCZENIA TYŁKO I WYŁĄCZNIE NA PODSTAWIE SAMEGO TYTUŁU."
    else:
        article_text_prompt = article_text
        
    # Przycięcie zbyt długich tekstów, aby modelowi starczyło okna kontekstowego na pełną odpowiedź!
    if len(article_text_prompt) > 4000:
        article_text_prompt = article_text_prompt[:4000] + "... [TEKST UCIĘTY]"

    prompt = f"""
    Jesteś profesjonalnym analitykiem wiadomości. Przeczytaj tytuł i treść artykułu, a następnie zwróć wynik WYŁĄCZNIE jako obiekt JSON (żadnego dodatkowego tekstu).

    ORYGINALNY TYTUŁ: {title}

    ZASADY DLA POLA "translated_title":
    - Przetłumacz powyższy oryginalny tytuł na język polski.
    - Tłumaczenie powinno brzmieć naturalnie w języku polskim, jak nagłówek prasowy (np. "In response to Trump, Taiwan says..." -> "Tajwan odpowiada Trumpowi: Jesteśmy suwerenni i niepodlegli").
    - Zachowaj powagę i styl informacyjny.

    ZASADY DLA POLA "summary":
    - Streszczenie 4-5 zdań wyłącznie po polsku.
    - Słowa kategorycznie ZAKAZANE w CAŁYM tekście streszczenia: "artykuł", "autor", "tekst", "wpis", "strona", "autorzy", "reportaż", "wiadomość", "redakcja", "doniesienie", "publikacja". Użycie któregokolwiek z tych słów jest krytycznym błędem!
    - Kategorycznie ZABRANIA SIĘ rozpoczynania streszczenia lub używania w nim sformułowań metatekstowych takich jak: "Artykuł mówi o...", "W artykule opisano...", "Artykuł dotyczy...", "Przedstawiono...", "Autor analizuje...", "Tekst opisuje...".
    - Pisz bezpośrednio i wprost o opisywanych wydarzeniach, tak jakby to była bezpośrednia relacja reporterska.
    - Przykład POPRAWNEGO początku streszczenia: "W Tokio wybuchł groźny pożar fabryki plastiku. Na miejscu pracuje kilkanaście zastępów straży pożarnej..."
    - Przykład NIEPOPRAWNEGO początku: "Artykuł opisuje pożar fabryki w Tokio, który wybuchł w niedzielę..."

    ZASADY DLA POLA "location":
    - Podaj JEDNO konkretne państwo w języku polskim (np. "Polska", "Stany Zjednoczone", "Ukraina", "Niemcy", "Tajwan", "Rosja").
    - Wykorzystaj nazwy miast, regionów, walut oraz nazwiska polityków jako kluczowe wskazówki.
    - Jeśli artykuł dotyczy relacji międzynarodowych, wojen, dyplomacji lub konfliktów zbrojnych (np. wojna w Ukrainie, napięcia na linii Chiny-Tajwan, wojna w Izraelu/Strefie Gazy), BEZWZGLĘDNIE wybierz jedno z państw, którego konflikt bezpośrednio dotyczy (np. "Ukraina", "Tajwan", "Rosja", "Izrael"). 
    - KATEGORYCZNY ZAKAZ: Konflikty zbrojne, sankcje polityczne i napięcia terytorialne NIGDY nie mogą być klasyfikowane jako "Globalne".
    - "Globalne" używaj TYLKO i WYŁĄCZNIE dla tematów stricte ogólnoświatowych, takich jak: astronomia, klimatologia, globalne pandemie, odkrycia naukowe obejmujące całą ludzkość. Jeśli masz wątpliwości, przypisz państwo.

    Zwróć JSON z kluczami:
    - "translated_title": Przetłumaczony na język polski tytuł artykułu (jako nagłówek)
    - "summary": Streszczenie bezpośrednie (4-5 zdań po polsku, bez meta-tekstów)
    - "location": Państwo (po polsku) lub "Globalne"
    - "sentiment": "Pozytywny", "Negatywny" lub "Neutralny"
    - "key_figures": Główne postacie lub organizacje (tekst, przecinki)

    Nie dodawaj żadnego innego tekstu ani tagów markdown. Zwróć czysty JSON.

    TREŚĆ ARTYLUŁU:
    {article_text_prompt}
    """

    try:
        client = ollama.AsyncClient()
        response = await client.generate(
            model='gemma2',
            prompt=prompt,
            format='json'
        )
        
        result_text = response['response'].strip()
        
        # Agresywne wycinanie czystego obiektu JSON (ignorowanie jakiegokolwiek tekstu przed/po)
        start_idx = result_text.find('{')
        end_idx = result_text.rfind('}')
        if start_idx != -1 and end_idx != -1 and end_idx >= start_idx:
            result_text = result_text[start_idx:end_idx+1]
        
        try:
            parsed_data = json.loads(result_text)
            
            summary = parsed_data.get("summary", "Brak podsumowania.")
            # Zabezpieczenie przed "matrioszką" (gdy model wklei JSON jako string w polu summary)
            if isinstance(summary, str) and summary.strip().startswith("{"):
                try:
                    nested = json.loads(summary)
                    summary = nested.get("summary", summary)
                except json.JSONDecodeError:
                    summary = "Model AI zapętlił się i wygenerował nieczytelną strukturę."

            return {
                "translated_title": parsed_data.get("translated_title", ""),
                "summary": summary,
                "location": parsed_data.get("location", "Nieznana"),
                "sentiment": parsed_data.get("sentiment", "Neutralny"),
                "key_figures": parsed_data.get("key_figures", "")
            }
        except json.JSONDecodeError:
            print(f"⚠️ Model nie zwrócił poprawnego JSONa (być może uciął odpowiedź). Raw: {result_text[:100]}")
            return {
                "translated_title": title, # Próba uratowania przynajmniej oryginalnego tytułu
                "summary": "Model AI niespodziewanie przerwał analizę artykułu (błąd dekodowania).", 
                "location": "Nieznana",
                "sentiment": "Neutralny",
                "key_figures": ""
            }
            
    except Exception as e:
        print(f"⚠️ Błąd lokalnego modelu LLM: {e}")
        return {
            "translated_title": "",
            "summary": "Błąd generowania podsumowania.", 
            "location": "Błąd",
            "sentiment": "Błąd",
            "key_figures": ""
        }
