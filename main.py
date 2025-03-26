import pygame
import random
import socket
import threading
import json
import math
from enum import Enum

# Initialize Pygame
pygame.init()
pygame.mixer.init()

# Game Constants
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
FPS = 60

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)

# Game States
class GameState(Enum):
    MENU = 0
    RACING = 1
    AMULET_SELECTION = 2
    FUSION_LAB = 3
    BLACK_MARKET = 4
    CLAN_WAR = 5
    GAME_OVER = 6

# Amulet Types
class AmuletType(Enum):
    BHAIRAV_FURY = 0
    MANAKAMANA_BLESSING = 1
    JHAKRI_DRUM = 2
    KICHKANDI_WHISPER = 3
    GARUDA_TALON = 4
    YAMRAJ_BARGAIN = 5

# Clan Types
class ClanType(Enum):
    BLOOD_MANTRAS = 0
    YETI_SYNDICATE = 1
    KUMARI_CARTEL = 2
    GHOST_RIDERS = 3

# Initialize screen
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Nepal Rush")
clock = pygame.time.Clock()

# Load assets
def load_image(name, scale=1):
    try:
        image = pygame.image.load(f"assets/{name}.png").convert_alpha()
        return pygame.transform.scale(image, (int(image.get_width() * scale), int(image.get_height() * scale)))
    except:
        # Fallback if image not found
        surf = pygame.Surface((50, 50), pygame.SRCALPHA)
        pygame.draw.rect(surf, (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255)), (0, 0, 50, 50))
        return surf

# Load sounds
def load_sound(name):
    try:
        return pygame.mixer.Sound(f"assets/sounds/{name}.wav")
    except:
        # Return silent sound if not found
        return pygame.mixer.Sound(buffer=bytearray(44))

# Game assets
car_img = load_image("car", 0.5)
amulet_imgs = {
    AmuletType.BHAIRAV_FURY: load_image("bhairav", 0.2),
    AmuletType.MANAKAMANA_BLESSING: load_image("manakamana", 0.2),
    AmuletType.JHAKRI_DRUM: load_image("drum", 0.2),
    AmuletType.KICHKANDI_WHISPER: load_image("kichkandi", 0.2),
    AmuletType.GARUDA_TALON: load_image("garuda", 0.2),
    AmuletType.YAMRAJ_BARGAIN: load_image("yamraj", 0.2)
}

# Sound effects
engine_sound = load_sound("engine")
crash_sound = load_sound("crash")
amulet_pickup_sound = load_sound("powerup")
fusion_sound = load_sound("fusion")

# Fonts
font_large = pygame.font.SysFont("Arial", 48)
font_medium = pygame.font.SysFont("Arial", 32)
font_small = pygame.font.SysFont("Arial", 24)

# Amulet class
class Amulet:
    def __init__(self, amulet_type, power=1.0, curse=None):
        self.type = amulet_type
        self.power = power
        self.curse = curse
        self.charges = 3
        self.image = amulet_imgs.get(amulet_type, None)
        
    def use(self):
        if self.charges > 0:
            self.charges -= 1
            return True
        return False
    
    def get_effect(self):
        effects = {
            AmuletType.BHAIRAV_FURY: {"speed_boost": 2.0 * self.power, "curse": "random_swerve"},
            AmuletType.MANAKAMANA_BLESSING: {"repair": 0.5 * self.power, "curse": "slow_near_temples"},
            AmuletType.JHAKRI_DRUM: {"animal_spirit": True, "curse": "attracts_ghosts"},
            AmuletType.KICHKANDI_WHISPER: {"see_hidden": True, "curse": "ghostly_screams"},
            AmuletType.GARUDA_TALON: {"jump_boost": 1.5 * self.power, "curse": "lose_control_in_water"},
            AmuletType.YAMRAJ_BARGAIN: {"instant_ko": True, "curse": "lose_hp"}
        }
        return effects.get(self.type, {})

