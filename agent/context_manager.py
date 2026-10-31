
from memory.memory_manager import get_memories


def build_context(student_id, question):

    """
    Select relevant student memory
    based on the current question.
    """

    memories = get_memories(
    student_id=student_id,
    authenticated_student_id=student_id
)

    question_lower = question.lower()

    relevant_categories = []

    # 1. Check specific programme-related questions FIRST
    if any(word in question_lower for word in [
        "programme", "program", "degree",
        "course", "qualification"
    ]):

        relevant_categories = [
            "programme"
        ]

    # 2. Check language-related questions
    elif any(word in question_lower for word in [
        "language", "english", "hindi"
    ]):

        relevant_categories = [
            "preferred_language"
        ]

    # 3. Check learning-related questions
    elif any(word in question_lower for word in [
        "explain", "learning", "study",
        "understand", "academic", "topic"
    ]):

        relevant_categories = [
            "programme",
            "preferred_language",
            "response_preference",
            "learning_preference"
        ]

    # 4. Check response preference questions
    elif any(word in question_lower for word in [
        "response", "preference", "style",
        "simple", "detailed"
    ]):

        relevant_categories = [
            "response_preference",
            "learning_preference"
        ]

    # 5. Select only relevant saved information
    selected_memories = {
        category: value
        for category, value in memories.items()
        if category in relevant_categories
    }

    # 6. Prepare the context
    if selected_memories:

        return (
            "RELEVANT STUDENT MEMORY:\n"
            + str(selected_memories)
        )

    return "No additional saved context is relevant."
