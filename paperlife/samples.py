"""Deterministic sample data for renders, README examples, and previews.

All names and values are obviously fictional; the renders show the real
output of the generator with sample inputs.
"""

from __future__ import annotations

SAMPLE_ICE = {
    "name": "Alex Rivera",
    "phone": "(555) 012-3456",
    "address": "12 Maple Street, Anytown, USA 12345",
    "emergency_name": "Jordan Rivera",
    "emergency_phone": "(555) 012-7890",
    "blood_type": "O+",
    "allergies": "Penicillin",
    "medications": "Lisinopril 10 mg, once daily",
    "doctor": "Dr. Priya Sharma",
    "doctor_phone": "(555) 014-2222",
    "insurance": "Brightway Mutual",
    "policy": "BWM-88213-01",
    "date_prepared": "2026-08-16",
}

# Weights sum to exactly 100.00%.
SAMPLE_CASH_WEIGHTS = {
    "Housing": "27.5",
    "Food": "12.5",
    "Transportation": "7.5",
    "Utilities": "10",
    "Savings": "15",
    "Fun": "10",
    "Gifts": "7.5",
    "Emergency": "10",
}

SAMPLE_CASH = {"income": "500.17", "weights": SAMPLE_CASH_WEIGHTS}

SAMPLE_CERT_VARIANTS = [
    {"name": "Maya Chen", "as_of": "2026-08-16",
     "assets": "1234567.89", "liabilities": "234567.89"},
    {"name": "Maya Chen", "as_of": "2026-07-01",
     "assets": "1245678.90", "liabilities": "235678.90"},
    {"name": "Marcus Webb", "as_of": "2026-08-01",
     "assets": "12500.00", "liabilities": "12500.00"},
    {"name": "Dana Osei", "as_of": "2026-08-10",
     "assets": "3500.00", "liabilities": "6000.00"},
    {"name": "Maya Chen", "as_of": "2026-08-16",
     "assets": "1234567.89", "liabilities": "234567.89"},  # A4 variant
    {"name": "Elena Petrova", "as_of": "2026-06-15",
     "assets": "999999.99", "liabilities": "100000.00"},
]

SAMPLE_FREEBEE = {
    "name": "Alex Rivera",
    "phone": "(555) 012-3456",
    "contact1": "Jordan Rivera", "contact1_phone": "(555) 012-7890",
    "contact2": "Sam Rivera", "contact2_phone": "(555) 012-1111",
    "blood_type": "O+",
    "allergies": "Penicillin",
    "doctor": "Dr. Priya Sharma", "doctor_phone": "(555) 014-2222",
    "insurance": "Brightway Mutual", "policy": "BWM-88213-01",
}
