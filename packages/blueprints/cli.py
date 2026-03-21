#!/usr/bin/env python3
"""
Blueprint CLI - Manage Your Prompt Library

Commands:
  save    - Save a new blueprint
  list    - List all blueprints
  test    - Test expansion
  search  - Search blueprints
  delete  - Remove a blueprint
  rate    - Rate a blueprint
  stats   - Show statistics
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import click
from expander import BlueprintLibrary, create_example_library


@click.group()
def cli():
    """Prompt Blueprints - Save and reuse your best prompts"""
    pass


@cli.command()
@click.argument("name")
@click.argument("trigger")
@click.argument("full_prompt")
@click.option("--tag", "-t", multiple=True, help="Tags (can use multiple)")
@click.option("--notes", "-n", default="", help="Personal notes")
def save(name, trigger, full_prompt, tag, notes):
    """Save a new blueprint.
    
    Example:
      blueprints save streetpunk "like a streetpunk" "Write in urban slang..."
    """
    lib = BlueprintLibrary()
    
    bp_id = lib.save(
        name=name,
        trigger=trigger,
        full_prompt=full_prompt,
        tags=list(tag),
        notes=notes,
    )
    
    click.echo(f"✅ Saved blueprint: {name}")
    click.echo(f"   ID: {bp_id}")
    click.echo(f"   Trigger: {trigger}")
    click.echo(f"   Tags: {', '.join(tag) if tag else '(none)'}")


@cli.command()
@click.option("--tag", "-t", default=None, help="Filter by tag")
def list(tag):
    """List all blueprints."""
    lib = BlueprintLibrary()
    
    blueprints = lib.list_all(tag=tag)
    
    if not blueprints:
        click.echo("No blueprints yet. Use 'save' to add one!")
        click.echo("\nExample:")
        click.echo("  blueprints save streetpunk 'like a streetpunk' 'Write in urban slang...'")
        return
    
    click.echo(f"\n📚 Your Blueprints ({len(blueprints)}):\n")
    
    for bp in blueprints:
        stars = "⭐" * int(bp.rating) if bp.rating > 0 else ""
        click.echo(f"  {bp.name:<20} | {bp.trigger:<25} | {bp.usage_count:>3} uses {stars}")
        if bp.tags:
            click.echo(f"                       Tags: {', '.join(bp.tags)}")


@cli.command()
@click.argument("text")
def test(text):
    """Test blueprint expansion.
    
    Example:
      blueprints test "Explain quantum like a streetpunk"
    """
    lib = BlueprintLibrary()
    
    # Find matching blueprints
    matches = lib.find_by_trigger(text)
    
    if not matches:
        click.echo("❌ No blueprints found in text")
        click.echo("\nYour text:")
        click.echo(f"  {text}")
        return
    
    click.echo(f"\n🔍 Found {len(matches)} blueprint(s):\n")
    
    for bp in matches:
        click.echo(f"  {bp.name}: {bp.trigger}")
    
    # Show expanded version
    expanded = lib.expand(text)
    
    click.echo(f"\n📝 Expanded:\n")
    click.echo(f"  {expanded}")


@cli.command()
@click.argument("query")
def search(query):
    """Search blueprints."""
    lib = BlueprintLibrary()
    
    results = lib.search(query)
    
    if not results:
        click.echo(f"❌ No blueprints matching: {query}")
        return
    
    click.echo(f"\n🔍 Search results for '{query}':\n")
    
    for bp in results:
        click.echo(f"  {bp.name}")
        click.echo(f"     Trigger: {bp.trigger}")
        click.echo(f"     Tags: {', '.join(bp.tags)}")
        click.echo(f"     Uses: {bp.usage_count}")
        click.echo()


@cli.command()
@click.argument("name")
def delete(name):
    """Delete a blueprint."""
    lib = BlueprintLibrary()
    
    # Find by name or ID
    bp = None
    for blueprint_id, blueprint in lib.blueprints.items():
        if blueprint.name == name or blueprint_id == name:
            bp = blueprint
            break
    
    if not bp:
        click.echo(f"❌ Blueprint not found: {name}")
        return
    
    click.confirm(f"Delete blueprint '{bp.name}'?", abort=True)
    
    lib.delete(bp.id)
    click.echo(f"✅ Deleted: {bp.name}")


@cli.command()
@click.argument("name")
@click.argument("rating", type=click.FloatRange(0, 5))
def rate(name, rating):
    """Rate a blueprint (0-5 stars)."""
    lib = BlueprintLibrary()
    
    # Find by name or ID
    bp = None
    for blueprint_id, blueprint in lib.blueprints.items():
        if blueprint.name == name or blueprint_id == name:
            bp = blueprint
            break
    
    if not bp:
        click.echo(f"❌ Blueprint not found: {name}")
        return
    
    lib.rate(bp.id, rating)
    stars = "⭐" * int(rating)
    click.echo(f"✅ Rated '{bp.name}': {stars}")


@cli.command()
def stats():
    """Show library statistics."""
    lib = BlueprintLibrary()
    
    stats = lib.get_stats()
    
    click.echo("\n📊 Blueprint Library Statistics\n")
    click.echo(f"  Total blueprints:  {stats['total_blueprints']}")
    click.echo(f"  Total uses:        {stats['total_uses']}")
    click.echo(f"  Average rating:    {stats['average_rating']:.1f}⭐")
    
    if stats['most_used']:
        click.echo(f"  Most used:         {stats['most_used']['name']} ({stats['most_used']['usage_count']} uses)")
    
    click.echo()


@cli.command()
def init():
    """Initialize with example blueprints."""
    if click.confirm("This will add 8 example blueprints. Continue?"):
        lib = create_example_library()
        click.echo(f"✅ Initialized with {len(lib.blueprints)} blueprints")
        click.echo("\nRun 'blueprints list' to see them")


def main():
    cli()


if __name__ == "__main__":
    main()
