#!/usr/bin/env python3
"""
Prompt Version Control CLI

Git-like commands for managing prompt versions.
"""

import sys
import json
import click
from pathlib import Path

from prompt_repo_enhanced import PromptRepo


@click.group()
@click.option("--repo", default=".prompt_repo.db", help="Repository database path")
@click.pass_context
def cli(ctx, repo):
    """Prompt Version Control - Git for LLM Prompts"""
    ctx.ensure_object(dict)
    ctx.obj['repo'] = PromptRepo(repo)


@cli.command()
@click.pass_context
def init(ctx):
    """Initialize a new prompt repository."""
    repo = ctx.obj['repo']
    repo.init()
    click.echo("✅ Initialized prompt repository")


@cli.command()
@click.option("-m", "--message", required=True, help="Commit message")
@click.option("-b", "--branch", default="main", help="Branch name")
@click.option("--system", default="", help="System prompt")
@click.option("--model", default="qwen2.5:7b", help="Target model")
@click.option("--tag", multiple=True, help="Tags for this commit")
@click.argument("prompt")
@click.pass_context
def commit(ctx, prompt, message, branch, system, model, tag):
    """Commit a new prompt version."""
    repo = ctx.obj['repo']
    
    # Get parent from current branch head
    parent_id = repo.get_branch(branch)
    
    version_id = repo.commit(
        prompt=prompt,
        system=system,
        model=model,
        message=message,
        branch=branch,
        parent_id=parent_id,
        tags=list(tag),
    )
    
    click.echo(f"✅ Committed: {version_id}")
    click.echo(f"   Branch: {branch}")
    click.echo(f"   Model: {model}")


@cli.command()
@click.option("-b", "--branch", default="main", help="Branch to view")
@click.option("-n", "--limit", default=10, help="Number of commits to show")
@click.pass_context
def log(ctx, branch, limit):
    """Show commit history."""
    repo = ctx.obj['repo']
    
    versions = repo.log(branch=branch, limit=limit)
    
    if not versions:
        click.echo("No commits yet.")
        return
    
    for v in versions:
        tags_str = f" [{', '.join(v.tags)}]" if v.tags else ""
        metrics_str = ""
        if v.metrics:
            if v.metrics.get('quality_score'):
                metrics_str += f" Q:{v.metrics['quality_score']:.1f}"
            if v.metrics.get('latency_ms'):
                metrics_str += f" L:{v.metrics['latency_ms']:.0f}ms"
        
        click.echo(f"\n{v.id[:8]} {v.created_at[:10]}{tags_str}{metrics_str}")
        click.echo(f"  {v.commit_message}")
        click.echo(f"  Model: {v.model} | Prompt: {len(v.prompt)} chars")


@cli.command()
@click.argument("version_id")
@click.pass_context
def show(ctx, version_id):
    """Show a specific version."""
    repo = ctx.obj['repo']
    
    try:
        v = repo.checkout(version_id)
        
        click.echo(f"\n{'='*60}")
        click.echo(f"Commit: {v.id}")
        click.echo(f"Date: {v.created_at}")
        click.echo(f"Branch: {v.branch}")
        click.echo(f"Model: {v.model}")
        if v.tags:
            click.echo(f"Tags: {', '.join(v.tags)}")
        click.echo(f"Message: {v.commit_message}")
        
        if v.metrics:
            click.echo(f"\nMetrics:")
            for key, value in v.metrics.items():
                click.echo(f"  {key}: {value}")
        
        click.echo(f"\n{'='*60}")
        click.echo("SYSTEM:")
        click.echo(v.system or "(none)")
        click.echo(f"\n{'='*60}")
        click.echo("PROMPT:")
        click.echo(v.prompt)
        click.echo(f"\n{'='*60}")
        
    except ValueError as e:
        click.echo(f"❌ Error: {e}", err=True)


@cli.command()
@click.argument("id1")
@click.argument("id2")
@click.pass_context
def diff(ctx, id1, id2):
    """Compare two versions."""
    repo = ctx.obj['repo']
    
    try:
        d = repo.diff(id1, id2)
        
        click.echo(f"\nComparing: {id1} → {id2}\n")
        
        click.echo("Prompt:")
        if d['prompt_changed']:
            click.echo(f"  Length change: {d['prompt_diff']['added']:+d} chars")
            click.echo(f"  Content changed: {d['prompt_diff']['changed']}")
        else:
            click.echo("  (no changes)")
        
        click.echo("\nSystem:")
        if d['system_changed']:
            click.echo(f"  Length change: {d['system_diff']['added']:+d} chars")
        else:
            click.echo("  (no changes)")
        
        click.echo("\nModel:")
        if d['model_changed']:
            click.echo(f"  Changed: {id1} → {id2}")
        else:
            click.echo("  (same model)")
        
        if d['metrics_diff']['comparable']:
            click.echo("\nMetrics:")
            if d['metrics_diff'].get('latency_change'):
                click.echo(f"  Latency: {d['metrics_diff']['latency_change']:+.0f}ms")
            if d['metrics_diff'].get('quality_change'):
                click.echo(f"  Quality: {d['metrics_diff']['quality_change']:+.1f}")
        
    except ValueError as e:
        click.echo(f"❌ Error: {e}", err=True)


