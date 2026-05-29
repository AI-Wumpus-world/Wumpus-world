class WumpusKnowledgeBase:
    def __init__(self):
        self.reset_kb()

    def reset_kb(self): #새로운 RUN은 가상 지도 초기화
        self.visited = set()                  # 방문한 좌표 저장
        self.safe_cells = set([(1, 1)])       # 안전함이 확실한 좌표
        
        # 4x4 격자판의 모든 칸에 대해 괴물과 웅덩이가 있을 가능성을 기록해둔다
        # 처음에는 아무 정보도 없으므로 모두 Maybe로 시작한다
        self.wumpus_map = {}
        self.pit_map = {}
        
        for x in range(1, 5):
            for y in range(1, 5):
                if (x, y) != (1, 1):
                    self.wumpus_map[(x, y)] = 'Maybe'
                    self.pit_map[(x, y)] = 'Maybe'
                else:
                    self.wumpus_map[(1, 1)] = 'No'
                    self.pit_map[(1, 1)] = 'No'

    def tell(self, agent_x, agent_y, percept): #이 함수가 추론 엔진 센서신호 받아 안전여부 계산 및 학습

        stench, breeze, glitter, bump, scream = percept
        
        # 현재 서 있는 칸은 안전
        self.visited.add((agent_x, agent_y))
        self.safe_cells.add((agent_x, agent_y))
        self.wumpus_map[(agent_x, agent_y)] = 'No'
        self.pit_map[(agent_x, agent_y)] = 'No'

        directions = [(0, 1), (0, -1), (1, 0), (-1, 0)]
        adj_cells = []
        for dx, dy in directions:
            nx, ny = agent_x + dx, agent_y + dy
            if 1 <= nx <= 4 and 1 <= ny <= 4:
                adj_cells.append((nx, ny))

        # 1. 미풍없으면 -> 주변 모든 칸은 웅덩이 없음
        if not breeze:
            for cell in adj_cells:
                self.pit_map[cell] = 'No'
                
        # 2. 악취없으면 -> 주변 모든 칸은 괴물 없음
        if not stench:
            for cell in adj_cells:
                self.wumpus_map[cell] = 'No'

        # 웅덩이도 없고 괴물도 없는 구역은 확실한 안전지대
        for cell in adj_cells:
            if self.pit_map[cell] == 'No' and self.wumpus_map[cell] == 'No':
                self.safe_cells.add(cell)

    def ask_next_move(self, agent_x, agent_y, current_direction_str, has_gold): #추론기반 행동 제안

        #금 먹었으면 최단으로 귀환
        if has_gold:
            if agent_x == 1 and agent_y == 1:
                return "Climb"

            if agent_x > 1:
                return "GoForward" if current_direction_str == 'West' else "TurnLeft"
            if agent_y > 1:
                return "GoForward" if current_direction_str == 'South' else "TurnLeft"

#금 없으면 안전한곳이면서 아직 안가본곳을 찾아 전진
        adj_moves = [('East', (agent_x + 1, agent_y)), ('West', (agent_x - 1, agent_y)), 
                     ('North', (agent_x, agent_y + 1)), ('South', (agent_x, agent_y - 1))]
        
        for direction, cell in adj_moves:
            if cell in self.safe_cells and cell not in self.visited:
                if current_direction_str == direction:
                    return "GoForward"
                else:
                    return "TurnRight"
        # 만약 주변에 안가본 안전한 칸 없으면 이미 가봤던 안전한 칸으로 되돌아가기 DFS
        for direction, cell in adj_moves:
            if cell in self.safe_cells:
                if current_direction_str == direction:
                    return "GoForward"
                    
        return "TurnRight"  # 완전히 길이 막혔을 땐 제자리 회전하며 새로운 단서 탐색