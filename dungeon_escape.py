
import arcade

#Constants
WIDTH = 1024
HEIGHT = 768
GAME_TITLE = "Dungeon Escape"
BLOCK_SCALE = .5
COIN_SIZE = 1
GRAVITY = 1
PLAYER_SCALE = 1
JUMP = 20
MOVEMENT_SPEED = 10
FACE_RIGHT = 0
FACE_LEFT = 1

#Constant for player's starting position
START_X = 100
START_Y = 256

def load_texture_pair(filename):
    """
    Load a texture pair, with the second being a mirror image.
    """
    return [
        arcade.load_texture(filename),
        arcade.load_texture(filename, flipped_horizontally=True),
    ]

class Player(arcade.Sprite):

    def __init__(self):
        super().__init__()

        self.cur_texture = 0
        self.scale = PLAYER_SCALE

        # Track our state
        self.jumping = False
        self.climbing = False
        self.is_on_ladder = False

        character = "Platform_Sprite_list/PNG/Characters/platformChar"
        self.character_face_direction = FACE_RIGHT

        self.idle_texture_pair = load_texture_pair(f"{character}_idle.png")
        self.jump_texture_pair = load_texture_pair(f"{character}_jump.png")
        #self.fall_texture_pair = arcade.load_texture_pair(f"{player}_fall.png")

        # Walking
        self.walk_textures = []
        for i in range(8):
            i = 1
            texture = load_texture_pair(f"{character}_walk{i}.png")
            self.walk_textures.append(texture)

        # Climbing
        self.climbing_textures = []
        texture = arcade.load_texture(f"{character}_climb1.png")
        self.climbing_textures.append(texture)
        texture = arcade.load_texture(f"{character}_climb2.png")
        self.climbing_textures.append(texture)

        # Set the initial texture
        self.texture = self.idle_texture_pair[0]

    def update_animation(self, delta_time: float = 1 / 60):

        # Figure out if we need to flip face left or right
        if self.change_x < 0 and self.character_face_direction == FACE_RIGHT:
            self.character_face_direction = FACE_LEFT
        elif self.change_x > 0 and self.character_face_direction == FACE_LEFT:
            self.character_face_direction = FACE_RIGHT
        

        # Climbing animation
        if self.is_on_ladder:
            self.climbing = True
        if not self.is_on_ladder and self.climbing:
            self.climbing = False
        if self.climbing and abs(self.change_y) > 1:
            self.cur_texture += 1
            if self.cur_texture > 7:
                self.cur_texture = 0
        if self.climbing:
            self.texture = self.climbing_textures[self.cur_texture // 4]
            return

        # Jumping animation
        if self.change_y > 0 and not self.is_on_ladder:
            self.texture = self.jump_texture_pair[self.character_face_direction]
            return

        # Idle animation
        if self.change_x == 0:
            self.texture = self.idle_texture_pair[self.character_face_direction]
            return

        # Walking animation
        self.cur_texture += 1
        if self.cur_texture > 7:
            self.cur_texture = 0
        self.texture = self.walk_textures[self.cur_texture][
            self.character_face_direction
        ]

    def update(self):
        if self.left < 0:
           self.left = 0
        elif self.right > WIDTH:
             self.right = WIDTH
    
class Game(arcade.Window):
    def __init__(self):
        super().__init__(WIDTH, HEIGHT, GAME_TITLE)

        #Game lists
        self.tile_map = None
        self.scene = arcade.Scene()
        self.player = None
        self.score = 0
        self.physics_engine = None
        self.camera = None
        self.gui_camera = None

    def setup(self):

        #Setup camera to be on player
        self.camera = arcade.Camera(self.width, self.height)
        self.gui_camera = arcade.Camera(self.width, self.height)

        #import map layout from tile editor
        level_one = "map_final.tmx"
        layer_options = {
            "Terrain": {"use_spatial_hash": True,},
            "Coins": {"use_spatial_hash": True,},
            "Kill_points": {"use_spacial_hash": True},
            "Ladder": {"use_spacial_hash": True},
            "Door": {"use_spacial_hash": True},
        }

        self.tile_map = arcade.load_tilemap(level_one, BLOCK_SCALE,layer_options)
        self.scene = arcade.Scene.from_tilemap(self.tile_map)

        #Create player sprite and position
        self.player = Player()
        self.player.center_x = START_X
        self.player.center_y = START_Y
        self.scene.add_sprite("Player", self.player)

        self.physics_engine = arcade.PhysicsEnginePlatformer(
            self.player, gravity_constant = GRAVITY,
            walls = self.scene["Terrain"],
            ladders = self.scene["Ladder"]
        )

        #Set the edge of the map
        self.end_of_map = self.tile_map.width

    def on_draw(self):

        #Draw the arcade window
        arcade.start_render()

        #self.camera.use()

        #Draw the scene to the arcade window
        self.scene.draw()

        #Activate the cameras
        self.gui_camera.use()

        #Draw the score and key
        score = f"Score = {self.score}"
        arcade.draw_text(score, 15, 700, 
                        arcade.csscolor.GOLD, 25)
        
    #Controls key presses on keyboard
    def on_key_press(self, key, modifiers):
        if key == arcade.key.A:
           if self.physics_engine.can_jump():
              self.player.change_y = JUMP
        elif key == arcade.key.RIGHT:
            self.player.change_x = MOVEMENT_SPEED
        elif key == arcade.key.LEFT:
            self.player.change_x = -MOVEMENT_SPEED
        elif key == arcade.key.UP:
            if self.physics_engine.is_on_ladder():
               self.player.change_y = MOVEMENT_SPEED // 2 
        
    #Controls what happens when key press is done
    def on_key_release(self, key, modifiers):
        if key == arcade.key.UP:
            if self.physics_engine.is_on_ladder():
                self.player_sprite.change_y = 0
        elif key == arcade.key.DOWN:
            if self.physics_engine.is_on_ladder():
                self.player_sprite.change_y = 0
        elif key == arcade.key.LEFT or key == arcade.key.RIGHT:
           self.player.change_x = 0
           
    def update(self, delta_time):

        self.player.update()

        #This allows physics engine to move player
        self.physics_engine.update()

        if self.physics_engine.is_on_ladder() and not self.physics_engine.can_jump():
            self.player.is_on_ladder = True
        else:
             self.player.is_on_ladder = False

        self.scene.update_animation(
            delta_time, ["Player", "Ladder"])

        #Collision for coins
        coin_hit_list = arcade.check_for_collision_with_list(
            self.player, self.scene["Coins"])

        for coin in coin_hit_list:
            coin.remove_from_sprite_lists()
            self.score += 1

        #Collision to detect player's death
        player_death = arcade.check_for_collision_with_list(
            self.player, self.scene["Kill_points"])
        
        for death in player_death:
            self.setup()
            self.update(delta_time)
            self.score = 0
        
        #Collision for entering door
        player_enters_door = arcade.check_for_collision_with_list(
               self.player, self.scene["Door"] 
        )

        for _ in player_enters_door:
            arcade.exit()

def main():
    window = Game()
    window.setup()
    arcade.run()

if __name__ == "__main__":
    main()
