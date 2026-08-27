from __future__ import annotations

import asyncio

from textual.app import App, ComposeResult
from textual.containers import Center, Container, Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import Button, Footer, Header, Input, Label, ListItem, ListView, ProgressBar, Static

from crowdforge.simulation.engine import SimulationEngine
from crowdforge.simulation.models import ProductScenario, SimulationConfig
from crowdforge.cli.app import repository


DISCLAIMER = "Synthetic perspectives under selected assumptions — not real-world survey statistics."


class Splash(Screen):
    BINDINGS = [("q", "app.quit", "Quit")]

    def compose(self) -> ComposeResult:
        with Center():
            with Vertical(id="hero"):
                yield Static("CROWD FORGE", id="wordmark")
                yield Label("Synthetic Society Simulator", id="tagline")
                yield Button("New simulation", id="new", variant="primary")
                yield Button("Recent simulations", id="recent")
                yield Label("One idea. Many perspectives.", classes="muted")
        yield Footer()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "new":
            self.app.push_screen(Setup())
        else:
            self.app.push_screen(Recent())


class Setup(Screen):
    BINDINGS = [("escape", "app.pop_screen", "Back")]

    def compose(self) -> ComposeResult:
        yield Header()
        with Center():
            with Vertical(id="setup"):
                yield Static("What are you testing?", classes="question")
                yield Input(placeholder="AI fitness coach for college students", id="idea")
                yield Static("Price in ₹", classes="question")
                yield Input(value="399", type="number", id="price")
                with Horizontal(classes="fields"):
                    yield Input(value="100", type="integer", id="population")
                    yield Input(value="30", type="integer", id="days")
                    yield Input(value="42", type="integer", id="seed")
                yield Label("Population  ·  Days  ·  Seed", classes="muted")
                yield Button("Forge society", id="run", variant="primary")
        yield Footer()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id != "run":
            return
        idea = self.query_one("#idea", Input).value.strip()
        if not idea:
            self.notify("Tell CrowdForge what you want to test.", severity="warning")
            return
        scenario = ProductScenario(name=idea, description=idea, target_audience="Indian consumers",
                                   price=float(self.query_one("#price", Input).value or 0), pricing_model="monthly", category=idea)
        config = SimulationConfig(population_size=int(self.query_one("#population", Input).value or 100),
                                  days=int(self.query_one("#days", Input).value or 30), seed=int(self.query_one("#seed", Input).value or 42))
        self.app.push_screen(Running(scenario, config))


class Running(Screen):
    BINDINGS = [("p", "pause", "Pause")]

    def __init__(self, scenario: ProductScenario, config: SimulationConfig) -> None:
        super().__init__()
        self.scenario, self.config = scenario, config

    def compose(self) -> ComposeResult:
        yield Header()
        with Center():
            with Vertical(id="running"):
                yield Static("CREATING SOCIETY", id="status")
                yield ProgressBar(total=self.config.days, id="progress")
                yield Label("Generating persistent people and relationships…", id="activity")
                yield Label(DISCLAIMER, classes="muted")
        yield Footer()

    def on_mount(self) -> None:
        self.run_worker(self._simulate(), exclusive=True)

    async def _simulate(self) -> None:
        def progress(day: int, total: int, message: str) -> None:
            self.query_one("#progress", ProgressBar).update(progress=day)
            self.query_one("#status", Static).update(f"DAY {day:02d} / {total:02d}   ● RUNNING")
            self.query_one("#activity", Label).update(message)
        result = await SimulationEngine().run(self.scenario, self.config, progress)
        await asyncio.to_thread(repository().save, result)
        self.app.push_screen(Results(result))


