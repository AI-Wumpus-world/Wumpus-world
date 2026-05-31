import time
from collections import deque

from environment import WumpusEnvironment
from agent import WumpusAgent
from knowledge_base import WumpusKnowledgeBase
from ui_manager import WumpusUI


DIRECTION_ORDER = ["East", "South", "West", "North"]
DIRECTION_DELTA = {
    "East": (1, 0),
    "South": (0, -1),
    "West": (-1, 0),
    "North": (0, 1),
}

GRID_MIN = 1
GRID_MAX = 4
MAX_STEPS = 100
MAX_DEATHS = 3
STEP_DELAY = 0.7


def in_world(cell):
    x, y = cell
    return GRID_MIN <= x <= GRID_MAX and GRID_MIN <= y <= GRID_MAX


def turn_toward(current_direction, target_direction):
    """현재 방향에서 목표 방향으로 가기 위한 행동 하나를 반환한다."""
    current_idx = DIRECTION_ORDER.index(current_direction)
    target_idx = DIRECTION_ORDER.index(target_direction)
    diff = (target_idx - current_idx) % 4

    if diff == 0:
        return "GoForward"
    if diff == 1:
        return "TurnRight"
    if diff == 3:
        return "TurnLeft"

    # 정반대 방향이면 한 번에 180도 회전할 수 없으므로 우회전부터 수행
    return "TurnRight"


def get_neighbor(cell, direction):
    dx, dy = DIRECTION_DELTA[direction]
    return (cell[0] + dx, cell[1] + dy)


def find_path_to_target(start, targets, movable_cells):
    """movable_cells 안에서 start -> targets 중 하나까지 가는 방향 리스트를 BFS로 찾는다."""
    queue = deque([(start, [])])
    visited = {start}

    while queue:
        cell, path = queue.popleft()

        if cell in targets and cell != start:
            return path

        for direction in DIRECTION_ORDER:
            next_cell = get_neighbor(cell, direction)
            if next_cell in movable_cells and next_cell not in visited:
                visited.add(next_cell)
                queue.append((next_cell, path + [direction]))

    return []


def choose_action(agent, kb, percept):
    """
    Percept -> Reasoning -> Action 흐름 중 Reasoning/Action 선택 부분.
    1순위: 현재 칸에 금이 있으면 Grab
    2순위: 금을 가진 뒤 (1,1)이면 Climb
    3순위: 금을 가진 뒤 안전한 칸을 통해 (1,1)로 복귀
    4순위: 아직 방문하지 않은 안전 칸 탐험
    5순위: 안전 칸이 없으면 인접한 미방문 unknown 칸을 위험 감수하고 탐험
    6순위: 전부 막히면 회전
    """
    stench, breeze, glitter, bump, scream = percept
    current_cell = (agent.x, agent.y)

    if glitter and not agent.has_gold:
        return "Grab"

    if agent.has_gold:
        if current_cell == (1, 1):
            return "Climb"

        path_home = find_path_to_target(
            start=current_cell,
            targets={(1, 1)},
            movable_cells=kb.safe_cells
        )

        if path_home:
            return turn_toward(agent.get_direction_str(), path_home[0])

        # 혹시 안전 경로 탐색이 실패하면 좌표 기준으로 원점 방향 복귀
        if agent.x > 1:
            return turn_toward(agent.get_direction_str(), "West")
        if agent.y > 1:
            return turn_toward(agent.get_direction_str(), "South")

    # 방문하지 않은 안전 칸을 우선 탐험
    unvisited_safe = kb.safe_cells - kb.visited
    path_to_safe = find_path_to_target(
        start=current_cell,
        targets=unvisited_safe,
        movable_cells=kb.safe_cells
    )

    if path_to_safe:
        return turn_toward(agent.get_direction_str(), path_to_safe[0])

    # 안전 칸이 더 이상 없으면, 바로 옆 unknown 칸 중 하나를 탐험한다.
    # 프로젝트 시연에서 에이전트가 멈추지 않도록 하기 위한 보조 규칙이다.
    for direction in DIRECTION_ORDER:
        next_cell = get_neighbor(current_cell, direction)
        if not in_world(next_cell):
            continue
        if next_cell in kb.visited:
            continue
        if kb.pit_map.get(next_cell) == "Yes" or kb.wumpus_map.get(next_cell) == "Yes":
            continue
        return turn_toward(agent.get_direction_str(), direction)

    return "TurnRight"