@cli.command()
@click.argument("name")
@click.option("--from", "from_commit", default=None, help="Source commit")
@click.pass_context
def branch(ctx, name, from_commit):
    """Create a new branch."""
    repo = ctx.obj['repo']
    
    try:
        repo.branch(name, from_commit)
        click.echo(f"✅ Created branch: {name}")
    except ValueError as e:
        click.echo(f"❌ Error: {e}", err=True)


@cli.command()
@click.pass_context
def branches(ctx):
    """List all branches."""
    repo = ctx.obj['repo']
    
    branches = repo.list_branches()
    
    if not branches:
        click.echo("No branches yet.")
        return
    
    for branch in branches:
        head = repo.get_branch(branch)
        current = "main" if branch == "main" else ""
        marker = "*" if branch == "main" else " "
        click.echo(f"{marker} {branch:<20} → {head[:8] if head else '(empty)'}")


@cli.command()
@click.argument("name")
@click.argument("commit_id")
@click.pass_context
def tag(ctx, name, commit_id):
    """Create a tag."""
    repo = ctx.obj['repo']
    
    try:
        repo.tag(name, commit_id)
        click.echo(f"✅ Created tag: {name} → {commit_id[:8]}")
    except ValueError as e:
        click.echo(f"❌ Error: {e}", err=True)


@cli.command()
@click.pass_context
def tags(ctx):
    """List all tags."""
    repo = ctx.obj['repo']
    
    tags = repo.list_tags()
    
    if not tags:
        click.echo("No tags yet.")
        return
    
    for tag in tags:
        click.echo(f"  {tag}")


@cli.command()
@click.argument("source_branch")
@click.option("--into", "target_branch", default="main", help="Target branch")
@click.pass_context
def merge(ctx, source_branch, target_branch):
    """Merge a branch into another."""
    repo = ctx.obj['repo']
    
    try:
        new_id = repo.merge(source_branch, target_branch)
        click.echo(f"✅ Merged {source_branch} → {target_branch}")
        click.echo(f"   New commit: {new_id[:8]}")
    except ValueError as e:
        click.echo(f"❌ Error: {e}", err=True)


@cli.command()
@click.argument("version_id")
@click.argument("test_prompt")
@click.option("--model", default=None, help="Override model for testing")
@click.pass_context
def test(ctx, version_id, test_prompt, model):
    """Test a prompt version."""
    repo = ctx.obj['repo']
    
    try:
        from langchain_ollama import ChatOllama
        
        v = repo.checkout(version_id)
        test_model = model or v.model
        
        click.echo(f"\n🧪 Testing: {version_id[:8]}")
        click.echo(f"   Model: {test_model}")
        click.echo(f"   Test: {test_prompt[:50]}...")
        
        llm = ChatOllama(model=test_model)
        
        messages = []
        if v.system:
            messages.append({"role": "system", "content": v.system})
        messages.append({"role": "user", "content": test_prompt})
        
        import time
        start = time.time()
        response = llm.invoke(messages)
        latency = (time.time() - start) * 1000
        
        click.echo(f"\n✅ Response ({latency:.0f}ms):")
        click.echo(f"   {response.content[:200]}...")
        
        # Save metrics
        metrics = {
            "latency_ms": latency,
            "test_prompt": test_prompt,
        }
        repo.update_metrics(version_id, metrics)
        click.echo("\n💾 Metrics saved")
        
    except ImportError:
        click.echo("❌ langchain_ollama not installed", err=True)
    except ValueError as e:
        click.echo(f"❌ Error: {e}", err=True)


@cli.command()
@click.pass_context
def stats(ctx):
    """Show repository statistics."""
    repo = ctx.obj['repo']
    
    stats = repo.get_stats()
    
    click.echo("\n📊 Prompt Repository Statistics")
    click.echo(f"{'='*40}")
    click.echo(f"  Total commits:   {stats['total_commits']}")
    click.echo(f"  Total branches:  {stats['total_branches']}")
    click.echo(f"  Total tags:      {stats['total_tags']}")
    click.echo(f"  Models used:     {', '.join(stats['models_used'])}")
    click.echo()


def main():
    cli(obj={})


if __name__ == "__main__":
    main()
