import pytest

from manas.cli.tui import MANASApp, Splash


@pytest.mark.asyncio
async def test_tui_launches_to_splash(monkeypatch, tmp_path):
    monkeypatch.setenv("MANAS_HOME", str(tmp_path / "home"))
    app = MANASApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        assert isinstance(app.screen, Splash)
        assert app.screen.query_one("#wordmark") is not None
