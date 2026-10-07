from app.application.bootstrap import build_application


def test_application_bootstrap_builds_local_pipeline() -> None:
    application = build_application()
    assert application.pipeline is not None
