import ollama

def summarize_article(article_text: str) -> str:
    """
    Wysyła tekst artykułu do lokalnego modelu (Qwen 2.5 14B) 
    z prośbą o krótkie podsumowanie i wskazanie lokalizacji.
    """
    if not article_text:
        return "Brak tekstu do podsumowania."

    prompt = f"""
    Jesteś profesjonalnym analitykiem wiadomości. Przeczytaj poniższy artykuł i zwróć:
    - KRÓTKIE PODSUMOWANIE (2-3 zdania w języku polskim)
    - LOKALIZACJA: (Kraj lub miasto, którego dotyczy tekst)

    Tekst artykułu:
    {article_text}
    """

    try:
        response = ollama.generate(
            model='gemma2',
            prompt=prompt
        )
        return response['response']
        
    except Exception as e:
        print(f"⚠️ Błąd lokalnego modelu LLM: {e}")
        return "Błąd generowania podsumowania."
