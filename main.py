import math, random, pygame

# PS: caro recrutador técnico, precisei me ausentar no domingo a tarde e sabado a noite devido à um problema familiar, se pudesse relevar que não tive tempo de colocar as imagens para a animação do player ser a correta, ficaria grato! Obrigado

# Configurações globais
WIDTH, HEIGHT = 1024, 768
TAMANHO_CELULA = 48
GRADE_LARGURA, GRADE_ALTURA = WIDTH // TAMANHO_CELULA, HEIGHT // TAMANHO_CELULA

# Cores
PRETO, BRANCO, CINZA, VERMELHO, VERDE = (0, 0, 0), (255, 255, 255), (100, 100, 100), (255, 0, 0), (0, 255, 0)
CINZA_CLARO, COR_PAREDE, COR_CHAO, COR_SAIDA = (200, 200, 200), (50, 50, 50), (30, 30, 30), (0, 200, 0)

# Estados do Jogo
ESTADO_MENU, ESTADO_JOGO, ESTADO_FIM, ESTADO_GANHOU = 0, 1, 2, 3
estado_atual = ESTADO_MENU
MAPA, labirintos_feitos, MAX_LABIRINTOS = [], 0, 3

# Controle de movimento contínuo do jogador
player_dx, player_dy = 0, 0

