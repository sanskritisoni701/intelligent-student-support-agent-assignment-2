import re
from pathlib import Path

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


# Locate the handbook
HANDBOOK_FILE = (
    Path(__file__).resolve().parent.parent
    / "data"
    / "student_handbook.txt"
)


def load_policy_chunks():

    with open(
        HANDBOOK_FILE,
        "r",
        encoding="utf-8"
    ) as file:

        content = file.read()

    # Split the handbook by section headings
    chunks = re.split(
        r"(?=SECTION\s+\d+\s*:)",
        content,
        flags=re.IGNORECASE
    )

    # Remove empty chunks and unnecessary whitespace
    chunks = [
        chunk.strip()
        for chunk in chunks
        if chunk.strip()
    ]

    return chunks
def search_policy(question: str):

    try:

        chunks = load_policy_chunks()

        if not chunks:
            return {
                "success": False,
                "message": "Policy document is empty."
            }

        # Convert handbook sections into numerical vectors
        vectorizer = TfidfVectorizer(
            stop_words="english"
        )

        policy_vectors = vectorizer.fit_transform(chunks)

        # Convert the student's question into a vector
        question_vector = vectorizer.transform([question])

        # Calculate similarity scores
        scores = cosine_similarity(
            question_vector,
            policy_vectors
        ).flatten()

        # Find the most relevant section
        best_index = scores.argmax()
        best_score = float(scores[best_index])

        # Avoid returning unrelated policy information
        if best_score < 0.08:

            return {
                "success": True,
                "found": False,
                "message": (
                    "The handbook does not contain "
                    "sufficient relevant information."
                ),
                "evidence": []
            }

        
        return {
            "success": True,
            "found": True,
            "evidence": [
                {
                    "chunk_id": int(best_index) + 1,
                    "content": chunks[int(best_index)],
                    "similarity": float(round(best_score, 3))
        }
    ]
}


    except FileNotFoundError:

        return {
            "success": False,
            "message": "Student handbook not found."
        }

    except ValueError as error:

        return {
            "success": False,
            "message": f"Policy retrieval error: {error}"
        }