class Results(Screen):
    BINDINGS = [("a", "agents", "Agents"), ("escape", "home", "Home")]

    def __init__(self, result) -> None:
        super().__init__()
        self.result = result

    def compose(self) -> ComposeResult:
        s = self.result.summary
        yield Header()
        with Container(id="results"):
            yield Static("SIMULATION COMPLETE", id="status")
            yield Static(f"[bold]{self.result.scenario.name}[/bold]\n\nPositive  {s.sentiment['positive']:.0%}     Neutral  {s.sentiment['neutral']:.0%}     Negative  {s.sentiment['negative']:.0%}\nPurchase intent  {s.average_purchase_intent:.0%}\nOpinion changes  {s.opinion_changes}", id="metrics")
            yield Static("\n".join(f"• {item}" for item in s.insights), id="insights")
            yield Label(DISCLAIMER, classes="muted")
            with Horizontal():
                yield Button("Explore agents [A]", id="agents", variant="primary")
                yield Button("Home", id="home")
        yield Footer()

    def action_agents(self) -> None:
        self.app.push_screen(AgentBrowser(self.result.agents))

    def action_home(self) -> None:
        self.app.pop_to_root()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        self.action_agents() if event.button.id == "agents" else self.action_home()


class AgentBrowser(Screen):
    BINDINGS = [("escape", "app.pop_screen", "Back")]

    def __init__(self, agents) -> None:
        super().__init__(); self.agents = agents

    def compose(self) -> ComposeResult:
        yield Header()
        with Horizontal(id="browser"):
            yield ListView(*[ListItem(Label(f"{a.name}\n[dim]{a.location} · {a.opinion.sentiment}[/dim]"), id=a.id) for a in self.agents], id="agent-list")
            yield Static("Select a synthetic person", id="agent-detail")
        yield Footer()

    def on_list_view_highlighted(self, event: ListView.Highlighted) -> None:
        if not event.item or not event.item.id:
            return
        a = next(agent for agent in self.agents if agent.id == event.item.id)
        memories = "\n".join(f"• Day {m.day}: {m.content}" for m in a.relevant_memories(999, 4)) or "• No salient memories"
        contradictions = "\n".join(f"• {x}" for x in a.contradictions) or "• None recorded"
        self.query_one("#agent-detail", Static).update(
            f"[bold cyan]{a.name.upper()}[/bold cyan]\n{a.age} · {a.location} · {a.occupation}\n\n[bold]Current stance[/bold]\n{a.opinion.sentiment.title()} · purchase intent {a.opinion.purchase_intent:.0%}\n\n[bold]Goals[/bold]\n" + "\n".join(f"• {x}" for x in a.goals) + f"\n\n[bold]Contradictions[/bold]\n{contradictions}\n\n[bold]Relevant memories[/bold]\n{memories}")


class Recent(Screen):
    BINDINGS = [("escape", "app.pop_screen", "Back")]

    def compose(self) -> ComposeResult:
        yield Header()
        runs = repository().list_runs()
        with Container(id="results"):
            yield Static("RECENT SIMULATIONS", id="status")
            yield Static("\n\n".join(f"[bold]{r.run_id}[/bold]\n{r.population_size} people · {r.days} days · intent {r.average_purchase_intent:.0%}" for r in runs[:10]) or "No saved simulations yet.")
        yield Footer()


class CrowdForgeApp(App):
    TITLE = "CrowdForge"
    CSS = """
    Screen { background: #090d14; color: #dce7ef; }
    #hero { width: 58; height: auto; padding: 3 5; margin-top: 5; align: center middle; background: #101823; border: round #2b91a8; }
    #wordmark { text-align: center; text-style: bold; color: #72e1d1; padding: 1; }
    #tagline { text-align: center; margin-bottom: 2; color: #9fb4c4; }
    Button { width: 100%; margin: 1 0 0 0; }
    Button.-primary { background: #168c87; }
    .muted { color: #718697; margin-top: 1; text-align: center; }
    #setup, #running { width: 72; height: auto; margin-top: 3; padding: 2 4; background: #101823; }
    .question { margin-top: 1; text-style: bold; }
    Input { margin: 1 0; border: tall #294452; }
    .fields { height: 5; }
    .fields Input { width: 1fr; margin-right: 1; }
    #status { color: #72e1d1; text-style: bold; margin-bottom: 2; }
    #activity { margin: 2 0; text-align: center; }
    #results { width: 86; height: auto; margin: 3 5; padding: 2 4; background: #101823; border-left: thick #168c87; }
    #metrics { padding: 1 2; background: #131f2d; }
    #insights { margin: 2 0; }
    #browser { padding: 1 2; }
    #agent-list { width: 36%; border-right: solid #294452; }
    #agent-detail { width: 64%; padding: 2 4; }
    """

    def on_mount(self) -> None:
        self.push_screen(Splash())
