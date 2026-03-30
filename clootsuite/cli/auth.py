"""Authentication commands for ClootSuite CLI."""

import asyncio

import click
from rich.console import Console
from rich.table import Table

from clootsuite.adapters.instagram import InstagramAdapter
from clootsuite.adapters.tiktok import TikTokAdapter
from clootsuite.adapters.x import XAdapter
from clootsuite.core.auth_manager import AuthManager
from clootsuite.core.models import Platform

console = Console()

# Adapter mapping
ADAPTERS = {
    "tiktok": TikTokAdapter(),
    "instagram": InstagramAdapter(),
    "x": XAdapter(),
}


@click.group(name="auth")
def auth() -> None:
    """Authentication management commands."""
    pass


@auth.command(name="login")
@click.argument("platform", type=click.Choice(["tiktok", "instagram", "x"]))
def login(platform: str) -> None:
    """Authenticate with a platform.

    Args:
        platform: Platform to authenticate with (tiktok, instagram, or x).
    """
    adapter = ADAPTERS.get(platform)
    if not adapter:
        console.print(f"[red]Unknown platform: {platform}[/red]")
        raise SystemExit(1)

    try:
        console.print(f"[yellow]Authenticating with {platform}...[/yellow]")
        access_token = asyncio.run(adapter.authenticate())
        console.print(
            f"[green]✓ Successfully authenticated with {platform}[/green]"
        )
    except NotImplementedError as e:
        console.print(f"[red]✗ {str(e)}[/red]")
        raise SystemExit(1)
    except Exception as e:
        console.print(f"[red]✗ Authentication failed: {str(e)}[/red]")
        raise SystemExit(1)


@auth.command(name="status")
def status() -> None:
    """Show authentication status for all platforms."""
    table = Table(title="Authentication Status")
    table.add_column("Platform", style="cyan")
    table.add_column("Status", style="magenta")

    for platform_name in ["tiktok", "instagram", "x"]:
        platform = Platform(platform_name)
        credentials = AuthManager.retrieve_credentials(platform)

        if credentials:
            status_text = "[green]✓ Authenticated[/green]"
        else:
            status_text = "[red]✗ Not authenticated[/red]"

        table.add_row(platform_name.capitalize(), status_text)

    console.print(table)


@auth.command(name="logout")
@click.argument("platform", type=click.Choice(["tiktok", "instagram", "x"]))
def logout(platform: str) -> None:
    """Logout from a platform.

    Args:
        platform: Platform to logout from (tiktok, instagram, or x).
    """
    try:
        platform_enum = Platform(platform)
        AuthManager.delete_credentials(platform_enum)
        console.print(f"[green]✓ Logged out from {platform}[/green]")
    except Exception as e:
        console.print(f"[red]✗ Logout failed: {str(e)}[/red]")
        raise SystemExit(1)
