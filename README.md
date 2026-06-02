# FEEDBACK — Three Map

An interactive installation that lets a visitor explore a large image archive
through several 2D map projections (UMAP). The visitor interacts with a Nuxt
front-end, which drives a Three.js viewer in real time over a small socket
server.

This README is written so that **anyone can get the installation running on a
fresh Mac** (e.g. the Mac mini it is displayed on), even without development
experience. Follow it top to bottom.

---

## 1. What runs (the three pieces)

The installation is made of three programs that must all be running at the same
time:

| Piece | Folder | Tech | Address (port) | Role |
|-------|--------|------|----------------|------|
| **Server** | `server/` | Node + socket.io | `localhost:3001` | Relays messages between the interface and the viewer |
| **Viewer** | `project/` | Vite + Three.js | `localhost:5173` | Renders the image maps (the points / thumbnails) |
| **Interface** | `interface_nuxt/` | Nuxt 4 + Vue 3 | `localhost:3050` | **The screen the visitor sees and touches** |

The visitor only ever looks at the **Interface** (`localhost:3050`). It embeds
the Viewer inside itself and talks to it through the Server. All three must be
launched.

> The `interface/` folder is an older version of the interface and is **not
> used** — ignore it. The `process/` folder is a one-time Python data pipeline
> and is **not needed to run the installation** (see §6).

---

## 2. What to install on the Mac

You need two things: **Node.js** and a way to download the project files. That's
it — no Python, no database.

### a. Node.js (required)

The app was built and tested with **Node.js v24**. Any recent LTS (v20+) will
also work.

**Easiest way — download the installer:**

1. Go to <https://nodejs.org>
2. Download the **LTS** macOS installer (`.pkg`).
3. Open it and click through the installer.

**Or, if you use Homebrew** (the macOS package manager):

```bash
# Install Homebrew first if you don't have it (https://brew.sh):
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Then install Node:
brew install node
```

**Check it worked** — open the **Terminal** app and run:

```bash
node -v   # should print something like v24.x.x (or v20+)
npm -v    # should print a version number
```

If both print a version, you're ready.

### b. The project files

The project is the `FEEDBACK_THREE_MAP` folder (the one containing this README).
Make sure the whole folder is present on the Mac, including:

- `project/datas/images/` — the ~5,000 source images
- `process/cache/atlas.jpg` and `atlas.json` — the packed image atlas the
  viewer draws from

These two are **not** tracked by git (they are large), so if you cloned the
repo instead of copying the folder, you must copy them over manually. Without
them the maps will load but show no images.

---

## 3. First-time setup (install dependencies)

Open the **Terminal** app and install the dependencies for each of the three
pieces. Run these one block at a time (copy, paste, press Enter, wait for it to
finish before the next).

```bash
# Go to the project folder (adjust the path if it lives elsewhere)
cd ~/Dropbox/HEAD/DIPLOMA/FEEDBACK_THREE_MAP

# 1) Server
cd server && npm install && cd ..

# 2) Viewer
cd project && npm install && cd ..

# 3) Interface
cd interface_nuxt && npm install && cd ..
```

You only need to do this **once** (and again only if the code changes). Each
`npm install` downloads that piece's libraries into a local `node_modules`
folder and may take a minute or two.

---

## 4. Running the installation

All three pieces must run at the same time, each in its **own Terminal tab/window**.
Open a new tab with **⌘T** in Terminal.

**Tab 1 — Server**
```bash
cd ~/Dropbox/HEAD/DIPLOMA/FEEDBACK_THREE_MAP/server
npm start
```

**Tab 2 — Viewer**
```bash
cd ~/Dropbox/HEAD/DIPLOMA/FEEDBACK_THREE_MAP/project
npm run dev
```

**Tab 3 — Interface**
```bash
cd ~/Dropbox/HEAD/DIPLOMA/FEEDBACK_THREE_MAP/interface_nuxt
npm run dev
```

Leave all three tabs open and running. Then:

5. Open a web browser (Safari or Chrome) and go to:

   **<http://localhost:3050>**

That page is the installation. For a clean display, put the browser in
**fullscreen** (Safari/Chrome: **⌃⌘F**) and hide the cursor / dock.

> Start order doesn't strictly matter, but starting the **Server first** is
> tidiest, since the other two connect to it.

---

## 5. Making it auto-start (optional, for the exhibit Mac mini)

For an unattended installation you'll want everything to launch on boot. A
simple approach is one shell script that opens the three processes, set to run
at login. Minimal example (`start.sh` in the project root):

```bash
#!/bin/zsh
ROOT="$HOME/Dropbox/HEAD/DIPLOMA/FEEDBACK_THREE_MAP"

(cd "$ROOT/server"         && npm start)   &
(cd "$ROOT/project"        && npm run dev) &
(cd "$ROOT/interface_nuxt" && npm run dev) &

# Wait a few seconds for the servers to come up, then open the display fullscreen
sleep 8
open -a Safari http://localhost:3050
```

Make it executable once with `chmod +x start.sh`, then add it as a **Login
Item** (System Settings → General → Login Items) or wrap it in a `launchd`
agent. Also disable display sleep and screen saver in System Settings → Lock
Screen / Displays so the screen stays on.

---

## 6. The data pipeline (`process/`) — usually you can ignore this

`process/` is a **Python** pipeline that prepares the image data. You only need
it if you want to **rebuild** the maps from a new set of images. For normal
display you do **not** run it — the outputs it produces are already included:

- `process/cache/atlas.jpg` + `atlas.json` — the packed thumbnail atlas
- `project/static/data/*.json` — the UMAP coordinate files

If you ever do need to regenerate them, it requires Python 3 and the libraries
in `process/.venv`. See `process/build_atlas.py` (packs images into the atlas)
and `process/umap_book.py` (computes UMAP projections).

---

## 7. Troubleshooting

- **The page at `localhost:3050` is blank or won't load** — make sure all three
  Terminal tabs are still running and none printed an error. The Interface needs
  the Server (3001) and Viewer (5173) alive.
- **Maps load but show no images** — the atlas/images are missing. Confirm
  `process/cache/atlas.jpg`, `process/cache/atlas.json`, and
  `project/datas/images/` exist (see §2b).
- **"port already in use"** — a previous run is still going. Quit the old
  Terminal tabs (or run `pkill -f vite; pkill -f nuxt; pkill -f "node server.js"`)
  and start again.
- **`npm: command not found`** — Node.js isn't installed or the Terminal needs
  to be reopened after installing it. Re-check §2a.
- **Fonts look wrong on the first load** — give it a moment on a cold cache;
  the typography is preloaded and settles after the first full load.

---

## Folder reference

```
FEEDBACK_THREE_MAP/
├── server/          socket.io relay        → localhost:3001   (npm start)
├── project/         Three.js map viewer    → localhost:5173   (npm run dev)
│   ├── datas/images/   source images (not in git)
│   └── static/data/    UMAP projection JSONs
├── interface_nuxt/  Nuxt visitor interface → localhost:3050   (npm run dev)  ← the display
├── process/         Python atlas/UMAP pipeline (build-time only)
│   └── cache/          atlas.jpg + atlas.json (not in git)
└── interface/       legacy interface — unused
```
