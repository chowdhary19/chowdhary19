# Put this on your GitHub profile

## 1. Create the profile repository

Create a **public** repository whose name is exactly your GitHub username. Put `README.md` at the repository root.

Upload this entire folder, including the hidden `.github` directory.

```text
<your-username>/
├── .github/workflows/
├── assets/
├── scripts/
├── README.md
├── SETUP.md
└── requirements-dev.txt
```

## 2. Push it

```bash
git init
git add .
git commit -m "build profile"
git branch -M main
git remote add origin https://github.com/<your-username>/<your-username>.git
git push -u origin main
```

## 3. Hydrate the real GitHub history

After the repository is online:

1. Open the repository on GitHub.
2. Click **Actions**.
3. Open **Refresh profile signal**.
4. Click **Run workflow**.
5. Refresh your public profile when the run completes.

The workflow detects the repository owner automatically and uses GitHub's built-in `GITHUB_TOKEN`. You do not need to add your username or create a personal token.

## 4. Add the social preview

Open **Settings → General → Social preview → Edit** and upload:

```text
assets/social-preview.png
```

## 5. Regenerate visual assets locally

```bash
python -m pip install -r requirements-dev.txt
python scripts/build_assets.py
python scripts/validate_profile.py
python scripts/build_preview.py
```

The portrait is built from `assets/source-portrait.jpg`. The actual photo stays visible and carries the likeness; the character field, scanline and edge signal are overlays.

## 6. Edit the writing

All biography and technical prose lives in `README.md`. The design uses one visual language only: near-black, terminal green, monospace assets and restrained motion.
