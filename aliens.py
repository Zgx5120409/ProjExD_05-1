#!/usr/bin/env python
""" pygame.examples.aliens

Shows a mini game where you have to defend against aliens.

What does it show you about pygame?

* pg.sprite, the difference between Sprite and Group.
* dirty rectangle optimization for processing for speed.
* music with pg.mixer.music, including fadeout
* sound effects with pg.Sound
* event processing, keyboard handling, QUIT handling.
* a main loop frame limited with a game clock from pg.time.Clock
* fullscreen switching.


Controls
--------

* Left and right arrows to move.
* Space bar to shoot
* f key to toggle between fullscreen.

"""

import random
import os
import pygame.font
# import basic pygame modules
import pygame as pg

# see if we can load more than standard BMP
if not pg.image.get_extended():
    raise SystemExit("Sorry, extended image module required")


# game constants
MAX_SHOTS = 4  # most player bullets onscreen
ENEMY_ODDS = 22  # chances a new alien appears
BOMB_ODDS = 60  # chances a new bomb will drop
ENEMY_RELOAD = 12  # frames between new aliens
SCREENRECT = pg.Rect(0, 0, 640, 480)
SCORE = 0
Pachi = False
SUPERMODE = False #mode切り替え用変数（ON：True）

main_dir = os.path.split(os.path.abspath(__file__))[0]


def load_image(file):
    """loads an image, prepares it for play"""
    file = os.path.join(main_dir, "data", file)
    try:
        surface = pg.image.load(file)
    except pg.error:
        raise SystemExit('Could not load image "%s" %s' % (file, pg.get_error()))
    return surface.convert()


def load_sound(file):
    """because pygame can be be compiled without mixer."""
    if not pg.mixer:
        return None
    file = os.path.join(main_dir, "data", file)
    try:
        sound = pg.mixer.Sound(file)
        return sound
    except pg.error:
        print("Warning, unable to load, %s" % file)
    return None


# Each type of game object gets an init and an update function.
# The update function is called once per frame, and it is when each object should
# change its current position and state.
#
# The Player object actually gets a "move" function instead of update,
# since it is passed extra information about the keyboard.


