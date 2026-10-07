from app.application.bootstrap import build_application


def test_application_bootstrap() -> None:
    application = build_application()
    assert application.run() == 0
