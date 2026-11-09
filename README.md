# 🐍 Snake Game

Un jeu Snake en Python avec **pygame**, jouable directement dans le navigateur grâce à **PyScript**, et hébergé sur **GitHub Pages**.

👉 **Jouer en ligne :** [https://aya-bel03.github.io/Snake-game/]

> Le premier chargement peut prendre 10 à 30 secondes (téléchargement de Python et de pygame dans le navigateur). Clique ensuite sur le jeu et appuie sur **ESPACE**.

## ✨ Fonctionnalités

- Serpent qui traverse les murs (le bord droit ramène à gauche, etc.)
- Pommes à manger pour grandir (le jeu accélère à chaque pomme)
- Étoiles bonus qui apparaissent au hasard (+3 de longueur)
- Obstacles (pierres) à éviter
- Sons générés par le code (aucun fichier audio externe)
- Menu d'accueil animé et écran Game Over avec le score final
- Thème sombre aux couleurs vertes

## 🎮 Commandes

| Touche | Action |
|--------|--------|
| ESPACE | Commencer la partie |
| ⬅️ ⬆️ ➡️ ⬇️ | Diriger le serpent |
| R | Rejouer (après Game Over) |
| Q / Échap | Quitter |

## 🗂️ Structure du projet

```
├── index.html   # Page web : charge PyScript et le canvas du jeu
├── main.py      # Le code du jeu (pygame-ce, version async pour le navigateur)
└── README.md
```

## 🚀 Lancer le projet

### Dans le navigateur (GitHub Pages)

1. Mets `index.html` et `main.py` à la racine du dépôt.
2. Va dans **Settings → Pages → Deploy from a branch → main / root**.
3. Attends 1 à 2 minutes, puis ouvre le lien donné par GitHub.

### En local

Le code utilise `asyncio` pour fonctionner dans le navigateur. Pour l'essayer sur ton ordinateur, lance un petit serveur web dans le dossier du projet :

```bash
python -m http.server 8000
```

puis ouvre `http://localhost:8000` dans ton navigateur.

## 🛠️ Technologies

- [Python](https://www.python.org/)
- [pygame-ce](https://pyga.me/)
- [PyScript](https://pyscript.net/) (Pyodide)
- HTML / CSS
- [GitHub Pages](https://pages.github.com/)

## 📝 Notes techniques

- Les sons sont créés avec les modules `array` et `math` (sans `numpy`) pour un chargement plus léger. Si l'audio n'est pas disponible dans le navigateur, le jeu continue sans son.
- La boucle de jeu est asynchrone (`await asyncio.sleep(...)`) pour ne pas bloquer la page.

## 👩‍💻 Auteure

Projet réalisé par **Aya**, dans le cadre de son apprentissage de la programmation à travers des projets créatifs.
