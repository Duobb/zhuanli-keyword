def generate_fallback_queries(original_query):
    """
    Generate query strings according to the user's fallback logic.
    Example: G06F3/01
    1. G06F3/01
    2. G06F3*
    3. G06F*
    4. G06*
    ...
    """
    original_query = original_query.strip()
    if not original_query:
        return
        
    yield original_query
    
    if "/" in original_query:
        base = original_query.split("/")[0]
        yield base + "*"
        for i in range(len(base) - 1, 0, -1):
            yield base[:i] + "*"
    else:
        for i in range(len(original_query) - 1, 0, -1):
            yield original_query[:i] + "*"

def perform_search(query, document_data):
    """
    Searches the document_data (list of dicts from parse_document)
    for the exact or fallback IPC query.
    Returns: (matched_query, list_of_matches) or (None, [])
    """
    for q in generate_fallback_queries(query):
        matches = []
        for row in document_data:
            ipc_text = row.get("ipc_text", "")
            if q in ipc_text:
                matches.append(row)
                
        if matches:
            return q, matches
                
    return None, []

def reverse_search(keyword, document_data):
    """
    Given a keyword, find all rows that contain it in keywords_text
    or context_text, and return them.
    """
    matches = []
    for row in document_data:
        kw = row.get("keywords_text", "")
        ctx = row.get("context_text", "")
        
        if keyword in kw or keyword in ctx:
            matches.append(row)
            
    return matches
