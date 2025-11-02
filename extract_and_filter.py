"""
Quick QBReader API helpers

Replace INSERT_SET_HERE with a string of set names (comma-separated) when you want
to call get_top_100_questions. Example: "SET A,SET B,SET C"

Base URL used: https://www.qbreader.org/api
"""

import requests
import math
from typing import Optional, List, Dict, Any, Union
import re
from google import genai
import os
from pathlib import Path
import shlex

def get_set_list(base_url: str = "https://www.qbreader.org/api") -> List[str]:
    """
    Fetch the list of available sets from /set-list.

    Returns:
        A list of set-name strings.
    Raises:
        requests.HTTPError on non-2xx responses.
    """
    url = f"{base_url.rstrip('/')}/set-list"
    resp = requests.get(url, timeout=10)
    resp.raise_for_status()
    data = resp.json()
    # the API returns an array of set names (or objects) depending on implementation;
    # normalize to a list of strings if necessary
    if isinstance(data, list):
        # If items are strings, return them; if items are dicts with 'name' keys, extract.
        if data and isinstance(data[0], dict):
            return [item.get("name", str(item)) for item in data]
        return [str(item) for item in data]
    # fallback: if API wraps under a key
    if isinstance(data, dict):
        for k in ("sets", "setList", "data"):
            if k in data and isinstance(data[k], list):
                return [str(x) for x in data[k]]
    # if format unexpected, return an empty list
    return []


import math
from typing import List, Dict, Any, Optional
import requests

def _fetch_query_page(
    base_url: str,
    params: Dict[str, Any],
    timeout: int = 15,
) -> Dict[str, Any]:
    url = f"{base_url.rstrip('/')}/query"
    resp = requests.get(url, params=params, timeout=timeout)
    resp.raise_for_status()
    return resp.json()