class Player(pg.sprite.Sprite):
    """Representing the player as a moon buggy type car."""

    speed = 10
    bounce = 24
    gun_offset = -11
    images = []

    def __init__(self):
        pg.sprite.Sprite.__init__(self, self.containers)
        self.image = self.images[0]
        self.rect = self.image.get_rect(midbottom=SCREENRECT.midbottom)
        self.reloading = 0
        self.origtop = self.rect.top
        self.facing = -1

    def move(self, direction):
        if direction:
            self.facing = direction
        self.rect.move_ip(direction * self.speed, 0)
        self.rect = self.rect.clamp(SCREENRECT)
        if direction < 0:
            self.image = self.images[0]
        elif direction > 0:
            self.image = self.images[1]
        self.rect.top = self.origtop - (self.rect.left // self.bounce % 2)

    def gunpos(self):
        pos = self.facing * self.gun_offset + self.rect.centerx
        return pos, self.rect.top


class Enemy(pg.sprite.Sprite):
    

    speed = 3
    animcycle = 12
    images = []

    def __init__(self):
        pg.sprite.Sprite.__init__(self, self.containers)
        self.image = self.images[0]
        scale = random.uniform(1.4,7.4)
        scale_width = int(self.image.get_width() * scale)
        scale_height = int(self.image.get_height() * scale)
        self.image = pg.transform,scale(self.image,(scale_width, scale_height))
        self.rect = self.image.get_rect()
        self.facing = random.choice((-1, 1)) * Enemy.speed
        self.frame = 0
        if self.facing < 0:
            self.rect.right = SCREENRECT.right

    def update(self):
        self.rect.move_ip(self.facing, 0)
        if not SCREENRECT.contains(self.rect):
            self.facing = -self.facing
            self.rect.top = self.rect.bottom + 1
            self.rect = self.rect.clamp(SCREENRECT)
        self.frame = self.frame + 1
        self.image = self.images[self.frame // self.animcycle % 3]


class Add_Enemy(pg.sprite.Sprite):
    """An alien space ship. That slowly moves down the screen."""

    speed = 150
    animcycle = 10

    def __init__(self):
        pg.sprite.Sprite.__init__(self, self.containers)
        self.image = pg.transform.scale(self.image, (30, 30))
        self.rect = self.image.get_rect()
        self.facing = random.choice((-1, 1)) * Add_Enemy.speed
        self.frame = 0
        if self.facing < 0:
            self.rect.right = SCREENRECT.right

    def update(self):
        self.rect.move_ip(self.facing, 0)
        if not SCREENRECT.contains(self.rect):
            self.facing = -self.facing
            self.rect.top = self.rect.bottom + 1
            self.rect = self.rect.clamp(SCREENRECT)
        

class Explosion(pg.sprite.Sprite):
    """An explosion. Hopefully the Alien and not the player!"""

    defaultlife = 12
    animcycle = 3
    images = []

    def __init__(self, actor):
        pg.sprite.Sprite.__init__(self, self.containers)
        self.image = self.images[0]
        self.rect = self.image.get_rect(center=actor.rect.center)
        self.life = self.defaultlife

    def update(self):
        """called every time around the game loop.

        Show the explosion surface for 'defaultlife'.
        Every game tick(update), we decrease the 'life'.

        Also we animate the explosion.
        """
        self.life = self.life - 1
        self.image = self.images[self.life // self.animcycle % 2]
        if self.life <= 0:
            self.kill()


class Shot(pg.sprite.Sprite):
    """a bullet the Player sprite fires."""

    speed = -11
    images = []

    def __init__(self, pos):
        pg.sprite.Sprite.__init__(self, self.containers)
        self.image = self.images[0]
        self.rect = self.image.get_rect(midbottom=pos)

    def update(self):
        """called every time around the game loop.

        Every tick we move the shot upwards.
        """
        self.rect.move_ip(0, self.speed)
        if self.rect.top <= 0:
            self.kill()


class Bomb(pg.sprite.Sprite):
    """A bomb the aliens drop."""

    speed = 9
    images = []

    def __init__(self, enemy):
        pg.sprite.Sprite.__init__(self, self.containers)
        self.image = self.images[0]
        self.rect = self.image.get_rect(midbottom=enemy.rect.move(0, 5).midbottom)

    def update(self):
        """called every time around the game loop.

        Every frame we move the sprite 'rect' down.
        When it reaches the bottom we:

        - make an explosion.
        - remove the Bomb.
        """
        self.rect.move_ip(0, self.speed)
        if self.rect.bottom >= 470:
            Explosion(self)
            self.kill()


class Score(pg.sprite.Sprite):
    """to keep track of the score."""

    def __init__(self):
        pg.sprite.Sprite.__init__(self)
        self.font = pg.font.Font(None, 20)
        self.font.set_italic(1)
        self.color = "white"
        self.lastscore = -1
        self.update()
        self.rect = self.image.get_rect().move(10, 450)

    def update(self):
        """We only update the score in update() when it has changed."""
        if SCORE != self.lastscore:
            self.lastscore = SCORE
            msg = "Score: %d" % SCORE
            self.image = self.font.render(msg, 0, self.color)


def main(winstyle=0):

    # Initialize pygame
    if pg.get_sdl_version()[0] == 2:
        pg.mixer.pre_init(44100, 32, 2, 1024)
    pg.init()
    if pg.mixer and not pg.mixer.get_init():
        print("Warning, no sound")
        pg.mixer = None

    fullscreen = False
    # Set the display mode
    winstyle = 0  # |FULLSCREEN
    bestdepth = pg.display.mode_ok(SCREENRECT.size, winstyle, 32)
    screen = pg.display.set_mode(SCREENRECT.size, winstyle, bestdepth)
    
    # Load images, assign to sprite classesa
    # (do this before the classes are used, after screen setup)
    img = load_image("kk.gif") 
    Player.images = [img, pg.transform.flip(img, 1, 0)]
    img = load_image("explosion1.gif")
    Explosion.images = [img, pg.transform.flip(img, 1, 1)]
    Enemy.images = [load_image(im) for im in ("kamata.gif","kamata.gif","kamata.gif")]
    Add_Enemy.image = load_image("chimp.png")
    Bomb.images = [load_image("bomb.gif")]
    Shot.images = [load_image("shot.gif")]
    
    # decorate the game window
    icon = pg.transform.scale(Enemy.images[0], (32, 32))
    pg.display.set_icon(icon)
    pg.display.set_caption("Pygame Enemys")
    pg.mouse.set_visible(0)

    # create the background, tile the bgd image
    bgdtile = load_image("background.gif")
    background = pg.Surface(SCREENRECT.size)
    for x in range(0, SCREENRECT.width, bgdtile.get_width()):
        background.blit(bgdtile, (x, 0))
    screen.blit(background, (0, 0))
    pg.display.flip()

    # load the sound effects
    boom_sound = load_sound("boom.wav")
    shoot_sound = load_sound("car_door.wav")
    if pg.mixer:
        music = os.path.join(main_dir, "data", "house_lo.wav")
        pg.mixer.music.load(music)
        pg.mixer.music.play(-1)

    # Initialize Game Groups
    enemys = pg.sprite.Group()
    addenemys = pg.sprite.Group()
    shots = pg.sprite.Group()
    bombs = pg.sprite.Group()
    all = pg.sprite.RenderUpdates()
    lastenemy = pg.sprite.GroupSingle()

    # assign default groups to each sprite class
    Player.containers = all
    Enemy.containers = enemys, all, lastenemy
    Add_Enemy.containers = addenemys, all, lastenemy
    Shot.containers = shots, all
    Bomb.containers = bombs, all
    Explosion.containers = all
    Score.containers = all

    # Create Some Starting Values
    global score
    enemyreload = ENEMY_RELOAD
    clock = pg.time.Clock()

    # initialize our starting sprites
    global SCORE
    player = Player()
    Enemy()  # note, this 'lives' because it goes into a sprite group
    if pg.font:
        all.add(Score())
    SCORE = 0
    Enemy.speed = 3
    score_multiple_of_5 = 0  #スコアが５の倍数かどうかチェック
    
    while player.alive():

        # get input
        for event in pg.event.get():
            if event.type == pg.QUIT:
                return
            if event.type == pg.KEYDOWN and event.key == pg.K_ESCAPE:
                return
            elif event.type == pg.KEYDOWN:
                if event.key == pg.K_f:
                    if not fullscreen:
                        print("Changing to FULLSCREEN")
                        screen_backup = screen.copy()
                        screen = pg.display.set_mode(
                            SCREENRECT.size, winstyle | pg.FULLSCREEN, bestdepth
                        )
                        screen.blit(screen_backup, (0, 0))
                    else:
                        print("Changing to windowed mode")
                        screen_backup = screen.copy()
                        screen = pg.display.set_mode(
                            SCREENRECT.size, winstyle, bestdepth
                        )
                        screen.blit(screen_backup, (0, 0))
                    pg.display.flip()
                    fullscreen = not fullscreen

        keystate = pg.key.get_pressed()
        

        # clear/erase the last drawn sprites
        all.clear(screen, background)

        # update all the sprites
        all.update()

        # handle player input
        direction = keystate[pg.K_RIGHT] - keystate[pg.K_LEFT]
        player.move(direction)
        firing = keystate[pg.K_SPACE]
        if not player.reloading and firing and len(shots) < MAX_SHOTS:
            Shot(player.gunpos())
            if pg.mixer:
                shoot_sound.play()
        player.reloading = firing

        # Create new alien
        if enemyreload:
            enemyreload = enemyreload - 1
        elif not int(random.random() * ENEMY_ODDS):
            Enemy()
            enemyreload = ENEMY_RELOAD
        #SUPERMODE 切り替え
        global SUPERMODE
        changemode = keystate[pg.K_TAB]
        if changemode:
            if SUPERMODE ==False:
                SUPERMODE=True
            else:
                SUPERMODE=False

        global Pachi
        #敵追加
        if SCORE > 0:
            if  SCORE % 20 == 0 and Pachi == False:
                Add_Enemy()
                Pachi = True
            if SCORE % 20 != 0:
                Pachi = False

        # Drop bombs
        if lastenemy and not int(random.random() * BOMB_ODDS):
            Bomb(lastenemy.sprite)

        # Detect collisions between aliens and players.
        for enemy in pg.sprite.spritecollide(player, enemys, 1):
            if pg.mixer:
                boom_sound.play()
            Explosion(enemy)
            Explosion(player)
            SCORE = SCORE + 1
            player.kill()

        # Detect collisions between aliens and players.
        for addenemy in pg.sprite.spritecollide(player, addenemys, 1):
            if pg.mixer:
                boom_sound.play()
            Explosion(enemy)
            Explosion(player)
            SCORE = SCORE + 1
            player.kill()

        # See if shots hit the aliens.
        for enemy in pg.sprite.groupcollide(enemys, shots, 1, 1).keys():
            if pg.mixer:
                boom_sound.play()
            if SUPERMODE: #SUPERMODEに入っていたら
                Shot(player.gunpos()) #playerがshotする
            Explosion(enemy)
            SCORE = SCORE + 1

        # See if shots hit the addenemy(ぱっちぃ).
        for addenemy in pg.sprite.groupcollide(addenemys, shots, 1, 1).keys():
            if pg.mixer:
                boom_sound.play()
                Explosion(addenemy)
                SCORE = SCORE + 10
            

        # See if alien boms hit the player.
        for bomb in pg.sprite.spritecollide(player, bombs, 1):
            if pg.mixer:
                boom_sound.play()
            Explosion(player)
            Explosion(bomb)
            player.kill()

        # draw the scene
        dirty = all.draw(screen)
        pg.display.update(dirty)


        # cap the framerate at 40fps. Also called 40HZ or 40 times per second.
        clock.tick(40)

        #スコアが5の倍数かどうかを確認し、Alianの速度を更新
        if SCORE % 5 == 0 and SCORE != score_multiple_of_5:
            Enemy.speed += 2
            score_multiple_of_5 = SCORE

    if pg.mixer:
        pg.mixer.music.fadeout(1000)
    pg.time.wait(1000)


# call the "main" function if running this script
if __name__ == "__main__":
    main()
    pg.quit()
