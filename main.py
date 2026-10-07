"""Application entry point."""
from app.application.bootstrap import build_application


def main() -> int:
    return build_application().run()


if __name__ == "__main__":
    raise SystemExit(main())
