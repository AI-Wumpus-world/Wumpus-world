class WumpusAgent:
    def __init__(self):
        # 0: 동, 1: 남, 2: 서, 3: 북
        self.directions = ['East', 'South', 'West', 'North']
        self.reset_agent()

    def reset_agent(self): #새로운 RUN 또는 부활시 에이전트의 상태를 기본값으로 초기화(지식은 유지)
        self.x = 1
        self.y = 1
        self.head = 0       # 처음 머리방향 동쪽
        self.arrows = 3     # 화살 3개
        self.has_gold = False
        self.is_alive = True
        self.climb_out = False

    def get_direction_str(self):# 현재 머리방향 출력용
        return self.directions[self.head]

    def turn_right(self): # 우회전 (현재 방향 + 1) % 4
        self.head = (self.head + 1) % 4
        return "TurnRight"

    def turn_left(self): # 좌회전 (현재 방향 - 1) % 4
        self.head = (self.head - 1) % 4
        return "TurnLeft"

    def go_forward(self): # 현재 머리방향으로 한칸 전진
        next_x = self.x
        next_y = self.y

        # 머리 방향에 따른 좌표 변화 계산
        if self.head == 0:    # 동
            next_x += 1
        elif self.head == 1:  # 남
            next_y -= 1
        elif self.head == 2:  # 서
            next_x -= 1
        elif self.head == 3:  # 북
            next_y += 1

        # 벽 충돌 체크 4x4 벗어나는지 확인
        if 1 <= next_x <= 4 and 1 <= next_y <= 4:
            self.x = next_x
            self.y = next_y
            return "GoForward", False  # 전진 성공 Bump 없음
        else:
            return "GoForward", True   # 전진 실패 벽에 부딪힘 -> Bump 발생