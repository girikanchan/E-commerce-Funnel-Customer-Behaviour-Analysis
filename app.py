"""
E-commerce Funnel & Customer Behaviour Analysis
Main Application Entry Point

Architecture: MVT (Model-View-Template)
- Models: Data generation, analysis engines, SQL queries
- Views: Streamlit dashboard and UI components
- Templates: Configuration and utilities
"""

import streamlit as st
from src.views.dashboard import main

if __name__ == "__main__":
    main()