def _normalize_tossups(tossup_array: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    out = []
    for t in tossup_array:
        out.append({
            "type": "tossup",
            "id": t.get("_id") or t.get("id"),
            "answer": t.get("answer", t.get("answerline", "")),
            "question": t.get("question", ""),
            "setName": t.get("setName"),
            "raw": t,
        })
    return out

def _normalize_bonuses(bonus_array: List[Dict[str, Any]], query: Optional[str] = None) -> List[Dict[str, Any]]:
    out = []
    q = (query or "").strip().lower()
    for b in bonus_array:
        raw_parts = b.get("parts") or b.get("questions")  # often a list
        # If parts is a list, try to find the part whose answer contains the query
        chosen_text = None
        if isinstance(raw_parts, list) and raw_parts:
            for part in raw_parts:
                if isinstance(part, dict):
                    part_answer = (part.get("answer") or part.get("answerline") or "").lower()
                    part_text = part.get("question") or part.get("text") or ""
                else:
                    part_answer = ""
                    part_text = str(part)
                if q and q in part_answer:
                    chosen_text = part_text
                    break
            # if no matching part, fall back to joining/first part
            if chosen_text is None:
                # if parts are dicts use their 'question' fields, otherwise join strings
                if isinstance(raw_parts[0], dict):
                    chosen_text = raw_parts[0].get("question") or raw_parts[0].get("text") or ""
                else:
                    chosen_text = " ".join(str(p) for p in raw_parts)
        else:
            # not a list — use text fields as before
            chosen_text = b.get("text") or b.get("question") or ""

        answer = b.get("answer", b.get("answerline", ""))
        out.append({
            "type": "bonus",
            "id": b.get("_id") or b.get("id"),
            "answer": answer,
            "question": chosen_text,
            "setName": b.get("setName"),
            "raw": b,
        })
    return out

#TODO: allow search by difficulty, set_list, and 
#TODO: category (literature, history, science, finearts, religion, mythology, philosophy, social science, current events, geography, other academic, and pop cultule)
#NOTE: category is capital with spaces???
#difficulty list = Pop Culture, Middle School, Easy High School, Regular High School, Hard High School, Easy College, Medium College, Regionals College, Nationals College, Open
#Note that these are listed with a key of 0-10 and a value of above

def get_top_n_questions(
    query: str,
    set_list: List[str],
    n: int,
    base_url: str = "https://www.qbreader.org/api",
    *,
    case_sensitive: bool = False,
    exact_phrase: bool = False,
    # optional: filter by difficulty (int, string, or list of ints/strings)
    difficulty: Optional[Union[int, str, List[Union[int, str]]]] = None,
    # optional: filter by category (string or list of strings); pass exact category names (e.g., "Literature")
    category: Optional[Union[str, List[str]]] = None,
    # optional: if you want to override per-request maxReturnLength cap
    request_timeout: int = 15,
    ) -> List[Dict[str, Any]]:
    """
    Pull the top `n` questions whose ANSWER contains `query`, evenly split across
    the provided set_list and evenly between tossups and bonuses per-set.

    Parameters:
        query: search string to look for inside answerlines (searchType=answer).
        set_list: list of set names (each will be queried separately).
        n: total number of questions desired across all sets and types.
        base_url: QBReader API base.
        case_sensitive, exact_phrase: forwarded to API.
        request_timeout: per-request timeout in seconds.

    Returns:
        List[dict] of normalized question dicts (type, id, answer, question, setName, raw).
    """
    if n <= 0:
        return []
    
    # If no sets were provided, treat as a single 'undefined' set
    if not set_list:
        set_list = ["undefined"]

    total_sets = len(set_list)
    base_per_set = n // total_sets
    remainder = n % total_sets

    # compute per-set allocation list
    per_set_alloc = [
        base_per_set + (1 if i < remainder else 0)
        for i in range(total_sets)
    ]
    results: List[Dict[str, Any]] = []

    # For each set, split its allocation between tossups and bonuses
    for idx, set_name in enumerate(set_list):
        per_set_count = per_set_alloc[idx]
        if per_set_count <= 0:
            continue

        # Even split between tossups and bonuses:
        # tossups = floor(per_set_count / 2)
        # bonuses = per_set_count - tossups
        # (This guarantees tossups + bonuses == per_set_count)
        tossup_count = per_set_count // 2
        bonus_count = per_set_count - tossup_count
        
        # Build common params. If set_name == "undefined" we omit 'setName'
        # so the API searches all sets (the absence of the parameter means "all").
        common_params = {
            "queryString": query,
            "searchType": "answer",
            "caseSensitive": str(bool(case_sensitive)).lower(),
            "exactPhrase": str(bool(exact_phrase)).lower(),
        }
        if set_name != "undefined":
            common_params["setName"] = set_name

        # optional difficulty filter: accept int/str or list -> join as comma-separated string
        if difficulty is not None:
            if isinstance(difficulty, (list, tuple)):
                common_params["difficulties"] = ",".join(str(d) for d in difficulty)
            else:
                common_params["difficulties"] = str(difficulty)

        # optional category filter: accept str or list -> join as comma-separated string
        if category is not None:
            if isinstance(category, (list, tuple)):
                common_params["categories"] = ",".join(str(c) for c in category)
            else:
                common_params["categories"] = str(category)

        # Fetch tossups for this set (if requested)
        if tossup_count > 0:
            params = dict(common_params)
            params.update({
                "questionType": "tossup",
                "maxReturnLength": tossup_count,
                # tossupPagination could be used for pagination; we request up to tossup_count
            })
            try:
                data = _fetch_query_page(base_url, params, timeout=request_timeout)
            except requests.HTTPError:
                # If a set/query fails, continue with others (you can change to re-raise)
                raise
            # Normalize tossups
            tossups_obj = data.get("tossups", {})
            if isinstance(tossups_obj, dict):
                tossup_arr = tossups_obj.get("questionArray", [])
            else:
                tossup_arr = tossups_obj if isinstance(tossups_obj, list) else []
            results.extend(_normalize_tossups(tossup_arr))

        # Fetch bonuses for this set (if requested)
        if bonus_count > 0:
            params = dict(common_params)
            params.update({
                "questionType": "bonus",
                "maxReturnLength": bonus_count,
            })
            try:
                data = _fetch_query_page(base_url, params, timeout=request_timeout)
            except requests.HTTPError:
                raise
            bonuses_obj = data.get("bonuses", {})
            if isinstance(bonuses_obj, dict):
                bonus_arr = bonuses_obj.get("questionArray", [])
            else:
                bonus_arr = bonuses_obj if isinstance(bonuses_obj, list) else []
            results.extend(_normalize_bonuses(bonus_arr, query))

    # Final safety: if API returned more than requested due to per-set rounding or API behavior,
    # trim to n elements (preserve order as returned: grouped by set and type).
    print(f"Found {len(results)} results, filtering to {min(n, len(results))}")
    if len(results) > n:
        results = results[:n]

    return results


def find_matches(available_sets: List[str], query: str) -> List[str]:
    """
    Return all sets from `available_sets` whose name contains `query`
    (case-insensitive).
    """
    q = (query or "").strip().lower()
    if not q:
        return []
    return [s for s in available_sets if q in s.lower()]



def select_params(available_sets: List[str]) -> Optional[tuple]:
    """
    Interactive selection for sets, difficulties, categories, plus user query and exact-phrase flag.

    Returns:
        (set_list_or_None, difficulties_csv_or_None, categories_csv_or_None, user_query_or_None, exact_phrase_bool)
    - set_list_or_None: List[str] of set names, or None meaning 'all sets'
    - difficulties_csv_or_None: comma-separated numeric difficulty keys as a string, or None
    - categories_csv_or_None: comma-separated category names as API expects, or None
    - user_query_or_None: string to search for in answers, or None to use default
    - exact_phrase_bool: True if user requested exact-phrase match, False otherwise

    Typing 'done' at the start with no selections returns None (signals caller to use defaults).
    """
    # Hardcoded options (user-specified)
    DIFFICULTY_LABELS = [
        "Pop Culture", "Middle School", "Easy High School", "Regular High School",
        "Hard High School", "National High School", "Easy College", "Medium College", "Regionals College",
        "Nationals College", "Open"
    ]  # mapped to numeric keys 0..9 (use index)

    # API-style categories (capitalized / spaced)
    CATEGORY_LABELS = [
        "Literature", "History", "Science", "Fine Arts", "Religion", "Mythology",
        "Philosophy", "Social Science", "Current Events", "Geography",
        "Other Academic", "Pop Culture"
    ]

    chosen_sets: List[str] = []
    chosen_difficulties: List[str] = []
    chosen_categories: List[str] = []

    def _prompt_list(prompt_text: str) -> str:
        val = input(prompt_text).strip()
        return val

    # --- Sets selection (search-style, allow 'all' or 'done') ---
    print("\n--- Select Sets ---")
    print("You may search sets by typing a substring; matching sets will be added automatically.")
    print("Type 'all' to select ALL sets (this will return None for sets meaning search all).")
    print("Type 'done' to finish selection (if you type 'done' with nothing selected, the whole function returns None).")

    while True:
        user = _prompt_list("Enter a set search term (or 'all' / 'done', or press Enter to skip to difficulties): ")
        if user.lower() == "done":
            if not chosen_sets and not chosen_difficulties and not chosen_categories:
                print("No selections made — returning None for all params.")
                return None
            break
        if user.lower() == "all":
            chosen_sets = None  # sentinel: None => search all sets
            print("Selected ALL sets (search will not be restricted to particular sets).")
            break
        if user == "":
            # skip sets selection
            break

        matches = find_matches(available_sets, user)
        if not matches:
            print(f"No matches found for '{user}'. Try another substring or type 'all' or 'done'.")
            continue
        added = 0
        for m in matches:
            if chosen_sets is None:
                break
            if m not in chosen_sets:
                chosen_sets.append(m)
                added += 1
        print(f"Found {len(matches)} matches — added {added} new set(s).")
        print("Current chosen sets (showing up to 20):")
        for s in chosen_sets[:20]:
            print("  -", s)
        print()

    # --- Difficulties selection ---
    print("\n--- Select Difficulties ---")
    print("Choose difficulties by label or number (comma-separated). Available options:")
    for i, lab in enumerate(DIFFICULTY_LABELS):
        print(f"  {i}. {lab}")
    print("Type 'all' to not filter by difficulty. Type 'done' to skip.")

    while True:
        user = _prompt_list("Enter difficulty(s) (e.g. '6' or 'Easy College,Medium College', 'all' or 'done'): ")
        if not user or user.lower() == "done" or user.lower() == "all":
            if user.lower() == "all":
                chosen_difficulties = None
            break
        parts = [p.strip() for p in user.split(",") if p.strip()]
        bad = []
        tmp = []
        for p in parts:
            if p.isdigit():
                idx = int(p)
                if 0 <= idx < len(DIFFICULTY_LABELS):
                    tmp.append(str(idx))
                else:
                    bad.append(p)
            else:
                found = False
                for i, lab in enumerate(DIFFICULTY_LABELS):
                    if p.lower() == lab.lower():
                        tmp.append(str(i))
                        found = True
                        break
                if not found:
                    bad.append(p)
        if bad:
            print("Unrecognized difficulty entries:", bad)
            print("Please enter numbers 0..{} or labels exactly as shown.".format(len(DIFFICULTY_LABELS)-1))
            continue
        seen = set()
        chosen_difficulties = [x for x in tmp if not (x in seen or seen.add(x))]
        print("Selected difficulties (API keys):", ",".join(chosen_difficulties))
        print("Human-readable:", ", ".join(DIFFICULTY_LABELS[int(x)] for x in chosen_difficulties))
        break

    # --- Categories selection ---
    print("\n--- Select Categories ---")
    print("Choose categories by label or number (comma-separated). Available options:")
    for i, lab in enumerate(CATEGORY_LABELS):
        print(f"  {i}. {lab}")
    print("Type 'all' to not filter by category. Type 'done' to skip.")

    while True:
        user = _prompt_list("Enter category(ies) (e.g. 'Science' or '0,2' or 'all'/'done'): ")
        if not user or user.lower() == "done" or user.lower() == "all":
            if user.lower() == "all":
                chosen_categories = None
            break
        parts = [p.strip() for p in user.split(",") if p.strip()]
        bad = []
        tmp = []
        for p in parts:
            if p.isdigit():
                idx = int(p)
                if 0 <= idx < len(CATEGORY_LABELS):
                    tmp.append(CATEGORY_LABELS[idx])
                else:
                    bad.append(p)
            else:
                matched = False
                for lab in CATEGORY_LABELS:
                    if p.lower() == lab.lower() or p.lower() == lab.replace(" ", "").lower():
                        tmp.append(lab)
                        matched = True
                        break
                if not matched:
                    bad.append(p)
        if bad:
            print("Unrecognized category entries:", bad)
            print("Please enter numbers 0..{} or labels exactly as shown.".format(len(CATEGORY_LABELS)-1))
            continue
        seen = set()
        chosen_categories = [x for x in tmp if not (x in seen or seen.add(x))]
        print("Selected categories (API names):", ", ".join(chosen_categories))
        break

    # Build return values: convert chosen lists to API-ready comma-strings
    if chosen_sets is None:
        ret_sets = None
    else:
        ret_sets = chosen_sets if chosen_sets else None

    if chosen_difficulties is None:
        ret_diff = None
    else:
        ret_diff = ",".join(chosen_difficulties) if chosen_difficulties else None

    if chosen_categories is None:
        ret_cat = None
    else:
        ret_cat = ",".join(chosen_categories) if chosen_categories else None

    # --- User query and exact-phrase (regex/exact) choice -----------------
    user_query = input("\nEnter the search query (the string to search for in answers). Press Enter to use default (Einstein): ").strip()
    if not user_query:
        user_query = None


    # Validate exact-phrase input: accept y/n or blank; re-prompt on garbage
    while True:
        exact_in = input("Use exact-phrase match? (y/N): ").strip().lower()
        if exact_in == "":
            exact_phrase_flag = False
            break
        if exact_in in ("y", "yes"):
            exact_phrase_flag = True
            break
        if exact_in in ("n", "no"):
            exact_phrase_flag = False
            break
        print("Please enter 'y' or 'n' (or press Enter for no).")

    return (ret_sets, ret_diff, ret_cat, user_query, exact_phrase_flag)


# --- helpers --------------------------------------------------------------

_RE_TAGS = re.compile(r"<[^>]+>")
_RE_WHITESPACE = re.compile(r"\s+")

def _strip_html(text: str) -> str:
    """Remove HTML tags and collapse whitespace."""
    if not text:
        return ""
    t = _RE_TAGS.sub("", text)
    t = _RE_WHITESPACE.sub(" ", t)
    return t.strip()

# sentence-finding regex:
# - Lazy-match from start up to a sentence end punctuation [.?!]
# - require that the punctuation is followed by either end-of-string OR whitespace + capital/quote/ digit
_SENTENCE_RE = re.compile(r"""
    (               # capture one sentence
      .*?           # minimal text
      [\.!?]        # sentence-ending punctuation
    )
    (?=             # only accept if followed by:
      \s+["'(\[]?[A-Z0-9]   # whitespace then optional quote/parens then uppercase/digit (next sentence start)
      |$            # or end of string
    )
""", re.VERBOSE | re.DOTALL)

def first_n_sentences(html_text: str, n: int = 2) -> str:
    """
    Return the first `n` sentences extracted from `html_text`.
    Strips HTML, collapses whitespace, and heuristically tokenizes sentences.
    If fewer than `n` sentences are present, returns the whole cleaned text.
    """
    s = _strip_html(html_text)
    if not s:
        return ""
    sentences: List[str] = []
    for m in _SENTENCE_RE.finditer(s):
        sentences.append(m.group(1).strip())
        if len(sentences) >= n:
            break
    if sentences:
        return " ".join(sentences)
    # fallback: if regex failed to find sentence boundaries, split on newline or return prefix
    parts = re.split(r"\.\s+|\?\s+|!\s+", s)
    if len(parts) <= n:
        return s
    # re-add punctuation from original by taking substring
    # conservative fallback: return first n parts joined with ". "
    return ". ".join(p.strip() for p in parts[:n]) + (". " if not s.endswith((".", "?", "!")) else "")

#TODO: implement function that goes from 2 sentence questions -> most valuable parts summary and 3 practice questions (made from just this stuff)
# return json format {overall_summary: , 
#                     power_summary: ,
#                     hard_qs: ,
#                     related entities: []}
def extract_larger_trends(query, unfiltered_sentences, filtered_sentences, client):
    if not query:
        print("Missing query, exiting")
        return

    if not unfiltered_sentences:
        print("Missing unfiltered sentences, exiting")
        return
    
    if not filtered_sentences:
        print("Missing filered sentences")
        return
    
    if len(filtered_sentences) != len(unfiltered_sentences):
        print(f"Warning, unequeal length sentence groups:\nUnfiltered: {len(unfiltered_sentences)}\nFiltered: {len(filtered_sentences)}")
    # turn filtered sentences and unfiltered into a str seperated by "\n"
    filtered_sentences_str = filtered_sentences[0]
    unfiltered_sentences_str = unfiltered_sentences[0]

    for q in unfiltered_sentences[1:]:
        unfiltered_sentences_str += f"\n{q}"
    
    for q in filtered_sentences[1:]:
        filtered_sentences_str += f"\n{q}"

    prompt = f"""Based on this information about {query}, please generate the following:
                1. Overall Summary: a string overall summary based on both the power and regular questions, which gives the reader context on the query and their interactions. I want this summary to almost read like a mini wikipedia article, so please include 4-6 sentences that make a detailed summary. 
                2. Power Summary: a string sumarry based only on the power questions, which focuses on the most common and earliest things to occur in questions. I want this summary to almost read like a mini wikipedia article, so please include 3-5 sentences that specifically adress the power topics.
                3. Hard Questions: a list of 3 strings that simulate the style of questions, but only using the most common data from the power questions
                4. Related Entities: a list of (no more than 5) strings that represent search terms that the user could search (other answers) that are related to this answer based on questions
                

                Please strictly follow the output format, and draw inspiration provided data.

                Additional Instructions:
                DO NOT say any phrases like "The user requested" or "To summarize" or anything else in this vein that makes it seem choppy/like it came from a chatbot.
                For the summaries, it should sound like it came off of a website or out of a book, it should be a cohesive paragraph.
                To select "power questions/hints", focus on phrases/clues that come up frequently and at the beginning of the clues (see power questions)

                Output format:
                {{\"overall_summary\": "",
                \"power_summary\": "",
                \"hard_questions\": ["", "", ""],
                \"related_entities\": ["", "", "", "", ""]}}
                
                
                Data:

                Power Questions (the first part of the question, which has the most impact on who buzzes first):
                {filtered_sentences_str}
                

                Regular Questions (the same questions, but not filtered to power parts):
                {unfiltered_sentences_str}
                """
    

    # get response from gemini -> send to parse function
    response = client.models.generate_content(
    model="gemini-2.5-flash-lite",
    contents=prompt,
    )

    print(response.text)


def get_api_key(var_name: str = "GEMINI_API_KEY", env_path: str = ".env") -> str:
    """Read `var_name` from .env or environment, else raise RuntimeError."""
    env_file = Path(env_path)
    if env_file.exists():
        for line in env_file.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            if key.strip() == var_name:
                return value.strip().strip('"').strip("'")

    if val := os.getenv(var_name):
        return val

    raise RuntimeError(f"{var_name} not found in {env_path!r} or environment variables.")


def get_gemini_client():
    api_key = get_api_key()
    client = genai.Client(api_key=api_key)
    return client


def parse_gemini_response(response):
    # take in messy response, filter to after first instance of { and use prior knowledge to repair to:
    # this format:  {{\"overall_summary\": "",
    #               \"power_summary\": "",
    #               \"hard_questions\": ["", "", ""],
    #               \"related_entities\": ["", "", "", "", ""]}}
    pass


def main():
    #TODO: remove random printing if just output
    """
    Per your instruction, only call the get_set_list helper here and use select_params to collect filters.
    """
    base = "https://www.qbreader.org/api"
    all_sets = get_set_list(base)
    print(f"Found {len(all_sets)} sets (showing up to first 30):")
    for s in all_sets[:30]:
        print(" -", s)

    sel = select_params(all_sets)

    # defaults
    selected_sets = None
    selected_diff = None
    selected_cat = None
    query = "einstein"
    exact_phrase = False

    if sel is None:
        # user chose nothing -> use defaults above (wildcard filters)
        pass
    else:
        selected_sets, selected_diff, selected_cat, user_query, exact_flag = sel
        # selected_sets may already be None meaning 'all'
        if user_query:
            query = user_query
        exact_phrase = bool(exact_flag)

    results = get_top_n_questions(
        query,
        selected_sets,
        n=20,
        difficulty=selected_diff,
        category=selected_cat,
        exact_phrase=exact_phrase,
    )

    print(f"Returned {len(results)} questions")
    """for r in results[:10]:
        # print the question text (not the answerline)
        print(r["type"], "\n", r.get("setName"), "\n", r.get("id"), "\n", r.get("question"), "\n", r.get("answer"))"""

    first_few_sentences = []
    for res in results:
        first_few_sentences.append(first_n_sentences(res.get("question"), n=2))  # filter to first two sentences
    unfiltered_qs = []

    client = get_gemini_client()
    extract_larger_trends(query=query, unfiltered_sentences=[res.get("question") for res in results], filtered_sentences=first_few_sentences, client=client)


if __name__ == "__main__":
    main()
