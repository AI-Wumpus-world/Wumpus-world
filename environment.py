# environment.py
import random

class WumpusEnvironment:
    def __init__(self):
        self.grid_size = 4
        self.reset()

    def reset(self):
        # 게임 시작 시 맵을 새로 부르고 요소들이 서로 겹치지 않게 배치한다
        self.grid = {}

        for x in range(1, 5):     
            for y in range(1, 5):  
                self.grid[(x, y)] = 'Empty'
    