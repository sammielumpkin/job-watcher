"""Title rule: is this posting a financial analyst / FP&A role?

A title is in role when it matches at least one INCLUDE pattern and none of the EXCLUDE
patterns. Matching is case-insensitive on the title only.
"""
import re

INCLUDE = [
    r"\bfp\s*&\s*a\b", r"\bfpa\b", r"financial planning",
    r"\b(financial|finance)\s+(analyst|associate|modell?er)\b",
    r"\bfinance\s+(manager|partner|business partner|specialist)\b",
    r"\bfinance (&|and) strategy\b", r"\bstrategic finance\b", r"\bcorporate finance\b",
    r"\bcommercial finance\b", r"\bbusiness finance\b", r"\bproduct finance\b",
    r"\bfinance forecasting\b", r"\bforecasting\b", r"\bbudget(ing)?\b",
    r"\bfinancial (reporting|control)\b", r"\bcontrollership\b",
    r"\btreasury analyst\b",
]
EXCLUDE = [
    r"engineer", r"developer", r"software", r"designer", r"scientist", r"researcher",
    r"counsel", r"lawyer", r"legal", r"sales", r"account executive", r"recruit", r"talent",
    r"marketing", r"product (manager|director|lead|operations)", r"compliance", r"fraud",
    r"financial crimes?", r"\baml\b", r"\bkyc\b", r"\brisk\b", r"\bsystems?\b", r"\bworkday\b",
    r"\boracle\b", r"\berp\b", r"customer", r"support", r"trader", r"\bquant", r"partnerships?",
    r"internal audit", r"\btax\b", r"\bhead of\b", r"\bchief\b", r"\bvp\b", r"vice president",
]
_INC = re.compile("|".join(INCLUDE), re.I)
_EXC = re.compile("|".join(EXCLUDE), re.I)


def in_role(title):
    t = title or ""
    return bool(_INC.search(t)) and not _EXC.search(t)
