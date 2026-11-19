# Aks98068 animated GitHub profile

## Install

1. Open your profile repository: `https://github.com/Aks98068/Aks98068`.
2. Download and extract this package.
3. Copy `README.md`, `scripts/`, `.github/`, `cards/`, `data/` and `requirements.txt` into the root of that repository.
4. Ensure the repository is **public** and named exactly `Aks98068`.
5. Open **Settings → Actions → General → Workflow permissions** and allow actions to read and write repository contents.
6. Go to **Actions → Refresh GitHub profile cards → Run workflow**.
7. After the first successful run, the generated SVG cards will appear in `cards/` and render in the profile README.

## Preview locally (PowerShell)

```powershell
$env:GH_TOKEN = "YOUR_GITHUB_TOKEN"
$env:GITHUB_USERNAME = "Aks98068"
python .\scripts\render_readme_cards.py
```

For a static screenshot-ready version:

```powershell
$env:STATIC = "1"
python .\scripts\render_readme_cards.py
Remove-Item Env:STATIC
```

Use a fine-grained token only if you run locally and need one; grant read access to public profile data. Do not commit tokens. GitHub Actions uses the built-in `GITHUB_TOKEN` secret.

## Notes

- The script reads contribution calendar data and pinned repositories from GitHub GraphQL.
- The contribution graph is based on the activity GitHub exposes to the authenticated token.
- Pin the repositories you want featured on your GitHub profile. The first two pinned repositories are used for the project cards. If fewer than two are pinned, the second card links to your repositories page.
- SVG animations are decorative; GitHub may cache images, so refreshed cards can take a little time to update.
- GitHub sanitizes README HTML. This setup uses Markdown links and image tags, while animation and styling live inside each SVG.
- The script uses system font stacks (Georgia/Arial) to avoid fragile remote-font dependencies. You can add embedded WOFF fonts later if you want an exact custom typeface.
