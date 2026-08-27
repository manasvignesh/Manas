from manas.cli import prompts


def test_interactive_setup_builds_shared_models(monkeypatch):
    integers = iter([3, 100, 1, 30, 42])
    monkeypatch.setattr(prompts.Prompt, "ask", lambda *args, **kwargs: "AI fitness coach")
    monkeypatch.setattr(prompts.FloatPrompt, "ask", lambda *args, **kwargs: 399.0)
    monkeypatch.setattr(prompts.IntPrompt, "ask", lambda *args, **kwargs: next(integers))
    setup = prompts.ask_new_simulation(prompts.Console())
    assert setup is not None
    assert setup.scenario.price == 399
    assert setup.scenario.pricing_model == "monthly"
    assert setup.config.population_size == 100
    assert setup.config.days == 30
    assert setup.config.seed == 42

