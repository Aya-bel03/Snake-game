import asyncio
import math
import random
from array import array

import pygame

# ── Lier le canvas HTML à pygame (nécessaire dans le navigateur) ─────
try:
    from pyscript import document
    import pyodide_js
    pyodide_js.canvas.setCanvas2D(document.getElementById("canvas"))
except Exception as e:
    print("Canvas non lié :", e)

# ── Initialisation ───────────────────────────────────────────────────
SAMPLE_RATE = 22050
SON_OK = True
try:
    pygame.mixer.pre_init(SAMPLE_RATE, -16, 1, 512)
    pygame.init()
    pygame.mixer.init(SAMPLE_RATE, -16, 1, 512)
except Exception as e:
    print("Son indisponible :", e)
    SON_OK = False
    pygame.init()

# Dimensions
largeur = 600
hauteur = 400
fenetre = pygame.display.set_mode((largeur, hauteur))
pygame.display.set_caption("Snake Game")

# ── Palette de couleurs ──────────────────────────────────────────────
FOND        = (15, 20, 10)
GRILLE      = (22, 32, 16)
BORDURE     = (80, 200, 80)
SERPENT_T   = (50, 220, 80)
SERPENT_C   = (30, 160, 55)
OBSTACLE    = (120, 70, 20)
OBSTACLE_L  = (160, 100, 40)
SCORE_C     = (200, 255, 180)
BLANC       = (255, 255, 255)
ROUGE_VIF   = (255, 60, 60)
JAUNE_BONUS = (255, 220, 0)
JAUNE_GLOW  = (255, 255, 100)
POMME_ROUGE  = (220, 40, 40)
POMME_FONCE  = (160, 20, 20)
POMME_REFLET = (255, 120, 120)
POMME_TIGE   = (80, 50, 10)
POMME_FEUIL  = (50, 180, 50)

# ── Paramètres ───────────────────────────────────────────────────────
taille_bloc      = 20
VITESSE_INITIALE = 6
nombre_obstacles = 5

# ── Polices (police par défaut de pygame : marche dans le navigateur) ─
police_titre  = pygame.font.Font(None, 52)
police_normal = pygame.font.Font(None, 34)
police_score  = pygame.font.Font(None, 30)

# ════════════════════════════════════════════════════════════════════
#  GÉNÉRATION DES SONS (sans numpy, sans fichiers externes)
# ════════════════════════════════════════════════════════════════════

class SonVide:
    """Faux son utilisé si l'audio ne marche pas (le jeu continue sans son)."""
    def play(self): pass
    def set_volume(self, v): pass

def make_sound(samples):
    try:
        buf = array("h", [int(max(-1.0, min(1.0, s)) * 32767) for s in samples])
        return pygame.mixer.Sound(buffer=buf.tobytes())
    except Exception as e:
        print("Son non créé :", e)
        return SonVide()

def sine(freq, dur, vol=0.5):
    n = int(SAMPLE_RATE * dur)
    return [
        vol * math.sin(2 * math.pi * freq * i / SAMPLE_RATE) * (1 - i / n) ** 1.5
        for i in range(n)
    ]

def noise(dur, vol=0.3):
    n = int(SAMPLE_RATE * dur)
    return [vol * (random.random() * 2 - 1) * (1 - i / n) ** 1.5 for i in range(n)]

def concat(*waves):
    out = []
    for w in waves:
        out.extend(w)
    return out

def overlay(*waves):
    length = max(len(w) for w in waves)
    out = [0.0] * length
    for w in waves:
        for i, v in enumerate(w):
            out[i] += v
    return out

def build_son_pomme():
    return make_sound(concat(
        sine(523, 0.05, 0.4),
        sine(659, 0.05, 0.4),
        sine(784, 0.10, 0.5),
    ))

def build_son_bonus():
    return make_sound(concat(
        sine(523, 0.07, 0.4),
        sine(659, 0.07, 0.4),
        sine(784, 0.07, 0.4),
        sine(1047, 0.15, 0.5),
    ))

def build_son_gameover():
    return make_sound(concat(
        sine(300, 0.15, 0.5),
        sine(250, 0.15, 0.5),
        sine(200, 0.15, 0.5),
        sine(150, 0.30, 0.5),
        overlay(sine(120, 0.25, 0.3), noise(0.25, 0.15)),
    ))

