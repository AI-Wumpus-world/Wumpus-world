# environment.py
import random

class WumpusEnvironment:
    def __init__(self):
        self.grid_size = 4
        self.reset_count = 0
        self.reset()

    def reset(self):

        self.grid = {}
        # 1. 4x4 빈 공간으로 채우기
        for x in range(1, 5):
            for y in range(1, 5):
                self.grid[(x, y)] = 'Empty'
        
        # 안전지대
        self.safe_zones = [(1, 1), (1, 2), (2, 1)]
        
        # 2. Pit 배치 (최대 2개 제한, 독립 확률 0.10)
        pit_count = 0
        for x in range(1, 5):
            for y in range(1, 5):

                if (x, y) in self.safe_zones:
                    continue

                if pit_count >= 2:
                    break
                    
                if random.random() < 0.10:
                    self.grid[(x, y)] = 'Pit'
                    pit_count += 1
                    
        # 3. Wumpus 배치 안전지대 제외 + 빈칸에
        wumpus_placed = False
        while not wumpus_placed:
            rx = random.randint(1, 4)
            ry = random.randint(1, 4)
            if (rx, ry) not in self.safe_zones and self.grid[(rx, ry)] == 'Empty':
                self.grid[(rx, ry)] = 'Wumpus'
                self.wumpus_pos = (rx, ry)
                wumpus_placed = True
                
        # 4. Gold 배치 안전지대 제외 + 빈칸에
        gold_placed = False
        while not gold_placed:
            rx = random.randint(1, 4)
            ry = random.randint(1, 4)
            if (rx, ry) not in self.safe_zones and self.grid[(rx, ry)] == 'Empty':
                self.grid[(rx, ry)] = 'Gold'
                self.gold_pos = (rx, ry)
                gold_placed = True

        self.wumpus_alive = True
        self.scream = False
        
        #맵 생성 결과 출력
        self.print_secret_map()

    def restart_same_run(self): #에이전트 죽었을 때 호출 괴물,웅덩이, 금 위치는 고정
        self.wumpus_alive = True 
        self.scream = False
        print("\n에이전트가 사망")
        self.print_secret_map()

    def print_secret_map(self): #에이전트는 못보는 지도
        print(f"\n=== 웜프스 지도 (현재 RUN) ===")
        for y in range(4, 0, -1):
            row_str = ""
            for x in range(1, 5):
                element = self.grid[(x, y)]
                row_str += f"[{element:<8}] "
            print(row_str)

    def get_percept(self, agent_x, agent_y, bumped, shot_arrow_hit): #에이전트 위치 기준 percept생성
        stench = False
        breeze = False
        
        glitter = (self.grid[(agent_x, agent_y)] == 'Gold') #현재 칸에 금있으면 Glitter는 참
        bump = bumped
        scream = shot_arrow_hit

        directions = [(0, 1), (0, -1), (1, 0), (-1, 0)]

        current_element = self.grid[(agent_x, agent_y)]
        if self.wumpus_alive and current_element == 'Wumpus':
            stench = True
        if current_element == 'Pit':
            breeze = True

        # 주변 4칸을 돌면 괴물이나 웅덩이 있는지 검사
        for dx, dy in directions:
            nx = agent_x + dx
            ny = agent_y + dy

            # 벽 넘어는 탐지 안하게 safe걸기
            if 1 <= nx <= 4 and 1 <= ny <= 4:
                neighbor = self.grid[(nx, ny)]
                
                # 주변에 웜프스 있으면 악취 발생
                if self.wumpus_alive and neighbor == 'Wumpus':
                    stench = True
                
                # 주변에 구덩이 있으면 미풍 발생
                if neighbor == 'Pit':
                    breeze = True

        # 교수님 가이드라인의 [Stench, Breeze, Glitter, Bump, Scream] 순서대로 반환합니다.
        return [stench, breeze, glitter, bump, scream]

if __name__ == "__main__": #맵 실행 확인용
    env = WumpusEnvironment()