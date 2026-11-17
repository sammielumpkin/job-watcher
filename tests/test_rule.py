import pytest

from jobwatcher.rule import in_role


@pytest.mark.parametrize("title", [
    "FP&A Manager", "Senior Financial Analyst, FP&A", "Finance Analyst (Financial Reporting)",
    "Associate, Strategic Finance", "Finance & Strategy Analyst", "Senior Finance Analyst",
    "Corporate Finance Intern (Summer 2027)", "Controllership Analyst (Reporting)",
    "Treasury Analyst", "Finance Forecasting Modeller", "Senior Commercial Finance Business Partner",
    "fp&a senior specialist",
])
def test_in_role(title):
    assert in_role(title)


@pytest.mark.parametrize("title", [
    "Software Engineer, Finance Applications", "Data Analyst", "Account Executive, Financial Services",
    "Financial Crime Analyst", "Credit Risk Analyst", "Product Manager, Finance Operations",
    "Head of FP&A | Credit Products", "Staff Business Systems Analyst, Oracle ERP Cloud",
    "Senior Tax Analyst", "Chef", "", None,
])
def test_not_in_role(title):
    assert not in_role(title)
