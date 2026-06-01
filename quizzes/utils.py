import random

from .models import Question


def _session_key(level_id):
    return f"quiz_{level_id}_question_ids"


def _recent_key(level_id):
    return f"quiz_{level_id}_recent_ids"


def get_all_level_questions(level):
    return list(Question.objects.filter(level=level))


def select_questions_for_attempt(level, count=None, session=None):
    """
    Load all questions for the level, shuffle, optionally limit by count.
    count=None → all questions. count=N → N questions (prefer not recently used).
    """
    pool = get_all_level_questions(level)
    if not pool:
        return []

    recent = set()
    if session is not None:
        recent = set(session.get(_recent_key(level.id), []))

    if count is not None and count > 0 and len(pool) > count:
        unused = [q for q in pool if q.id not in recent]
        source = unused if len(unused) >= count else pool
        selected = random.sample(source, count)
    else:
        selected = pool[:]
        random.shuffle(selected)

    if session is not None:
        recent_list = list(recent) + [q.id for q in selected]
        session[_recent_key(level.id)] = recent_list[-100:]
        if hasattr(session, "modified"):
            session.modified = True

    return selected


def store_attempt_questions(session, level_id, questions):
    session[_session_key(level_id)] = [q.id for q in questions]
    if hasattr(session, "modified"):
        session.modified = True


def load_attempt_questions(session, level):
    ids = session.get(_session_key(level.id)) or []
    if not ids:
        return []
    by_id = {q.id: q for q in Question.objects.filter(level=level, id__in=ids)}
    return [by_id[qid] for qid in ids if qid in by_id]


def clear_attempt_questions(session, level_id):
    key = _session_key(level_id)
    if key in session:
        del session[key]
        if hasattr(session, "modified"):
            session.modified = True


def parse_question_count(request):
    """?count=all or omitted → all questions; ?count=10 → limit to 10."""
    raw = (request.GET.get("count") or "").strip().lower()
    if raw in ("", "all"):
        return None
    try:
        n = int(raw)
        return n if n > 0 else None
    except ValueError:
        return None