if SON_OK:
    son_pomme    = build_son_pomme()
    son_bonus    = build_son_bonus()
    son_gameover = build_son_gameover()
else:
    son_pomme = son_bonus = son_gameover = SonVide()

son_pomme.set_volume(0.7)
son_bonus.set_volume(0.8)
son_gameover.set_volume(0.8)

# ════════════════════════════════════════════════════════════════════
#  FONCTIONS D'AFFICHAGE
# ════════════════════════════════════════════════════════════════════

def draw_text_center(surface, texte, police, couleur, cy, shadow=True):
    if shadow:
        ombre = police.render(texte, True, (0, 0, 0))
        r = ombre.get_rect(center=(largeur // 2 + 2, cy + 2))
        surface.blit(ombre, r)
    msg = police.render(texte, True, couleur)
    rect = msg.get_rect(center=(largeur // 2, cy))
    surface.blit(msg, rect)

def afficher_score(score, bonus_actif):
    texte = police_score.render(f"Score : {score}", True, SCORE_C)
    fenetre.blit(texte, [12, 10])
    if bonus_actif:
        b = police_score.render("BONUS !", True, JAUNE_BONUS)
        fenetre.blit(b, [largeur - b.get_width() - 12, 10])

def dessiner_grille():
    for x in range(0, largeur, taille_bloc):
        pygame.draw.line(fenetre, GRILLE, (x, 0), (x, hauteur))
    for y in range(0, hauteur, taille_bloc):
        pygame.draw.line(fenetre, GRILLE, (0, y), (largeur, y))

def dessiner_pomme(surface, pos):
    cx = pos[0] + taille_bloc // 2
    cy = pos[1] + taille_bloc // 2
    r  = taille_bloc // 2 - 1
    pygame.draw.circle(surface, POMME_FONCE,  (cx, cy), r)
    pygame.draw.circle(surface, POMME_ROUGE,  (cx, cy), r - 1)
    pygame.draw.circle(surface, POMME_REFLET, (cx - 3, cy - 3), r // 3)
    pygame.draw.line(surface, POMME_TIGE, (cx, cy - r), (cx + 2, cy - r - 4), 2)
    pygame.draw.ellipse(surface, POMME_FEUIL, [cx + 1, cy - r - 5, 7, 4])

def dessiner_bonus(surface, pos, tick):
    cx = pos[0] + taille_bloc // 2
    cy = pos[1] + taille_bloc // 2
    r_ext = taille_bloc // 2
    r_int = r_ext // 2
    n = 5
    pts = []
    pulse = 1 + 0.15 * math.sin(tick * 0.15)
    for i in range(n * 2):
        angle = math.pi / n * i - math.pi / 2
        r = r_ext * pulse if i % 2 == 0 else r_int
        pts.append((cx + r * math.cos(angle), cy + r * math.sin(angle)))
    pygame.draw.polygon(surface, JAUNE_GLOW, pts)
    pygame.draw.polygon(surface, JAUNE_BONUS, pts, 2)

def dessiner_obstacle(surface, pos):
    x, y = pos[0], pos[1]
    t = taille_bloc
    pygame.draw.rect(surface, OBSTACLE,   [x, y, t, t], border_radius=4)
    pygame.draw.rect(surface, OBSTACLE_L, [x + 1, y + 1, t // 2, t // 3], border_radius=2)
    pygame.draw.rect(surface, (60, 35, 5), [x, y, t, t], 1, border_radius=4)

def dessiner_serpent(surface, serpent):
    for i, seg in enumerate(serpent):
        couleur = SERPENT_T if i == len(serpent) - 1 else SERPENT_C
        pygame.draw.rect(surface, couleur,
                         [seg[0] + 1, seg[1] + 1, taille_bloc - 2, taille_bloc - 2],
                         border_radius=5)
        if i == len(serpent) - 1:
            pygame.draw.circle(surface, BLANC,   (seg[0] + 5,  seg[1] + 5), 3)
            pygame.draw.circle(surface, BLANC,   (seg[0] + 15, seg[1] + 5), 3)
            pygame.draw.circle(surface, (0, 0, 0), (seg[0] + 5,  seg[1] + 5), 1)
            pygame.draw.circle(surface, (0, 0, 0), (seg[0] + 15, seg[1] + 5), 1)

# ── Génération ────────────────────────────────────────────────────────
def case_aleatoire():
    return [
        random.randrange(0, largeur // taille_bloc) * taille_bloc,
        random.randrange(0, hauteur // taille_bloc) * taille_bloc,
    ]

def generer_obstacles(serpent, nourriture):
    obst = []
    while len(obst) < nombre_obstacles:
        c = case_aleatoire()
        if c not in obst and c != nourriture and c not in serpent:
            obst.append(c)
    return obst

def generer_bonus(serpent, obstacles):
    while True:
        c = case_aleatoire()
        if c not in serpent and c not in obstacles:
            return c

def nouvelle_nourriture(serpent, obstacles):
    while True:
        c = case_aleatoire()
        if c not in serpent and c not in obstacles:
            return c

# ════════════════════════════════════════════════════════════════════
#  MENU  (retourne True pour jouer, False pour quitter)
# ════════════════════════════════════════════════════════════════════
async def menu_principal():
    tick = 0
    while True:
        fenetre.fill(FOND)
        dessiner_grille()

        r_col = int(100 + 80 * math.sin(tick * 0.05))
        g_col = int(220 + 30 * math.sin(tick * 0.05 + 1))
        couleur_titre = (r_col, g_col, 80)

        draw_text_center(fenetre, "Welcome to Snake Game!", police_titre, couleur_titre, 155)
        draw_text_center(fenetre, "Appuie sur ESPACE pour commencer", police_normal, BLANC, 235)
        draw_text_center(fenetre, "Mange les pommes ! Evite les pierres !", police_normal, BLANC, 285)

        epaisseur = 3 + int(1.5 * abs(math.sin(tick * 0.05)))
        pygame.draw.rect(fenetre, BORDURE, [0, 0, largeur, hauteur], epaisseur)

        pygame.display.update()
        tick += 1

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    return True
                elif event.key in (pygame.K_q, pygame.K_ESCAPE):
                    return False

        await asyncio.sleep(1 / 30)   # indispensable dans le navigateur

# ════════════════════════════════════════════════════════════════════
#  BOUCLE DE JEU  (retourne True pour rejouer, False pour quitter)
# ════════════════════════════════════════════════════════════════════
async def boucle_jeu():
    game_close = False
    gameover_joue = False

    x = largeur // 2
    y = hauteur // 2
    x_change = taille_bloc
    y_change = 0

    serpent = []
    longueur_serpent = 1

    nourriture = nouvelle_nourriture([], [])
    obstacles  = generer_obstacles([], nourriture)
    bonus      = None

    vitesse = VITESSE_INITIALE
    tick    = 0

    while True:

        # ── Écran Game Over ──────────────────────────────────────────
        while game_close:
            if not gameover_joue:
                son_gameover.play()
                gameover_joue = True

            fenetre.fill(FOND)
            dessiner_grille()
            pygame.draw.rect(fenetre, ROUGE_VIF, [0, 0, largeur, hauteur], 4)
            draw_text_center(fenetre, "GAME OVER !", police_titre, ROUGE_VIF, 150)
            draw_text_center(fenetre, f"Score final : {longueur_serpent - 1}", police_normal, SCORE_C, 195)
            draw_text_center(fenetre, "R = Rejouer   |   Q = Quitter", police_normal, BLANC, 250)
            pygame.display.update()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return False
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_q:
                        return False
                    elif event.key == pygame.K_r:
                        return True

            await asyncio.sleep(1 / 30)

        # ── Événements ──────────────────────────────────────────────
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_LEFT and x_change != taille_bloc:
                    x_change = -taille_bloc; y_change = 0
                elif event.key == pygame.K_RIGHT and x_change != -taille_bloc:
                    x_change = taille_bloc; y_change = 0
                elif event.key == pygame.K_UP and y_change != taille_bloc:
                    y_change = -taille_bloc; x_change = 0
                elif event.key == pygame.K_DOWN and y_change != -taille_bloc:
                    y_change = taille_bloc; x_change = 0

        x += x_change
        y += y_change

        # Traverser les murs
        if x >= largeur:  x = 0
        if x < 0:         x = largeur - taille_bloc
        if y >= hauteur:  y = 0
        if y < 0:         y = hauteur - taille_bloc
        tete = [x, y]

        # ── Dessin ──────────────────────────────────────────────────
        fenetre.fill(FOND)
        dessiner_grille()
        dessiner_pomme(fenetre, nourriture)
        for obs in obstacles:
            dessiner_obstacle(fenetre, obs)
        if bonus:
            dessiner_bonus(fenetre, bonus, tick)

        serpent.append(tete)
        if len(serpent) > longueur_serpent:
            del serpent[0]

        # Collisions
        for seg in serpent[:-1]:
            if seg == tete:
                game_close = True
        for obs in obstacles:
            if tete == obs:
                game_close = True

        dessiner_serpent(fenetre, serpent)
        afficher_score(longueur_serpent - 1, bonus is not None)
        pygame.draw.rect(fenetre, BORDURE, [0, 0, largeur, hauteur], 3)
        pygame.display.update()

        # ── Manger pomme ────────────────────────────────────────────
        if tete == nourriture:
            son_pomme.play()
            longueur_serpent += 1
            vitesse = min(vitesse + 1, 25)
            nourriture = nouvelle_nourriture(serpent, obstacles)
            if bonus is None and random.randint(1, 5) == 1:
                bonus = generer_bonus(serpent, obstacles)

        # ── Manger bonus ────────────────────────────────────────────
        if bonus and tete == bonus:
            son_bonus.play()
            longueur_serpent += 3
            bonus = None

        tick += 1
        await asyncio.sleep(1 / vitesse)   # remplace clock.tick(vitesse)

# ════════════════════════════════════════════════════════════════════
#  PROGRAMME PRINCIPAL
# ════════════════════════════════════════════════════════════════════
def envoyer_touche(key):
    """Simule l'appui sur une touche du clavier."""
    pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=key))

def installer_tactile():
    """Swipe + tap sur le canvas, et boutons fléchés à l'écran (téléphone)."""
    try:
        from pyscript import document
        from pyodide.ffi import create_proxy
    except Exception as e:
        print("Tactile indisponible :", e)
        return

    canvas = document.getElementById("canvas")
    etat = {"x": 0, "y": 0, "fait": False}
    SEUIL = 20  # distance minimale (pixels) pour compter comme un swipe

    def touch_start(e):
        e.preventDefault()
        t = e.changedTouches.item(0)
        etat["x"], etat["y"], etat["fait"] = t.clientX, t.clientY, False

    def touch_move(e):
        e.preventDefault()
        if etat["fait"]:
            return
        t = e.changedTouches.item(0)
        dx = t.clientX - etat["x"]
        dy = t.clientY - etat["y"]
        if max(abs(dx), abs(dy)) < SEUIL:
            return
        etat["fait"] = True
        if abs(dx) > abs(dy):
            envoyer_touche(pygame.K_RIGHT if dx > 0 else pygame.K_LEFT)
        else:
            envoyer_touche(pygame.K_DOWN if dy > 0 else pygame.K_UP)

    def touch_end(e):
        e.preventDefault()
        if not etat["fait"]:
            # simple tap : commencer (ESPACE) ou rejouer (R)
            envoyer_touche(pygame.K_SPACE)
            envoyer_touche(pygame.K_r)

    canvas.addEventListener("touchstart", create_proxy(touch_start))
    canvas.addEventListener("touchmove", create_proxy(touch_move))
    canvas.addEventListener("touchend", create_proxy(touch_end))

    def lier_bouton(id_bouton, actions):
        bouton = document.getElementById(id_bouton)
        if bouton is None:
            return
        def appui(e):
            e.preventDefault()
            for k in actions:
                envoyer_touche(k)
        bouton.addEventListener("pointerdown", create_proxy(appui))

    lier_bouton("btn-up",    [pygame.K_UP])
    lier_bouton("btn-down",  [pygame.K_DOWN])
    lier_bouton("btn-left",  [pygame.K_LEFT])
    lier_bouton("btn-right", [pygame.K_RIGHT])
    lier_bouton("btn-ok",    [pygame.K_SPACE, pygame.K_r])

async def main():
    installer_tactile()
    if not await menu_principal():
        return
    while await boucle_jeu():
        pass
    fenetre.fill(FOND)
    draw_text_center(fenetre, "Merci d'avoir joué !", police_titre, SCORE_C, hauteur // 2)
    pygame.display.update()

await main()
