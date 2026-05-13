import ollama
import json

async def summarize_article(article_text: str, title: str = "") -> dict:
    """
    Wysyła tekst artykułu do lokalnego modelu z prośbą o analitykę.
    """
    if not article_text:
        return {
            "summary": "Brak tekstu do podsumowania.", 
            "location": "Nieznana",
            "sentiment": "Neutralny",
            "category": "Inne",
            "key_figures": ""
        }

    prompt = f"""
    Jesteś profesjonalnym analitykiem wiadomości. Przeczytaj tytuł i treść artykułu, a następnie zwróć wynik WYŁĄCZNIE jako obiekt JSON.

    TYTUŁ: {title}

    ZASADY DLA POLA "location":
    - Podaj JEDNO konkretne państwo w języku polskim (np. "Polska", "Stany Zjednoczone", "Ukraina", "Niemcy").
    - Jeśli tytuł zawiera skrót "USA" lub "Stany Zjednoczone" — wpisz "Stany Zjednoczone".
    - Jeśli artykuł dotyczy kilku krajów, wybierz ten, o którym mówi GŁÓWNY wątek.
    - Wpisz "Globalne" TYLKO gdy artykuł naprawdę nie dotyczy żadnego konkretnego państwa (np. raporty ONZ, globalne statystyki klimatyczne).

    Zwróć JSON z kluczami:
    - "summary": Streszczenie 4-5 zdań po polsku
    - "location": Państwo (po polsku) lub "Globalne"
    - "sentiment": "Pozytywny", "Negatywny" lub "Neutralny"
    - "category": "Polityka", "Gospodarka", "Klimat", "Konflikty", "Technologia", lub "Inne"
    - "key_figures": Główne postacie lub organizacje (tekst, przecinki)

    Nie dodawaj żadnego innego tekstu ani tagów markdown. Zwróć czysty JSON.

    TREŚĆ ARTYKUŁU:
    {article_text}
    """

    try:
        client = ollama.AsyncClient()
        response = await client.generate(
            model='gemma2',
            prompt=prompt,
            format='json'
        )
        
        # Parsujemy odpowiedź JSON
        result_text = response['response']
        try:
            parsed_data = json.loads(result_text)
            return {
                "summary": parsed_data.get("summary", "Brak podsumowania."),
                "location": parsed_data.get("location", "Nieznana"),
                "sentiment": parsed_data.get("sentiment", "Neutralny"),
                "category": parsed_data.get("category", "Inne"),
                "key_figures": parsed_data.get("key_figures", "")
            }
        except json.JSONDecodeError:
            print("⚠️ Model nie zwrócił poprawnego JSONa.")
            return {
                "summary": result_text, 
                "location": "Nieznana",
                "sentiment": "Neutralny",
                "category": "Inne",
                "key_figures": ""
            }
            
    except Exception as e:
        print(f"⚠️ Błąd lokalnego modelu LLM: {e}")
        return {
            "summary": "Błąd generowania podsumowania.", 
            "location": "Błąd",
            "sentiment": "Błąd",
            "category": "Błąd",
            "key_figures": ""
        }
