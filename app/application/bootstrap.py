"""Composition root for the application."""
from app.application.service import TranslatorApplication


def build_application() -> TranslatorApplication:
    return TranslatorApplication()
