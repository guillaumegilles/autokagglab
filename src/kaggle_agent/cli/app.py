"""kaggle-agent CLI application."""

import typer

from kaggle_agent.cli import baseline as baseline_cmd
from kaggle_agent.cli import init as init_cmd
from kaggle_agent.cli import status as status_cmd
from kaggle_agent.cli import validate as validate_cmd

app = typer.Typer(
    name="kaggle-agent",
    help="Autonomous Kaggle research harness (offline, single-user).",
    no_args_is_help=True,
)

init_cmd.register(app)
validate_cmd.register(app)
baseline_cmd.register(app)
status_cmd.register(app)
