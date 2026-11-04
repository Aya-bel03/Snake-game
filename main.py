import pygame
import random
import math
import numpy as np

# ── Initialisation ───────────────────────────────────────────────────
pygame.mixer.pre_init(44100, -16, 1, 512)
pygame.init()
pygame.mixer.init(44100, -16, 1, 512)

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
SAMPLE_RATE      = 44100

# ── Polices ──────────────────────────────────────────────────────────
police_titre  = pygame.font.SysFont("arial", 36, bold=True)
police_normal = pygame.font.SysFont("arial", 24)
police_score  = pygame.font.SysFont("arial", 22, bold=True)
police_emoji  = pygame.font.SysFont("segoe ui emoji", 30)

# ════════════════════════════════════════════════════════════════════
#  GÉNÉRATION DES SONS (sans fichiers externes)
# ════════════════════════════════════════════════════════════════════

def make_sound(wave: np.ndarray) -> pygame.mixer.Sound:
    """Convertit un array numpy [-1,1] en Sound pygame."""
    samples = np.clip(wave, -1, 1)
    buf = (samples * 32767).astype(np.int16)
    return pygame.mixer.Sound(buffer=buf.tobytes())

def sine(freq, dur, vol=0.5, fade_out=True):
    t = np.linspace(0, dur, int(SAMPLE_RATE * dur), endpoint=False)
    w = vol * np.sin(2 * np.pi * freq * t)
    if fade_out:
        env = np.linspace(1, 0, len(w)) ** 1.5
        w *= env
    return w

def square(freq, dur, vol=0.3, duty=0.5):
    t = np.linspace(0, dur, int(SAMPLE_RATE * dur), endpoint=False)
    w = vol * np.sign(np.sin(2 * np.pi * freq * t))
    env = np.linspace(1, 0, len(w)) ** 2
    return w * env

def noise(dur, vol=0.3):
    n = int(SAMPLE_RATE * dur)
    w = vol * (np.random.random(n) * 2 - 1)
    env = np.linspace(1, 0, n) ** 1.5
    return w * env

def concat(*waves):
    return np.concatenate(waves)

def overlay(*waves):
    length = max(len(w) for w in waves)
    out = np.zeros(length)
    for w in waves:
        out[:len(w)] += w
    return out

# 🍎 Son pomme : "bip" aigu montant
def build_son_pomme():
    w = concat(
        sine(523, 0.05, 0.4),   # Do5
        sine(659, 0.05, 0.4),   # Mi5
        sine(784, 0.10, 0.5),   # Sol5
    )
    return make_sound(w)

# ⭐ Son bonus : fanfare festive
def build_son_bonus():
    w = concat(
        sine(523, 0.07, 0.4),
        sine(659, 0.07, 0.4),
        sine(784, 0.07, 0.4),
        sine(1047,0.15, 0.5),
    )
    return make_sound(w)

# 💀 Son game over : descente grave
def build_son_gameover():
    w = concat(
        sine(300, 0.15, 0.5),
        sine(250, 0.15, 0.5),
        sine(200, 0.15, 0.5),
        sine(150, 0.30, 0.5),
        overlay(
            sine(120, 0.25, 0.3),
            noise(0.25, 0.15)
        )
    )
    return make_sound(w)



# ── Charger les sons ─────────────────────────────────────────────────
son_pomme    = build_son_pomme()
son_bonus    = build_son_bonus()
son_gameover = build_son_gameover()


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

