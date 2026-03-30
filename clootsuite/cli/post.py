"""Publishing commands for ClootSuite CLI."""

import asyncio
from pathlib import Path

import click
from rich.console import Console
from rich.progress import Progress
from rich.table import Table

from clootsuite.core.models import Platform, PostRequest
from clootsuite.core.publisher import Publisher

console = Console()


@click.command(name="post")
@click.argument("video", type=click.Path(exists=True, dir_okay=False))
@click.option(
    "--caption",
    "-c",
    required=True,
    help="Post caption/description.",
)
@click.option(
    "--platforms",
    "-p",
    multiple=True,
    type=click.Choice(["tiktok", "instagram", "x"]),
    required=True,
    help="Platforms to publish to.",
)
@click.option(
    "--hashtags",
    "-t",
    multiple=True,
    help="Hashtags to include.",
)
def post(
    video: str,
    caption: str,
    platforms: tuple[str, ...],
    hashtags: tuple[str, ...],
) -> None:
    """Publish a video to multiple platforms.

    Args:
        video: Path to video file.
        caption: Post caption.
        platforms: Platforms to publish to.
        hashtags: Hashtags to include.
    """
    # Validate video file
    video_path = Path(video)
    if not video_path.exists():
        console.print(f"[red]✗ Video file not found: {video}[/red]")
        raise SystemExit(1)

    if not video_path.is_file():
        console.print(f"[red]✗ Not a file: {video}[/red]")
        raise SystemExit(1)

    # Convert platform strings to enum
    try:
        platform_enums = [Platform(p) for p in platforms]
    except ValueError as e:
        console.print(f"[red]✗ Invalid platform: {str(e)}[/red]")
        raise SystemExit(1)

    # Create post request
    post_request = PostRequest(
        video_path=str(video_path.absolute()),
        caption=caption,
        platforms=platform_enums,
        hashtags=list(hashtags) if hashtags else None,
    )

    console.print(
        f"[cyan]Publishing to: {', '.join(str(p) for p in platforms)}[/cyan]"
    )

    # Publish
    try:
        publisher = Publisher()
        results = asyncio.run(publisher.publish(post_request))

        # Display results
        _display_results(results)

        # Exit with error if any failed
        if any(not r.success for r in results):
            raise SystemExit(1)

    except Exception as e:
        console.print(f"[red]✗ Publishing failed: {str(e)}[/red]")
        raise SystemExit(1)


def _display_results(results: list) -> None:
    """Display publishing results in a table.

    Args:
        results: List of PostResult objects.
    """
    table = Table(title="Publishing Results")
    table.add_column("Platform", style="cyan")
    table.add_column("Status", style="magenta")
    table.add_column("Post ID / Error", style="yellow")

    for result in results:
        status = "[green]✓ Success[/green]" if result.success else "[red]✗ Failed[/red]"
        info = result.post_id or result.error or ""
        platform_name = result.platform.value if isinstance(result.platform, Platform) else str(result.platform)
        table.add_row(platform_name.capitalize(), status, info)

    console.print(table)