def faz_labirinto(larg, alt):
    grade = [['W'] * larg for _ in range(alt)]
    sx, sy = random.randrange(1, larg - 1, 2), random.randrange(1, alt - 1, 2)
    visitado = [[False] * larg for _ in range(alt)]
    pilha = [(sx, sy)]
    visitado[sy][sx], grade[sy][sx] = True, 'F'
    direcoes = [(0, 2), (0, -2), (2, 0), (-2, 0)]
    while pilha:
        cx, cy = pilha[-1]
        vizinhos = [(cx + dx, cy + dy, dx, dy) for dx, dy in direcoes if 0 < cx + dx < larg - 1 and 0 < cy + dy < alt - 1 and not visitado[cy + dy][cx + dx]]
        if vizinhos:
            nx, ny, dx, dy = random.choice(vizinhos)
            grade[cy + dy // 2][cx + dx // 2], grade[ny][nx], visitado[ny][nx] = 'F', 'F', True
            pilha.append((nx, ny))
        else: pilha.pop()
    celulas_livres = [(x, y) for y in range(alt) for x in range(larg) if grade[y][x] == 'F']
    pos_p, pos_e = (random.choice(celulas_livres), random.choice([c for c in celulas_livres if c != random.choice(celulas_livres)])) if len(celulas_livres) >= 2 else ((1, 1), (larg - 2, alt - 2))
    grade[pos_p[1]][pos_p[0]], grade[pos_e[1]][pos_e[0]] = 'P', 'E'
    return ["".join(row) for row in grade]

class Botao:
    def __init__(self, x, y, larg, alt, texto, acao, cor=CINZA, cor_foco=CINZA_CLARO, cor_texto=BRANCO, tam_fonte=40):
        self.ret = pygame.Rect(x, y, larg, alt); self.texto, self.acao = texto, acao
        self.cor, self.cor_foco, self.cor_texto, self.tam_fonte, self.focado = cor, cor_foco, cor_texto, tam_fonte, False
    def desenha(self):
        screen.draw.filled_rect(self.ret, self.cor_foco if self.focado else self.cor)
        screen.draw.text(self.texto, center=self.ret.center, color=self.cor_texto, fontsize=self.tam_fonte)
    def verifica_foco(self, pos): self.focado = self.ret.collidepoint(pos)
    def foi_clicado(self, pos): return self.ret.collidepoint(pos)

larg_btn, alt_btn, espaco_btn = 300, 60, 20
y_inicio_botoes = (HEIGHT / 2) + 50
btn_comecar = Botao((WIDTH - larg_btn) / 2, y_inicio_botoes, larg_btn, alt_btn, "JOGAR", lambda: muda_estado(ESTADO_JOGO))
btn_sair = Botao((WIDTH - larg_btn) / 2, btn_comecar.ret.bottom + espaco_btn, larg_btn, alt_btn, "SAIR", exit)
botoes_menu = [btn_comecar, btn_sair]
jogador, inimigos = None, []

class Entidade:
    def __init__(self, gx, gy, img_nome, proporcao=0.7):
        self.x_grade, self.y_grade = gx, gy
        self.x, self.y = gx * TAMANHO_CELULA + TAMANHO_CELULA / 2, gy * TAMANHO_CELULA + TAMANHO_CELULA / 2
        self.x_alvo, self.y_alvo, self.movendo, self.velocidade = self.x, self.y, False, TAMANHO_CELULA * 3
        self.img = Actor(img_nome); self.img.center = (self.x, self.y)
        self.img.scale = (TAMANHO_CELULA * proporcao) / max(self.img.width, self.img.height)
        self.tempo_animacao, self.velocidade_animacao, self.estado_animacao, self.escala_animacao = 0.0, 0.5, 0, 0.05

    def atualiza_movimento(self, dt):
        if not self.movendo: return
        dx, dy = self.x_alvo - self.x, self.y_alvo - self.y
        dist = math.sqrt(dx**2 + dy**2)
        if dist > 0:
            mov_quant = self.velocidade * dt
            self.x, self.y, self.movendo = (self.x_alvo, self.y_alvo, False) if mov_quant >= dist else \
                                           (self.x + (dx / dist) * mov_quant, self.y + (dy / dist) * mov_quant, True)
            self.img.center = (self.x, self.y)
        else: self.movendo = False
    
    def atualiza_animacao(self, dt):
        self.tempo_animacao += dt
        if self.tempo_animacao >= self.velocidade_animacao:
            self.estado_animacao = 1 - self.estado_animacao
            self.tempo_animacao = 0.0
        if self.img: self.img.scale = (self.img.scale / (1 + (self.escala_animacao if self.estado_animacao == 1 else -self.escala_animacao))) * (1 + (self.escala_animacao if self.estado_animacao == 1 else -self.escala_animacao))
    def desenha(self): self.img.draw()

class Jogador(Entidade):
    def __init__(self, gx, gy): super().__init__(gx, gy, 'player'); self.velocidade_animacao = 0.2
    def move(self, dx, dy):
        if self.movendo: return False
        nx, ny = self.x_grade + dx, self.y_grade + dy
        if 0 <= nx < GRADE_LARGURA and 0 <= ny < GRADE_ALTURA and MAPA[ny][nx] != 'W':
            self.x_grade, self.y_grade = nx, ny
            self.x_alvo, self.y_alvo = nx * TAMANHO_CELULA + TAMANHO_CELULA / 2, ny * TAMANHO_CELULA + TAMANHO_CELULA / 2
            self.movendo, self.estado_animacao, self.tempo_animacao = True, 0, 0.0
            return True
        return False
    def atualiza(self, dt): self.atualiza_movimento(dt); self.atualiza_animacao(dt)

class Inimigo(Entidade):
    def __init__(self, gx, gy): super().__init__(gx, gy, 'enemy'); self.tempo_movimento, self.intervalo_movimento = 0.0, 1.2
    def move(self):
        if self.movendo or (jogador and jogador.movendo): return
        movimentos_possiveis = [(0,1), (0,-1), (1,0), (-1,0), (0,0)]; random.shuffle(movimentos_possiveis)
        for dx, dy in movimentos_possiveis:
            nx, ny = self.x_grade + dx, self.y_grade + dy
            if (0 <= nx < GRADE_LARGURA and 0 <= ny < GRADE_ALTURA and MAPA[ny][nx] != 'W' and (nx, ny) != (jogador.x_grade, jogador.y_grade if jogador else (-1,-1)) and MAPA[ny][nx] != 'E'):
                self.x_grade, self.y_grade = nx, ny
                self.x_alvo, self.y_alvo = nx * TAMANHO_CELULA + TAMANHO_CELULA / 2, ny * TAMANHO_CELULA + TAMANHO_CELULA / 2
                self.movendo, self.estado_animacao, self.tempo_animacao = True, 0, 0.0
                return True
        return False
    def atualiza(self, dt):
        self.atualiza_movimento(dt); self.atualiza_animacao(dt); self.tempo_movimento += dt
        if self.tempo_movimento >= self.intervalo_movimento: self.move(); self.tempo_movimento = 0.0

def muda_estado(novo_estado):
    global estado_atual, jogador, inimigos, MAPA, labirintos_feitos, player_dx, player_dy
    if novo_estado == ESTADO_JOGO and estado_atual != ESTADO_JOGO:
        if estado_atual == ESTADO_MENU: labirintos_feitos = 0
        MAPA = faz_labirinto(GRADE_LARGURA, GRADE_ALTURA)
        pos_inicial_p = next(((x, y) for y, linha in enumerate(MAPA) for x, c in enumerate(linha) if c == 'P'), (1, 1))
        jogador = Jogador(*pos_inicial_p); inimigos.clear()
        for _ in range(3):
            while True:
                ex, ey = random.randint(1, GRADE_LARGURA - 2), random.randint(1, GRADE_ALTURA - 2)
                if MAPA[ey][ex] == 'F' and (ex, ey) != pos_inicial_p and all((ex, ey) != (e.x_grade, e.y_grade) for e in inimigos): # Evitar inimigos na mesma célula inicial
                    inimigos.append(Inimigo(ex, ey)); break
        player_dx, player_dy = 0, 0
    elif novo_estado == ESTADO_GANHOU and estado_atual == ESTADO_JOGO:
        labirintos_feitos += 1; sounds.win_sound.play(); sounds.win_sound.set_volume(0.05)
        if labirintos_feitos < MAX_LABIRINTOS: muda_estado(ESTADO_JOGO); return
    estado_atual = novo_estado

def draw():
    screen.fill(PRETO)
    if estado_atual == ESTADO_MENU:
        screen.draw.text("Salve o Viking!", center=(WIDTH/2, HEIGHT/4), color=BRANCO, fontsize=70)
        screen.draw.text("Apenas uma vida, se mova nas setas!", center=(WIDTH/2, HEIGHT/4 + 54), color=BRANCO, fontsize=40)
        [btn.desenha() for btn in botoes_menu]
    elif estado_atual == ESTADO_JOGO:
        for y in range(GRADE_ALTURA):
            for x in range(GRADE_LARGURA):
                ret = pygame.Rect(x * TAMANHO_CELULA, y * TAMANHO_CELULA, TAMANHO_CELULA, TAMANHO_CELULA)
                tipo = MAPA[y][x]
                screen.draw.filled_rect(ret, COR_PAREDE if tipo == 'W' else (COR_SAIDA if tipo == 'E' else COR_CHAO))
        jogador.desenha(); [e.desenha() for e in inimigos]
    elif estado_atual == ESTADO_FIM: 
        screen.draw.text("FIM DE JOGO", center=(WIDTH/2, HEIGHT/2 - 30), color=VERMELHO, fontsize=70)
        screen.draw.text("VOLTAR AO MENU: ESC", center=(WIDTH/2, HEIGHT/2 + 40), color=BRANCO, fontsize=30)
    elif estado_atual == ESTADO_GANHOU: 
        screen.draw.text("VENCEU TODOS!", center=(WIDTH/2, HEIGHT/2 - 30), color=VERDE, fontsize=70)
        screen.draw.text("VOLTAR AO MENU: ESC", center=(WIDTH/2, HEIGHT/2 + 40), color=BRANCO, fontsize=30)

def update(dt):
    if estado_atual == ESTADO_JOGO:
        jogador.atualiza(dt); [e.atualiza(dt) for e in inimigos]
        if not jogador.movendo and (player_dx != 0 or player_dy != 0): jogador.move(player_dx, player_dy)
        if MAPA[jogador.y_grade][jogador.x_grade] == 'E': muda_estado(ESTADO_GANHOU)
        if any(jogador.x_grade == e.x_grade and jogador.y_grade == e.y_grade for e in inimigos): muda_estado(ESTADO_FIM)

def on_mouse_move(pos):
    if estado_atual == ESTADO_MENU: [btn.verifica_foco(pos) for btn in botoes_menu]

def on_mouse_down(pos):
    if estado_atual == ESTADO_MENU:
        for btn in botoes_menu:
            if btn.foi_clicado(pos): btn.acao(); break

def on_key_down(key):
    global estado_atual, player_dx, player_dy
    if estado_atual == ESTADO_MENU:
        if key == keys.RETURN: muda_estado(ESTADO_JOGO)
    elif estado_atual == ESTADO_JOGO:
        if key == keys.LEFT: player_dx, player_dy = -1, 0
        elif key == keys.RIGHT: player_dx, player_dy = 1, 0
        elif key == keys.UP: player_dx, player_dy = 0, -1
        elif key == keys.DOWN: player_dx, player_dy = 0, 1
    elif key == keys.F11: screen.set_mode((WIDTH, HEIGHT), pygame.FULLSCREEN if not screen.is_fullscreen else 0)
    elif estado_atual in [ESTADO_FIM, ESTADO_GANHOU] and key == keys.ESCAPE: muda_estado(ESTADO_MENU)

def on_key_up(key):
    global player_dx, player_dy
    if estado_atual == ESTADO_JOGO:
        if (key == keys.LEFT and player_dx == -1) or (key == keys.RIGHT and player_dx == 1) or \
           (key == keys.UP and player_dy == -1) or (key == keys.DOWN and player_dy == 1):
            player_dx, player_dy = 0, 0

muda_estado(ESTADO_MENU)