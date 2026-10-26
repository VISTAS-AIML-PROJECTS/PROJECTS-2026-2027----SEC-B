# How to push this folder to GitHub

Push ONLY this folder (stratosphere-ui). Never push your original full project folder:
Git keeps history forever, so anything committed once can be recovered.

## 1. One-time setup
1. Install Git: https://git-scm.com/downloads
2. Tell Git who you are:
   git config --global user.name "Your Name"
   git config --global user.email "your-github-email@example.com"

## 2. Create the empty repository on GitHub
1. Sign in to GitHub (use your college organization if you were asked to).
2. Click New repository. Name it e.g. stratosphere-ui-showcase.
3. Choose Public or Private as your college requires.
4. Do NOT tick "Add a README", .gitignore or license (they already exist here).
5. Click Create repository and copy the URL, e.g. https://github.com/<user-or-org>/stratosphere-ui-showcase.git

## 3. Push
Open a terminal inside the stratosphere-ui folder:
   git init -b main
   git add .
   git status                 # check the list: no .env, .pkl, data or credentials
   git commit -m "Add Stratosphere UI showcase"
   git remote add origin https://github.com/<user-or-org>/stratosphere-ui-showcase.git
   git push -u origin main

## 4. Sign-in when Git asks
GitHub no longer accepts your account password. Use one of:
- GitHub CLI (easiest): install https://cli.github.com then run `gh auth login`
- Personal Access Token: GitHub > Settings > Developer settings > Personal access tokens,
  create one with the "repo" scope, and paste it when Git asks for a password.
- SSH key: https://docs.github.com/authentication/connecting-to-github-with-ssh

## 5. Check the result
Open the repository page: the README, screenshots and the files should be visible.
Run `git ls-files` to list everything that was uploaded.

## 6. Later updates
   git add .
   git commit -m "Describe the change"
   git push

## If something goes wrong
- "remote origin already exists": git remote set-url origin <URL>
- "failed to push, fetch first": git pull --rebase origin main, then push again
- Pushed a secret by mistake: rotate/regenerate that key immediately; deleting the file later does not remove it from history.
