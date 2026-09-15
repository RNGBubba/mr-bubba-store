#!/usr/bin/env python3
"""
Mr Bubba Services - GitHub Pages Deployment Script
Deploys a built website to GitHub Pages under the RNGBubba account.
"""

import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from urllib.parse import quote

GITHUB_USERNAME = "RNGBubba"
GITHUB_REMOTE = f"git@github.com:{GITHUB_USERNAME}"


def run(cmd, cwd=None, check=True, capture=True):
    """Run a shell command and return the result."""
    result = subprocess.run(
        cmd, shell=True, cwd=cwd,
        capture_output=capture, text=True
    )
    if check and result.returncode != 0:
        raise RuntimeError(f"Command failed: {cmd}\n{result.stderr}")
    return result


def deploy_site(site_dir: Path, repo_name: str, cname: str = "") -> dict:
    """
    Deploy a website directory to GitHub Pages.
    
    Args:
        site_dir: Path to the built website files
        repo_name: Name for the GitHub repository (slug)
        cname: Optional custom domain
    
    Returns:
        dict with 'success', 'url', 'repo_url', 'error'
    """
    site_dir = Path(site_dir)
    if not site_dir.exists():
        return {"success": False, "error": f"Site directory not found: {site_dir}"}
    
    if not (site_dir / "index.html").exists():
        return {"success": False, "error": "No index.html found in site directory"}

    # Sanitize repo name
    repo_slug = re.sub(r'[^a-z0-9-]', '', repo_name.lower().replace(" ", "-"))
    if not repo_slug:
        repo_slug = f"site-{int(time.time())}"

    repo_full = f"{GITHUB_USERNAME}/{repo_slug}"
    repo_url = f"https://github.com/{repo_full}"
    live_url = f"https://{GITHUB_USERNAME}.github.io/{repo_slug}"

    # Create CNAME file if custom domain specified
    if cname:
        (site_dir / "CNAME").write_text(cname.strip(), encoding="utf-8")

    # Create .nojekyll to bypass Jekyll processing
    (site_dir / ".nojekyll").write_text("", encoding="utf-8")

    # Create GitHub Actions workflow for Pages
    workflow_dir = site_dir / ".github" / "workflows"
    workflow_dir.mkdir(parents=True, exist_ok=True)
    workflow_content = f"""name: Deploy to GitHub Pages

on:
  push:
    branches: [gh-pages]
  workflow_dispatch:

permissions:
  contents: read
  pages: write
  id-token: write

concurrency:
  group: "pages"
  cancel-in-progress: false

jobs:
  deploy:
    environment:
      name: github-pages
      url: ${{{{ steps.deployment.outputs.page_url }}}}
    runs-on: ubuntu-latest
    steps:
      - name: Checkout
        uses: actions/checkout@v4
        with:
          ref: gh-pages
      - name: Setup Pages
        uses: actions/configure-pages@v4
      - name: Upload artifact
        uses: actions/upload-pages-artifact@v3
        with:
          path: '.'
      - name: Deploy to GitHub Pages
        id: deployment
        uses: actions/deploy-pages@v4
"""
    (workflow_dir / "pages.yml").write_text(workflow_content, encoding="utf-8")

    # Initialize git and push
    try:
        run("git init", cwd=site_dir)
        run("git checkout -b gh-pages", cwd=site_dir)
        run("git add .", cwd=site_dir)
        run('git commit -m "Initial website deployment"', cwd=site_dir)
        run(f"git remote add origin {GITHUB_REMOTE}/{repo_slug}.git", cwd=site_dir)
        
        # Try to create repo via gh CLI
        result = subprocess.run(
            ["gh", "repo", "create", repo_slug, "--public", "--source=.", "--remote=origin", "--push"],
            cwd=site_dir, capture_output=True, text=True, timeout=60
        )
        
        if result.returncode != 0:
            # Fallback: push directly
            push_result = subprocess.run(
                ["git", "push", "-u", "origin", "gh-pages", "--force"],
                cwd=site_dir, capture_output=True, text=True, timeout=60
            )
            if push_result.returncode != 0:
                return {"success": False, "error": f"Push failed: {push_result.stderr}"}

        # Enable Pages via API
        pages_result = subprocess.run(
            ["gh", "api", f"repos/{repo_full}/pages",
             "--method", "POST",
             "-f", "source[branch]=gh-pages",
             "-f", "source[path]=/"],
            capture_output=True, text=True, timeout=30
        )

        # Set CNAME if provided
        if cname:
            subprocess.run(
                ["gh", "api", f"repos/{repo_full}/pages",
                 "--method", "PUT",
                 "-f", f"cname={cname.strip()}"],
                capture_output=True, text=True, timeout=30
            )

        return {
            "success": True,
            "url": live_url,
            "repo_url": repo_url,
            "repo_name": repo_slug,
            "cname": cname or ""
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


def update_site(site_dir: Path) -> dict:
    """Update an existing deployed site with new content."""
    site_dir = Path(site_dir)
    if not site_dir.exists():
        return {"success": False, "error": f"Directory not found: {site_dir}"}

    try:
        run("git add .", cwd=site_dir)
        run('git commit -m "Update website content"', cwd=site_dir)
        run("git push origin gh-pages", cwd=site_dir)
        return {"success": True}
    except Exception as e:
        return {"success": False, "error": str(e)}


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Deploy to GitHub Pages")
    parser.add_argument("site_dir", help="Path to the built website")
    parser.add_argument("--repo-name", required=True, help="Repository name")
    parser.add_argument("--cname", default="", help="Custom domain")
    args = parser.parse_args()

    result = deploy_site(Path(args.site_dir), args.repo_name, args.cname)
    print(json.dumps(result, indent=2) if "import json" in dir() else result)
