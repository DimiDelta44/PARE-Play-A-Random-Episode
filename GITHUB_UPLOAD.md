# How to Upload PARE to GitHub

## Prerequisites
- GitHub account
- Git installed on your system

## Step-by-Step Instructions

### 1. Create a New Repository on GitHub
1. Go to https://github.com/new
2. Repository name: `PARE` (or `pare-random-episode-player`)
3. Description: "Universal TV series random episode player with TVDB integration"
4. Set to **Public**
5. **DO NOT** initialize with README (we already have one)
6. Click "Create repository"

### 2. Initialize Git in Your Local Folder
Open PowerShell in the PARE directory and run:

```powershell
cd "d:\Misc Files\Python Coding\PARE"
git init
```

### 3. Add Files to Git
```powershell
git add .
```

This will add all files except those in `.gitignore` (which excludes build artifacts, `__pycache__`, etc.)

### 4. Create Initial Commit
```powershell
git commit -m "Initial commit: PARE - Play A Random Episode"
```

### 5. Link to GitHub Repository
Replace `YOUR_USERNAME` with your GitHub username:

```powershell
git remote add origin https://github.com/YOUR_USERNAME/PARE.git
```

### 6. Push to GitHub
```powershell
git branch -M main
git push -u origin main
```

### 7. (Optional) Create a Release with the Executable

1. Go to your repository on GitHub
2. Click "Releases" → "Create a new release"
3. Tag version: `v1.0.0`
4. Release title: `PARE v1.0.0 - Initial Release`
5. Description: Brief description of features
6. **Attach the executable**: Upload `dist/PARE.exe` as a binary
7. Click "Publish release"

## What Gets Uploaded

✅ **Included:**
- `pare.py` - Main application
- `README.md` - Documentation
- `LICENSE` - MIT License
- `.gitignore` - Git ignore rules
- `PARE.spec` - PyInstaller build configuration
- `build_exe.py` - Build helper script
- `assets/` - Logo and icon files

❌ **Excluded (via .gitignore):**
- `config.json` - User settings (personal)
- `build/` - Build artifacts
- `dist/` - Compiled executable (upload separately as release)
- `__pycache__/` - Python cache
- `*.pyc` - Compiled Python files

## Updating the Repository Later

```powershell
git add .
git commit -m "Description of changes"
git push
```

## Troubleshooting

**If you get authentication errors:**
- GitHub now requires Personal Access Tokens instead of passwords
- Go to GitHub Settings → Developer settings → Personal access tokens
- Generate a new token with `repo` scope
- Use the token as your password when prompted

**Alternative: Use GitHub Desktop**
1. Download GitHub Desktop from https://desktop.github.com/
2. File → Add Local Repository → Select PARE folder
3. Publish repository to GitHub