# Player class
class Player:
    def __init__(self, x, y):
        self.rect = pygame.Rect(x, y, 50, 80)
        self.speed = 5
        self.max_speed = 10
        self.health = 100
        self.amulets = []
        self.current_amulet = None
        self.clan = None
        self.karma = 50  # 0-100 scale
        self.fusion_meter = 0
        
    def move(self, dx, dy):
        self.rect.x += dx * self.speed
        self.rect.y += dy * self.speed
        
        # Boundary checking
        self.rect.x = max(0, min(self.rect.x, SCREEN_WIDTH - self.rect.width))
        self.rect.y = max(0, min(self.rect.y, SCREEN_HEIGHT - self.rect.height))
    
    def use_amulet(self):
        if self.current_amulet and self.current_amulet.use():
            return self.current_amulet.get_effect()
        return None
    
    def add_amulet(self, amulet):
        if len(self.amulets) < 5:  # Max 5 amulets
            self.amulets.append(amulet)
            return True
        return False
    
    def fuse_amulets(self, amulet1, amulet2, amulet3):
        # Simple fusion logic - in a real game this would be more complex
        if amulet1 and amulet2 and amulet3:
            # Remove the amulets
            self.amulets.remove(amulet1)
            self.amulets.remove(amulet2)
            self.amulets.remove(amulet3)
            
            # Create a new fused amulet
            new_power = (amulet1.power + amulet2.power + amulet3.power) / 3 * 1.5
            fused_type = random.choice(list(AmuletType))
            fused_amulet = Amulet(fused_type, new_power, "unstable")
            
            # Add random effects based on input amulets
            effects = []
            if amulet1.type == AmuletType.BHAIRAV_FURY or amulet2.type == AmuletType.BHAIRAV_FURY or amulet3.type == AmuletType.BHAIRAV_FURY:
                effects.append("rage_mode")
            if amulet1.type == AmuletType.MANAKAMANA_BLESSING or amulet2.type == AmuletType.MANAKAMANA_BLESSING or amulet3.type == AmuletType.MANAKAMANA_BLESSING:
                effects.append("self_heal")
            
            fused_amulet.special_effects = effects
            self.amulets.append(fused_amulet)
            return fused_amulet
        return None

# Track class
class Track:
    def __init__(self, track_type):
        self.type = track_type
        self.background = None
        self.obstacles = []
        self.special_zones = []
        self.load_track()
        
    def load_track(self):
        # In a real game, this would load from files
        if self.type == "desert":
            self.background = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
            self.background.fill((210, 180, 140))  # Sand color
            # Add desert obstacles
            for _ in range(10):
                self.obstacles.append(pygame.Rect(
                    random.randint(0, SCREEN_WIDTH - 50),
                    random.randint(0, SCREEN_HEIGHT - 50),
                    50, 50
                ))
        elif self.type == "mountain":
            self.background = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
            self.background.fill((70, 70, 70))  # Mountain color
            # Add mountain obstacles
            for _ in range(15):
                self.obstacles.append(pygame.Rect(
                    random.randint(0, SCREEN_WIDTH - 50),
                    random.randint(0, SCREEN_HEIGHT - 50),
                    random.randint(20, 80), random.randint(20, 80)
                ))
        # Add other track types...

# Black Market class
class BlackMarket:
    def __init__(self):
        self.inventory = []
        self.generate_inventory()
        
    def generate_inventory(self):
        # Generate random amulets for sale
        for _ in range(5):
            amulet_type = random.choice(list(AmuletType))
            power = random.uniform(0.8, 1.5)
            curse = random.choice([None, "random_teleport", "health_drain", "attracts_enemies"])
            price = random.randint(100, 500)
            self.inventory.append({
                "amulet": Amulet(amulet_type, power, curse),
                "price": price,
                "seller": random.choice(["Blind Trader", "Ex-Royal Mechanic", "Cyber-Sadhu"])
            })
    
    def buy_amulet(self, player, index):
        if 0 <= index < len(self.inventory):
            item = self.inventory[index]
            # In a real game, you'd have a currency system
            player.add_amulet(item["amulet"])
            self.inventory.pop(index)
            return True
        return False

# Clan War system
class ClanWar:
    def __init__(self):
        self.clans = {
            ClanType.BLOOD_MANTRAS: {"territory": 0, "members": [], "color": RED},
            ClanType.YETI_SYNDICATE: {"territory": 0, "members": [], "color": BLUE},
            ClanType.KUMARI_CARTEL: {"territory": 0, "members": [], "color": GREEN},
            ClanType.GHOST_RIDERS: {"territory": 0, "members": [], "color": (150, 150, 150)}
        }
        self.current_war = None
        
    def start_war(self, clan1, clan2):
        self.current_war = {
            "clans": [clan1, clan2],
            "score": [0, 0],
            "time_left": 300  # 5 minutes
        }
        return self.current_war
    
    def update_war(self, dt):
        if self.current_war:
            self.current_war["time_left"] -= dt
            if self.current_war["time_left"] <= 0:
                self.end_war()
                
    def end_war(self):
        if self.current_war:
            clan1, clan2 = self.current_war["clans"]
            score1, score2 = self.current_war["score"]
            
            if score1 > score2:
                winner = clan1
                loser = clan2
            else:
                winner = clan2
                loser = clan1
                
            # Update territories
            territory_change = min(3, self.clans[loser]["territory"])
            self.clans[winner]["territory"] += territory_change
            self.clans[loser]["territory"] -= territory_change
            
            self.current_war = None
            return winner
        return None

