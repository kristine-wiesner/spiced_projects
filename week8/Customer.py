import numpy as np
from tiles_skeleton import OFS, TILE_SIZE
class Customer:

    def __init__(self, id, state, t_mat, terrain_map, image, x=15, y=10):
        self.id = id
        self.state = state
        self.t_mat = t_mat
        self.checkout_visits = 0
        self.a = t_mat.columns.values.tolist()
        self.terrain_map = terrain_map
        self.image = image
        self.x = x
        self.y = y

    def __repr__(self):
        return f'{self.id} is in {self.state}'
    
    def is_active(self):
        return self.checkout_visits < 2
    
    def next_state(self):
        p = self.t_mat.loc[self.state].to_list()
        self.state = np.random.choice(self.a, p=p)
        self.x, self.y = self.move(self.state)
        if (self.state) == 'checkout':
            self.checkout_visits = self.checkout_visits + 1

    def draw(self, frame):
        xpos = OFS + self.x * TILE_SIZE
        ypos = OFS + self.y * TILE_SIZE
        frame[ypos:ypos+TILE_SIZE, xpos:xpos+TILE_SIZE] = self.image

    def move(self, location):
        if location == 'fruit':
            return (11,4)
        if location == 'dairy':
            return (3,3)
        if location == 'spices':
            return (10,5)
        if location == 'drinks':
            return (7,4)
        if location == 'checkout':
            return (3,8)
        return (15,10)
    
