from collections import deque

DIRECTION_ORDER = ["East", "South", "West", "North"]
DIRECTION_DELTA = {
    "East": (1, 0),
    "South": (0, -1),
    "West": (-1, 0),
    "North": (0, 1),
}

class WumpusKnowledgeBase:
    def __init__(self):
        self.reset_kb()

    def reset_kb(self):
        self.visited = set()                  
        self.safe_cells = set([(1, 1)])       
        
        # 확률/카운트 기반
        # 0: 없음(No), 1이상: 가능성 있음(Maybe/Yes)
        self.wumpus_prob = {}
        self.pit_prob = {}
        
        # UI 표시용 맵 
        self.wumpus_map = {}
        self.pit_map = {}
        
        for x in range(1, 5):
            for y in range(1, 5):
                self.wumpus_prob[(x, y)] = 0
                self.pit_prob[(x, y)] = 0
                if (x, y) == (1, 1):
                    self.wumpus_map[(x, y)] = 'No'
                    self.pit_map[(x, y)] = 'No'
                else:
                    self.wumpus_map[(x, y)] = 'Maybe'
                    self.pit_map[(x, y)] = 'Maybe'

    def tell(self, agent_x, agent_y, percept):
        stench, breeze, glitter, bump, scream = percept
        current_cell = (agent_x, agent_y)
        
        self.visited.add(current_cell)
        self.safe_cells.add(current_cell)
        self.wumpus_map[current_cell] = 'No'
        self.pit_map[current_cell] = 'No'
        self.wumpus_prob[current_cell] = 0
        self.pit_prob[current_cell] = 0

        directions = [(0, 1), (0, -1), (1, 0), (-1, 0)]
        adj_cells = []
        for dx, dy in directions:
            nx, ny = agent_x + dx, agent_y + dy
            if 1 <= nx <= 4 and 1 <= ny <= 4:
                adj_cells.append((nx, ny))

        # 추론 로직 강화
        for adj in adj_cells:
            # 이미 방문한 칸은 안전이 확정된 칸이므로 건너뛴다
            if adj in self.visited:
                continue
                
            # 1. 미풍(Breeze) 기반 추론
            if breeze:
                # 미풍이 있으면 주변 칸의 위험 점수를 올린다
                self.pit_prob[adj] += 1
                self.pit_map[adj] = 'Maybe'
            else:
                # 미풍이 없으면 주변 칸은 절대 웅덩이가 아니다
                self.pit_prob[adj] = 0
                self.pit_map[adj] = 'No'

            # 2. 악취(Stench) 기반 추론
            if stench:
                self.wumpus_prob[adj] += 1
                self.wumpus_map[adj] = 'Maybe'
            else:
                self.wumpus_prob[adj] = 0
                self.wumpus_map[adj] = 'No'

            # 3. 구덩이 점수도 0이고 왐퍼스 점수도 0이면 안전
            if self.pit_prob[adj] == 0 and self.wumpus_prob[adj] == 0:
                self.safe_cells.add(adj)
            else:
                # 위험 요소가 하나라도 있으면 안전 목록에서 제외 (이미 들어있었더라도)
                if adj in self.safe_cells:
                    self.safe_cells.remove(adj)

    def mark_death(self, cell, element):
        """에이전트가 죽은 칸을 확실한 위험 구역으로 기록합니다."""
        if cell in self.safe_cells:
            self.safe_cells.remove(cell)
        
        # 죽은 칸은 다시는 안 가도록 
        if element == "Pit":
            self.pit_map[cell] = "Yes"
            self.pit_prob[cell] = 999
        elif element == "Wumpus":
            self.wumpus_map[cell] = "Yes"
            self.wumpus_prob[cell] = 999

    def _in_world(self, cell):
        x, y = cell
        return 1 <= x <= 4 and 1 <= y <= 4

    def _get_neighbor(self, cell, direction):
        dx, dy = DIRECTION_DELTA[direction]
        return (cell[0] + dx, cell[1] + dy)

    def _turn_toward(self, current_direction, target_direction): 
        # 현재 방향에서 목표 방향으로 가기 위한 가장 빠른 회전 행동을 반환
        current_idx = DIRECTION_ORDER.index(current_direction)
        target_idx = DIRECTION_ORDER.index(target_direction)
        diff = (target_idx - current_idx) % 4

        if diff == 0:
            return "GoForward"
        if diff == 1:
            return "TurnRight"
        if diff == 3:
            return "TurnLeft"
        
        # 180도 회전 시 (diff == 2)
        return "TurnRight"

    def _find_path_to_target(self, start, targets, movable_cells):
        if not targets:
            return []
        queue = deque([(start, [])])
        visited = {start}

        while queue:
            cell, path = queue.popleft()

            if cell in targets:
                return path

            for direction in DIRECTION_ORDER:
                next_cell = self._get_neighbor(cell, direction)
                if next_cell in movable_cells and next_cell not in visited:
                    visited.add(next_cell)
                    queue.append((next_cell, path + [direction]))
        return []

    def ask_next_move(self, agent, percept):
        stench, breeze, glitter, bump, scream = percept
        current_cell = (agent.x, agent.y)

        # 1. 금 발견 시 줍기
        if glitter and not agent.has_gold:
            return "Grab"

        # 2. 왐퍼스 감지 시 사격
        if stench and agent.arrows > 0 and not agent.has_gold:
            return "Shoot"

        # 3. 금 획득 후 탈출
        if agent.has_gold:
            if current_cell == (1, 1):
                return "Climb"

            path_home = self._find_path_to_target(
                start=current_cell,
                targets={(1, 1)},
                movable_cells=self.safe_cells
            )

            if path_home:
                return self._turn_toward(agent.get_direction_str(), path_home[0])

        # 4. 안 가본 안전한 칸 탐험
        unvisited_safe = self.safe_cells - self.visited
        path_to_safe = self._find_path_to_target(
            start=current_cell,
            targets=unvisited_safe,
            movable_cells=self.safe_cells
        )

        if path_to_safe:
            return self._turn_toward(agent.get_direction_str(), path_to_safe[0])

        # 5. 갈 수 있는 안 가본 안전한 칸이 없으면, 이미 가본 안전한 칸 중에서 unknown(미방문) 칸과 인접한 곳으로 이동
        path_to_any_unvisited = self._find_path_to_target(
            start=current_cell,
            targets=set([(x,y) for x in range(1,5) for y in range(1,5)]) - self.visited,
            movable_cells=self.safe_cells
        )
        if path_to_any_unvisited:
            return self._turn_toward(agent.get_direction_str(), path_to_any_unvisited[0])

        # 6. 정말 안전한 곳이 더 이상 없으면 위험을 감수하고 가장 점수가 낮은 인접 칸으로 이동
        best_move = None
        min_risk = float('inf')
        
        for direction in DIRECTION_ORDER:
            next_cell = self._get_neighbor(current_cell, direction)
            if not self._in_world(next_cell) or next_cell in self.visited:
                continue
            
            risk = self.pit_prob[next_cell] + self.wumpus_prob[next_cell]
            if risk < min_risk:
                min_risk = risk
                best_move = direction

        if best_move:
            return self._turn_toward(agent.get_direction_str(), best_move)

        # 7. 완전히 고립되었다면 제자리 회전
        return "TurnRight"
