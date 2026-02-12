"""
Domain Layer - Business Logic & Entities

This layer contains the core business logic and domain entities.
It is INDEPENDENT of infrastructure concerns (databases, APIs, files).

Key Principles:
- Domain entities own business rules
- Repository interfaces define contracts (implementations in infrastructure/)
- Value objects ensure invariants
- No dependencies on frameworks or I/O
"""
