# tests/test_sql_filters.py

import pytest
from services.sql_filters import escape_in_list, form_where_clause, apply_date_filter

def test_escape_in_list_basic():
    """Test escaping a basic list of strings for SQL IN clause."""
    values = ["US", "Canada", "O'Reilly"]
    result = escape_in_list(values)
    assert result == "US', 'Canada', 'O''Reilly"

def test_escape_in_list_empty():
    """Test escaping an empty list returns empty string."""
    assert escape_in_list([]) == ""

def test_form_where_clause_full_filters():
    """Test WHERE clause generation with all filters provided."""
    clauses = form_where_clause(
        date_range=["2023-01-01", "2023-01-31"],
        country=["US", "Canada"],
        genre=["Rock"],
        artist=["Queen"]
    )
    assert any("DATE(i.InvoiceDate)" in clause for clause in clauses)
    assert any("i.BillingCountry IN" in clause for clause in clauses)
    assert any("g.Name IN" in clause for clause in clauses)
    assert any("ar.Name IN" in clause for clause in clauses)

def test_form_where_clause_partial_filters():
    """Test WHERE clause generation with only genre and artist."""
    clauses = form_where_clause(
        genre=["Jazz"],
        artist=["Miles Davis"]
    )
    assert len(clauses) == 2
    assert "g.Name IN" in clauses[0]
    assert "ar.Name IN" in clauses[1]

def test_form_where_clause_empty():
    """Test WHERE clause generation with no filters returns empty list."""
    assert form_where_clause() == []

def test_apply_date_filter_with_range():
    """Test SQL JOIN clause with date filtering."""
    clause = apply_date_filter(["2023-01-01", "2023-01-31"])
    assert "JOIN Invoice i ON i.InvoiceId = e.InvoiceId" in clause
    assert "DATE(i.InvoiceDate) BETWEEN" in clause

def test_apply_date_filter_without_range():
    """Test SQL JOIN clause without date filtering."""
    clause = apply_date_filter(None)
    assert clause == "JOIN Invoice i ON i.InvoiceId = e.InvoiceId"
