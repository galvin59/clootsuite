"""ClootSuite CLI entry point."""

import click

from clootsuite import __version__

from .auth import auth
from .post import post


@click.group()
@click.version_option(version=__version__, prog_name="cloot")
def cli() -> None:
    """ClootSuite: Multi-platform video publishing CLI.

    Publish videos to TikTok, Instagram, and X in one command.
    """
    pass


cli.add_command(auth)
cli.add_command(post)

if __name__ == "__main__":
    cli()