def shoot_arrow(env, agent):
    """현재 에이전트 방향으로 화살 발사. 맞으면 Wumpus 제거."""
    if agent.arrows <= 0:
        return False

    agent.arrows -= 1
    dx, dy = DIRECTION_DELTA[agent.get_direction_str()]
    x, y = agent.x + dx, agent.y + dy

    while in_world((x, y)):
        if env.grid[(x, y)] == "Wumpus" and env.wumpus_alive:
            env.wumpus_alive = False
            return True
        x += dx
        y += dy

    return False


def mark_death_cell(kb, env, cell):
    """죽은 칸을 KB에 위험 칸으로 기록해서 다음 시도 때 피하게 한다."""
    element = env.grid.get(cell)
    kb.safe_cells.discard(cell)

    if element == "Pit":
        kb.pit_map[cell] = "Yes"
    elif element == "Wumpus":
        kb.wumpus_map[cell] = "Yes"


def execute_action(action, env, agent):
    """
    action을 실제 객체에 반영한다.
    return: bumped, scream, dead, message
    """
    bumped = False
    scream = False
    dead = False
    message = ""

    if action == "TurnRight":
        agent.turn_right()
        message = "오른쪽으로 90도 회전"

    elif action == "TurnLeft":
        agent.turn_left()
        message = "왼쪽으로 90도 회전"

    elif action == "GoForward":
        _, bumped = agent.go_forward()
        if bumped:
            message = "벽에 부딪힘: Bump=True"
        else:
            current_cell = (agent.x, agent.y)
            current_element = env.grid[current_cell]

            if current_element == "Pit":
                agent.is_alive = False
                dead = True
                message = "Pit에 빠져 사망"
            elif current_element == "Wumpus" and env.wumpus_alive:
                agent.is_alive = False
                dead = True
                message = "Wumpus를 만나 사망"
            else:
                message = "한 칸 전진"

    elif action == "Grab":
        if env.grid[(agent.x, agent.y)] == "Gold":
            agent.has_gold = True
            env.grid[(agent.x, agent.y)] = "Empty"
            message = "Gold 획득"
        else:
            message = "현재 칸에 Gold가 없음"

    elif action == "Shoot":
        scream = shoot_arrow(env, agent)
        message = "화살 명중: Scream=True" if scream else "화살 빗나감"

    elif action == "Climb":
        if agent.has_gold and (agent.x, agent.y) == (1, 1):
            agent.climb_out = True
            message = "Gold를 가지고 (1,1)에서 탈출 성공"
        else:
            message = "아직 Climb 조건이 아님"

    else:
        message = f"알 수 없는 행동: {action}"

    return bumped, scream, dead, message


def main():
    env = WumpusEnvironment()
    agent = WumpusAgent()
    kb = WumpusKnowledgeBase()

    # True: 실제 PIT/WUMPUS/GOLD까지 보여주는 발표/디버깅 모드
    # False: 에이전트가 탐험하며 알게 된 정보 중심으로 표시
    ui = WumpusUI(show_secret=True)

    bumped = False
    scream = False
    death_count = 0
    message = "Start"
    last_action = "None"

    for step in range(1, MAX_STEPS + 1):
        percept = env.get_percept(agent.x, agent.y, bumped, scream)
        kb.tell(agent.x, agent.y, percept)

        ui.draw(env, agent, kb, percept, last_action, step, message, death_count)
        time.sleep(STEP_DELAY)

        action = choose_action(agent, kb, percept)
        bumped, scream, dead, message = execute_action(action, env, agent)
        last_action = action

        ui.draw(env, agent, kb, percept, last_action, step, message, death_count)
        time.sleep(STEP_DELAY)

        if agent.climb_out:
            ui.draw(env, agent, kb, percept, "Climb", step, "탐험 종료: 성공", death_count)
            break

        if dead:
            death_count += 1
            dead_cell = (agent.x, agent.y)
            mark_death_cell(kb, env, dead_cell)
            ui.draw(env, agent, kb, percept, "Dead", step, message, death_count)
            time.sleep(STEP_DELAY)

            if death_count >= MAX_DEATHS:
                ui.draw(env, agent, kb, percept, "Stop", step, "사망 횟수 초과로 종료", death_count)
                break

            # 가이드라인의 '죽기 직전까지 인식된 state 유지'에 맞춰 KB는 유지하고 agent만 시작점으로 복귀
            env.restart_same_run()
            agent.reset_agent()
            bumped = False
            scream = False
            message = "에이전트 재시작: 기존 KB 유지"
            last_action = "Restart"

    ui.wait()


if __name__ == "__main__":
    main()
