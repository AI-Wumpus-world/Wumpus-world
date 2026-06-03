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


def shoot_arrow(env, agent):
    # 현재 에이전트 방향으로 화살 발사 맞으면 Wumpus 제거
    if agent.arrows <= 0:
        return False

    agent.arrows -= 1
    dx, dy = DIRECTION_DELTA[agent.get_direction_str()]
    x, y = agent.x + dx, agent.y + dy

    while 1 <= x <= 4 and 1 <= y <= 4:
        if env.grid[(x, y)] == "Wumpus" and env.wumpus_alive:
            env.wumpus_alive = False
            return True
        x += dx
        y += dy

    return False


def execute_action(action, env, agent):
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

        action = kb.ask_next_move(agent, percept)
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
            kb.mark_death(dead_cell, env.grid.get(dead_cell))
            ui.draw(env, agent, kb, percept, "Dead", step, message, death_count)
            time.sleep(STEP_DELAY)

            if death_count >= MAX_DEATHS:
                ui.draw(env, agent, kb, percept, "Stop", step, "사망 횟수 초과로 종료", death_count)
                break

            env.restart_same_run()
            agent.reset_agent()
            bumped = False
            scream = False
            message = "에이전트 재시작: 기존 KB 유지"
            last_action = "Restart"

    ui.wait()


if __name__ == "__main__":
    main()