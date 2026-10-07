from app.application.bootstrap import build_application


def test_application_bootstrap_is_lazy() -> None:
    application = build_application()
    assert application.pipeline is None
    assert application._pipeline_factory is not None
