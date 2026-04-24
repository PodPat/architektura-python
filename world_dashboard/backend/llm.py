import ollama
import json

async def summarize_article(article_text: str) -> dict:
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
    Jesteś profesjonalnym analitykiem wiadomości. Przeczytaj poniższy artykuł i zwróć wynik WYŁĄCZNIE jako obiekt JSON z następującymi kluczami:
    - "summary": Streszczenie (4-5 zdania w języku polskim)
    - "location": Państwo, którego dotyczy tekst. Podaj jedną główną lokalizację, jeśli tekst nie dotyczy konkretnej lokalizacji wpisz 'Globalne'.
    - "sentiment": Wydźwięk artykułu. Wybierz jedną opcję: 'Pozytywny', 'Negatywny' lub 'Neutralny'.
    - "category": Kategoria artykułu. Wybierz jedną z: 'Polityka', 'Gospodarka', 'Klimat', 'Konflikty', 'Technologia', lub 'Inne'.
    - "key_figures": Główne postacie lub organizacje (zwróć jako jeden tekst, połączone przecinkami).

    Nie dodawaj żadnego innego tekstu, tagów markdown ani komentarzy, zwróć czysty JSON.
    
    Tekst artykułu:
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