def draw_emoji_center(surface, texte, cy):
    try:
        msg = police_emoji.render(texte, True, BLANC)
        rect = msg.get_rect(center=(largeur // 2, cy))
        surface.blit(msg, rect)
    except:
        pass

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
    pygame.draw.circle(surface, POMME_FONCE,  (cx, cy),     r)
    pygame.draw.circle(surface, POMME_ROUGE,  (cx, cy),     r - 1)
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
    pygame.draw.rect(surface, OBSTACLE_L, [x+1, y+1, t//2, t//3], border_radius=2)
    pygame.draw.rect(surface, (60, 35, 5), [x, y, t, t], 1, border_radius=4)

def dessiner_serpent(surface, serpent):
    for i, seg in enumerate(serpent):
        couleur = SERPENT_T if i == len(serpent) - 1 else SERPENT_C
        pygame.draw.rect(surface, couleur,
                         [seg[0]+1, seg[1]+1, taille_bloc-2, taille_bloc-2],
                         border_radius=5)
        if i == len(serpent) - 1:
            pygame.draw.circle(surface, BLANC,  (seg[0]+5,  seg[1]+5), 3)
            pygame.draw.circle(surface, BLANC,  (seg[0]+15, seg[1]+5), 3)
            pygame.draw.circle(surface, (0,0,0),(seg[0]+5,  seg[1]+5), 1)
            pygame.draw.circle(surface, (0,0,0),(seg[0]+15, seg[1]+5), 1)

# ── Génération ────────────────────────────────────────────────────────
def generer_obstacles(serpent, nourriture):
    obst = []
    while len(obst) < nombre_obstacles:
        ox = round(random.randrange(0, largeur - taille_bloc) / taille_bloc) * taille_bloc
        oy = round(random.randrange(0, hauteur - taille_bloc) / taille_bloc) * taille_bloc
        if [ox, oy] not in obst and [ox, oy] != nourriture and [ox, oy] not in serpent:
            obst.append([ox, oy])
    return obst

def generer_bonus(serpent, obstacles):
    while True:
        bx = round(random.randrange(0, largeur - taille_bloc) / taille_bloc) * taille_bloc
        by = round(random.randrange(0, hauteur - taille_bloc) / taille_bloc) * taille_bloc
        if [bx, by] not in serpent and [bx, by] not in obstacles:
            return [bx, by]

def nouvelle_nourriture(serpent, obstacles):
    while True:
        nx = round(random.randrange(0, largeur - taille_bloc) / taille_bloc) * taille_bloc
        ny = round(random.randrange(0, hauteur - taille_bloc) / taille_bloc) * taille_bloc
        if [nx, ny] not in serpent and [nx, ny] not in obstacles:
            return [nx, ny]

# ════════════════════════════════════════════════════════════════════
#  MENU
# ════════════════════════════════════════════════════════════════════
def menu_principal():
    tick = 0
    en_attente = True
    while en_attente:
        fenetre.fill(FOND)
        dessiner_grille()

        r_col = int(100 + 80 * math.sin(tick * 0.05))
        g_col = int(220 + 30 * math.sin(tick * 0.05 + 1))
        couleur_titre = (r_col, g_col, 80)

        draw_text_center(fenetre, "Welcome to Snake Game!", police_titre, couleur_titre, 155)
        draw_emoji_center(fenetre, "  Appuie sur ESPACE pour commencer", 235)
        draw_emoji_center(fenetre, "Mange les pommes!  Evite les pierres!", 285)

        epaisseur = 3 + int(1.5 * abs(math.sin(tick * 0.05)))
        pygame.draw.rect(fenetre, BORDURE, [0, 0, largeur, hauteur], epaisseur)

        pygame.display.update()
        tick += 1
        pygame.time.Clock().tick(30)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); quit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    en_attente = False
                elif event.key in (pygame.K_q, pygame.K_ESCAPE):
                    pygame.quit(); quit()

# ════════════════════════════════════════════════════════════════════
#  BOUCLE DE JEU
# ════════════════════════════════════════════════════════════════════
def boucle_jeu():
    game_over  = False
    game_close = False
    gameover_joue = False   # évite de rejouer le son en boucle

    x = largeur / 2
    y = hauteur / 2

    x_change = taille_bloc
    y_change = 0

    serpent          = []
    longueur_serpent = 1

    nourriture = nouvelle_nourriture([], [])
    obstacles  = generer_obstacles([], nourriture)
    bonus      = None

    clock   = pygame.time.Clock()
    vitesse = VITESSE_INITIALE
    tick    = 0



    while not game_over:

        # ── Écran Game Over ──────────────────────────────────────────
        while game_close:
            if not gameover_joue:

                son_gameover.play()
                gameover_joue = True

            fenetre.fill(FOND)
            dessiner_grille()
            pygame.draw.rect(fenetre, ROUGE_VIF, [0, 0, largeur, hauteur], 4)
            draw_text_center(fenetre, "GAME OVER !",                        police_titre,  ROUGE_VIF, 150)
            draw_text_center(fenetre, f"Score final : {longueur_serpent - 1}" , police_normal, SCORE_C,  195)
            draw_emoji_center(fenetre, "R = Rejouer   |   Q = Quitter",   250)
            pygame.display.update()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit(); quit()
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_q:
                        game_over  = True
                        game_close = False
                    elif event.key == pygame.K_r:
                        boucle_jeu(); return

        # ── Événements ──────────────────────────────────────────────
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                game_over = True
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_LEFT  and x_change != taille_bloc:
                    x_change = -taille_bloc; y_change = 0
                elif event.key == pygame.K_RIGHT and x_change != -taille_bloc:
                    x_change =  taille_bloc; y_change = 0
                elif event.key == pygame.K_UP   and y_change != taille_bloc:
                    y_change = -taille_bloc; x_change = 0
                elif event.key == pygame.K_DOWN  and y_change != -taille_bloc:
                    y_change =  taille_bloc; x_change = 0

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

        # ── Manger pomme 🍎 ─────────────────────────────────────────
        if tete == nourriture:
            son_pomme.play()
            longueur_serpent += 1
            vitesse    = min(vitesse + 1, 25)
            nourriture = nouvelle_nourriture(serpent, obstacles)
            if bonus is None and random.randint(1, 5) == 1:
                bonus = generer_bonus(serpent, obstacles)

        # ── Manger bonus ⭐ ─────────────────────────────────────────
        if bonus and tete == bonus:
            son_bonus.play()
            longueur_serpent += 3
            bonus = None

        tick += 1
        clock.tick(vitesse)

    pygame.quit(); quit()

# ▶ Lancer
menu_principal()
boucle_jeu()