# Game class
class Game:
    def __init__(self):
        self.state = GameState.MENU
        self.player = Player(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)
        self.track = Track("desert")
        self.black_market = BlackMarket()
        self.clan_war = ClanWar()
        self.opponents = []
        self.score = 0
        self.game_time = 0
        self.network = None
        self.is_host = False
        
    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if self.state == GameState.RACING:
                        self.state = GameState.MENU
                    else:
                        self.state = GameState.RACING
                
                if event.key == pygame.K_SPACE and self.state == GameState.RACING:
                    effect = self.player.use_amulet()
                    if effect and self.network:
                        self.network.send_amulet_use(effect)
                
                if event.key == pygame.K_f and self.state == GameState.RACING:
                    if self.player.fusion_meter >= 100:
                        self.state = GameState.FUSION_LAB
                
                if event.key == pygame.K_b and self.state == GameState.RACING:
                    self.state = GameState.BLACK_MARKET
                
                if event.key == pygame.K_c and self.state == GameState.RACING:
                    if self.player.clan:
                        self.state = GameState.CLAN_WAR
            
            # Handle mouse clicks for menus
            if event.type == pygame.MOUSEBUTTONDOWN:
                if self.state == GameState.MENU:
                    # Check menu buttons
                    pass
                elif self.state == GameState.AMULET_SELECTION:
                    # Check amulet selection
                    pass
                elif self.state == GameState.FUSION_LAB:
                    # Check fusion lab buttons
                    pass
                elif self.state == GameState.BLACK_MARKET:
                    # Check black market purchases
                    pass
        
        return True
    
    def update(self, dt):
        if self.state == GameState.RACING:
            keys = pygame.key.get_pressed()
            dx, dy = 0, 0
            
            if keys[pygame.K_LEFT] or keys[pygame.K_a]:
                dx = -1
            if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
                dx = 1
            if keys[pygame.K_UP] or keys[pygame.K_w]:
                dy = -1
            if keys[pygame.K_DOWN] or keys[pygame.K_s]:
                dy = 1
                
            self.player.move(dx, dy)
            
            # Update game time
            self.game_time += dt
            
            # Update opponents (AI or network players)
            for opponent in self.opponents:
                # Simple AI movement
                opponent.rect.x += random.randint(-1, 1) * opponent.speed
                opponent.rect.y += random.randint(-1, 1) * opponent.speed
                
                # Boundary checking
                opponent.rect.x = max(0, min(opponent.rect.x, SCREEN_WIDTH - opponent.rect.width))
                opponent.rect.y = max(0, min(opponent.rect.y, SCREEN_HEIGHT - opponent.rect.height))
            
            # Update clan war
            if self.clan_war.current_war:
                self.clan_war.update_war(dt)
            
            # Regenerate fusion meter
            self.player.fusion_meter = min(100, self.player.fusion_meter + 0.1)
        
        return True
    
    def render(self):
        screen.fill(BLACK)
        
        if self.state == GameState.MENU:
            self.render_menu()
        elif self.state == GameState.RACING:
            self.render_racing()
        elif self.state == GameState.AMULET_SELECTION:
            self.render_amulet_selection()
        elif self.state == GameState.FUSION_LAB:
            self.render_fusion_lab()
        elif self.state == GameState.BLACK_MARKET:
            self.render_black_market()
        elif self.state == GameState.CLAN_WAR:
            self.render_clan_war()
        elif self.state == GameState.GAME_OVER:
            self.render_game_over()
        
        pygame.display.flip()
    
    def render_menu(self):
        title = font_large.render("Nepal Rush", True, WHITE)
        screen.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 100))
        
        # Menu options
        start_text = font_medium.render("Press SPACE to Start", True, WHITE)
        screen.blit(start_text, (SCREEN_WIDTH // 2 - start_text.get_width() // 2, 300))
    
    def render_racing(self):
        # Draw track background
        screen.blit(self.track.background, (0, 0))
        
        # Draw obstacles
        for obstacle in self.track.obstacles:
            pygame.draw.rect(screen, (100, 100, 100), obstacle)
        
        # Draw player
        screen.blit(car_img, self.player.rect)
        
        # Draw opponents
        for opponent in self.opponents:
            pygame.draw.rect(screen, RED, opponent.rect)
        
        # Draw HUD
        health_text = font_small.render(f"Health: {self.player.health}", True, WHITE)
        screen.blit(health_text, (10, 10))
        
        score_text = font_small.render(f"Score: {self.score}", True, WHITE)
        screen.blit(score_text, (10, 40))
        
        time_text = font_small.render(f"Time: {self.game_time:.1f}s", True, WHITE)
        screen.blit(time_text, (10, 70))
        
        # Draw current amulet
        if self.player.current_amulet:
            amulet_text = font_small.render(f"Amulet: {self.player.current_amulet.type.name}", True, WHITE)
            screen.blit(amulet_text, (10, 100))
            
            charges_text = font_small.render(f"Charges: {self.player.current_amulet.charges}", True, WHITE)
            screen.blit(charges_text, (10, 130))
        
        # Draw fusion meter
        pygame.draw.rect(screen, (50, 50, 50), (SCREEN_WIDTH - 210, 10, 200, 20))
        pygame.draw.rect(screen, (0, 200, 200), (SCREEN_WIDTH - 210, 10, 200 * (self.player.fusion_meter / 100), 20))
        fusion_text = font_small.render("Fusion Energy", True, WHITE)
        screen.blit(fusion_text, (SCREEN_WIDTH - 210, 35))
        
        # Draw clan info
        if self.player.clan:
            clan_text = font_small.render(f"Clan: {self.player.clan.name}", True, self.clan_war.clans[self.player.clan]["color"])
            screen.blit(clan_text, (SCREEN_WIDTH - 210, 70))
            
            territory_text = font_small.render(f"Territory: {self.clan_war.clans[self.player.clan]['territory']}", True, WHITE)
            screen.blit(territory_text, (SCREEN_WIDTH - 210, 100))
    
    def render_amulet_selection(self):
        # Semi-transparent background
        s = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        s.fill((0, 0, 0, 200))
        screen.blit(s, (0, 0))
        
        title = font_large.render("Select an Amulet", True, WHITE)
        screen.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 50))
        
        # Display available amulets
        for i, amulet in enumerate(self.player.amulets):
            x = 200 + (i % 3) * 300
            y = 150 + (i // 3) * 200
            
            # Draw amulet image
            if amulet.image:
                screen.blit(amulet.image, (x, y))
            
            # Draw amulet info
            name_text = font_medium.render(amulet.type.name.replace("_", " "), True, WHITE)
            screen.blit(name_text, (x, y + 100))
            
            # Highlight if selected
            if amulet == self.player.current_amulet:
                pygame.draw.rect(screen, GREEN, (x - 5, y - 5, 110, 110), 3)
    
    def render_fusion_lab(self):
        # Semi-transparent background
        s = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        s.fill((0, 0, 0, 200))
        screen.blit(s, (0, 0))
        
        title = font_large.render("Fusion Lab", True, WHITE)
        screen.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 50))
        
        # Display fusion slots
        pygame.draw.rect(screen, (50, 50, 50), (SCREEN_WIDTH // 2 - 150, 150, 300, 100))
        pygame.draw.rect(screen, (50, 50, 50), (SCREEN_WIDTH // 2 - 150, 300, 300, 100))
        pygame.draw.rect(screen, (50, 50, 50), (SCREEN_WIDTH // 2 - 150, 450, 300, 100))
        
        # Display available amulets
        for i, amulet in enumerate(self.player.amulets):
            x = 50 + (i % 4) * 150
            y = 150 + (i // 4) * 100
            
            # Draw amulet image
            if amulet.image:
                screen.blit(amulet.image, (x, y))
    
    def render_black_market(self):
        # Semi-transparent background
        s = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        s.fill((0, 0, 0, 200))
        screen.blit(s, (0, 0))
        
        title = font_large.render("Black Market", True, WHITE)
        screen.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 50))
        
        # Display market items
        for i, item in enumerate(self.black_market.inventory):
            x = 100 + (i % 2) * 500
            y = 150 + (i // 2) * 200
            
            # Draw amulet image
            if item["amulet"].image:
                screen.blit(item["amulet"].image, (x, y))
            
            # Draw item info
            name_text = font_medium.render(item["amulet"].type.name.replace("_", " "), True, WHITE)
            screen.blit(name_text, (x + 100, y))
            
            seller_text = font_small.render(f"Seller: {item['seller']}", True, (200, 200, 200))
            screen.blit(seller_text, (x + 100, y + 40))
            
            price_text = font_small.render(f"Price: {item['price']}", True, (200, 200, 0))
            screen.blit(price_text, (x + 100, y + 70))
    
    def render_clan_war(self):
        # Semi-transparent background
        s = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        s.fill((0, 0, 0, 200))
        screen.blit(s, (0, 0))
        
        title = font_large.render("Clan War", True, WHITE)
        screen.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 50))
        
        if self.clan_war.current_war:
            # Display current war status
            clan1, clan2 = self.clan_war.current_war["clans"]
            score1, score2 = self.clan_war.current_war["score"]
            time_left = self.clan_war.current_war["time_left"]
            
            clan1_text = font_medium.render(f"{clan1.name}: {score1}", True, self.clan_war.clans[clan1]["color"])
            screen.blit(clan1_text, (SCREEN_WIDTH // 2 - 200, 150))
            
            vs_text = font_medium.render("VS", True, WHITE)
            screen.blit(vs_text, (SCREEN_WIDTH // 2 - vs_text.get_width() // 2, 150))
            
            clan2_text = font_medium.render(f"{clan2.name}: {score2}", True, self.clan_war.clans[clan2]["color"])
            screen.blit(clan2_text, (SCREEN_WIDTH // 2 + 100, 150))
            
            time_text = font_medium.render(f"Time Left: {time_left:.1f}s", True, WHITE)
            screen.blit(time_text, (SCREEN_WIDTH // 2 - time_text.get_width() // 2, 200))
        else:
            # Display clan selection
            for i, clan in enumerate(ClanType):
                x = SCREEN_WIDTH // 2 - 100
                y = 150 + i * 100
                
                pygame.draw.rect(screen, self.clan_war.clans[clan]["color"], (x, y, 200, 80))
                
                clan_text = font_medium.render(clan.name.replace("_", " "), True, WHITE)
                screen.blit(clan_text, (x + 100 - clan_text.get_width() // 2, y + 40 - clan_text.get_height() // 2))
    
    def render_game_over(self):
        title = font_large.render("Game Over", True, RED)
        screen.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 100))
        
        score_text = font_medium.render(f"Final Score: {self.score}", True, WHITE)
        screen.blit(score_text, (SCREEN_WIDTH // 2 - score_text.get_width() // 2, 200))
        
        restart_text = font_medium.render("Press R to Restart", True, WHITE)
        screen.blit(restart_text, (SCREEN_WIDTH // 2 - restart_text.get_width() // 2, 300))

# Network class
class NetworkManager:
    def __init__(self, host, port):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.host = host
        self.port = port
        self.connected = False
        self.is_host = False
        
    def connect(self):
        try:
            self.socket.connect((self.host, self.port))
            self.connected = True
            return True
        except:
            return False
        
    def host_game(self):
        try:
            self.socket.bind((self.host, self.port))
            self.socket.listen(1)
            self.is_host = True
            return True
        except:
            return False
    
    def accept_connection(self):
        conn, addr = self.socket.accept()
        self.socket = conn
        self.connected = True
        return True
    
    def send_data(self, data):
        try:
            self.socket.send(json.dumps(data).encode())
            return True
        except:
            return False
    
    def receive_data(self):
        try:
            data = self.socket.recv(1024).decode()
            return json.loads(data) if data else None
        except:
            return None
    
    def send_amulet_use(self, effect):
        self.send_data({"type": "amulet_use", "effect": effect})
    
    def close(self):
        self.socket.close()
        self.connected = False

# Main game loop
def main():
    game = Game()
    running = True
    
    # Initialize network (optional)
    network = NetworkManager("localhost", 5555)
    if input("Host game? (y/n): ").lower() == "y":
        if network.host_game():
            print("Waiting for connection...")
            network.accept_connection()
            game.is_host = True
    else:
        if network.connect():
            print("Connected to host")
    
    game.network = network
    
    # Main game loop
    last_time = pygame.time.get_ticks()
    while running:
        current_time = pygame.time.get_ticks()
        dt = (current_time - last_time) / 1000.0  # Delta time in seconds
        last_time = current_time
        
        # Handle network events
        if network.connected:
            data = network.receive_data()
            if data:
                if data["type"] == "amulet_use":
                    # Handle opponent amulet use
                    pass
        
        # Handle game events
        running = game.handle_events()
        
        # Update game state
        running = game.update(dt) and running
        
        # Render game
        game.render()
        
        # Cap the frame rate
        clock.tick(FPS)
    
    # Clean up
    if network.connected:
        network.close()
    pygame.quit()

if __name__ == "__main__":
    main()
