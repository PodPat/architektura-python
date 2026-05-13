"""
Moduł do grupowania artykułów o tych samych wydarzeniach
przy użyciu embeddingów i podobieństwa kosinusowego.
"""
import json
import numpy as np
from sentence_transformers import SentenceTransformer
from sqlalchemy.orm import Session
import models

# Wielojęzyczny model - działa dobrze z polskim tekstem
MODEL_NAME = "paraphrase-multilingual-MiniLM-L12-v2"
SIMILARITY_THRESHOLD = 0.80  # Próg podobieństwa (0-1), im wyższy - tym bardziej rygorystyczny

_model = None

def get_model() -> SentenceTransformer:
    """Leniwe ładowanie modelu (tylko raz przy pierwszym wywołaniu)."""
    global _model
    if _model is None:
        print(f"⏳ Ładowanie modelu embeddingów '{MODEL_NAME}'...")
        _model = SentenceTransformer(MODEL_NAME)
        print("✅ Model embeddingów gotowy.")
    return _model


def cosine_similarity(v1: list, v2: list) -> float:
    """Oblicza podobieństwo kosinusowe między dwoma wektorami."""
    a = np.array(v1)
    b = np.array(v2)
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))


def generate_embedding(text: str) -> list:
    """Generuje embedding dla podanego tekstu."""
    model = get_model()
    vector = model.encode(text, normalize_embeddings=True)
    return vector.tolist()


def assign_clusters(db: Session) -> int:
    """
    Główna funkcja grupowania.
    Przetwarza artykuły bez przypisanego cluster_id i grupuje je
    z istniejącymi artykułami o podobnej treści.

    Zwraca liczbę artykułów, którym przypisano nową lub istniejącą grupę.
    """
    # Pobierz artykuły bez embeddings
    articles_without_embedding = db.query(models.Article).filter(
        models.Article.embedding == None
    ).all()

    if not articles_without_embedding:
        print("Wszystkie artykuły mają już embeddingi. Pomijam.")
        return 0

    print(f"🔍 Generowanie embeddingów dla {len(articles_without_embedding)} artykułów...")

    # Generuj embeddingi dla nowych artykułów
    for article in articles_without_embedding:
        text = f"{article.title}. {article.llm_summary or ''}"
        embedding = generate_embedding(text)
        article.embedding = json.dumps(embedding)

    db.commit()

    # Pobierz WSZYSTKIE artykuły z embeddingami do grupowania
    all_articles = db.query(models.Article).filter(
        models.Article.embedding != None
    ).all()

    print(f"🧩 Grupowanie {len(all_articles)} artykułów...")

    # Wyznacz najwyższy istniejący cluster_id jako punkt startowy
    max_cluster = db.query(models.Article).filter(
        models.Article.cluster_id != None
    ).count()
    next_cluster_id = max_cluster + 1

    # Słownik: cluster_id -> reprezentatywny embedding (średnia grupy)
    cluster_embeddings: dict[int, list] = {}

    # Załaduj embeddingi istniejących klastrów
    for article in all_articles:
        if article.cluster_id is not None:
            emb = json.loads(article.embedding)
            if article.cluster_id not in cluster_embeddings:
                cluster_embeddings[article.cluster_id] = emb

    assigned = 0

    # Przypisz nowe artykuły do klastrów
    for article in articles_without_embedding:
        if article.embedding is None:
            continue

        emb = json.loads(article.embedding)
        best_cluster = None
        best_score = 0.0

        # Porównaj z każdym istniejącym klastrem
        for cid, centroid in cluster_embeddings.items():
            score = cosine_similarity(emb, centroid)
            if score > best_score:
                best_score = score
                best_cluster = cid

        if best_score >= SIMILARITY_THRESHOLD and best_cluster is not None:
            # Dopasowano do istniejącego klastra
            article.cluster_id = best_cluster
            print(f"  ✅ '{article.title[:60]}...' → klaster #{best_cluster} (podobieństwo: {best_score:.2f})")
        else:
            # Nowe wydarzenie - utwórz nowy klaster
            article.cluster_id = next_cluster_id
            cluster_embeddings[next_cluster_id] = emb
            print(f"  🆕 '{article.title[:60]}...' → nowy klaster #{next_cluster_id}")
            next_cluster_id += 1

        assigned += 1

    db.commit()
    print(f"✅ Grupowanie zakończone. Przypisano {assigned} artykułów.")
    return assigned
