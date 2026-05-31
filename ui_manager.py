import turtle

class WumpusUI:
    def __init__(self, cell_size=90, show_secret=True):
        self.cell_size = cell_size
        self.show_secret = show_secret
        
        self.board_left = -300
        self.board_bottom = -230
        self.status_x = 130
        self.status_y = 180

        self.screen = turtle.Screen()
        self.screen.title("Wumpus World")
        self.screen.setup(width=900, height=650)
        self.screen.bgcolor("white")
        self.screen.tracer(0)

        self.pen = turtle.Turtle()
        self.pen.hideturtle()
        self.pen.speed(0)   
    
    def cell_origin(self, x, y):
        # Wumpus 좌표 (1, 1)을 turtle 화면의 왼쪽 아래 칸으로 변환
        sx = self.board_left + (x - 1) * self.cell_size
        sy = self.board_bottom + (y - 1) * self.cell_size
        return sx, sy
    
    def write(self, x, y, text, size=11, align="center", style="normal"):
        self.pen.penup()
        self.pen.goto(x, y)
        self.pen.write(text, align=align, font=("Arial", size, style))
    
    def draw_rect(self, x, y, width, height, fill="white", outline="black"):
        self.pen.penup()
        self.pen.goto(x, y)
        self.pen.pendown()
        self.pen.color(outline, fill)
        self.pen.begin_fill()
        for _ in range(2):
            self.pen.forward(width)
            self.pen.left(90)
            self.pen.forward(height)
            self.pen.left(90)
        self.pen.end_fill()
        self.pen.color("black")
    
    def get_cell_center(self, cell, env, kb):
        if self.show_secret:
            element = env.grid.get(cell, "Empty")
            if element == "Pit":
                return "misty rose"
            if element == "Wumpus":
                return "plum"
            if element == "Gold":
                return "lemon chiffon"
        
        if cell in kb.visited:
            return "light cyan"
        if cell in kb.safe_cells:
            return "honeydew"
        return "white"
    
    def draw_cell_info(self, x, y, env, kb):
        cell = (x, y)
        sx, sy = self.cell_origin(x, y)
        cx = sx + self.cell_size / 2

        # 좌표
        self.write(sx + 7, sy + self.cell_size - 18, f"({x},{y})", size=8, align="left")

        # 실제 맵 정보: 발표/디버깅용. 최종에서 숨기려면 show_secret=False
        if self.show_secret:
            element = env.grid.get(cell, "Empty")
            if element == "Pit":
                self.write(cx, sy + 57, "PIT", size=12, style="bold")
            elif element == "Wumpus":
                if env.wumpus_alive:
                    self.write(cx, sy + 57, "WUMPUS", size=10, style="bold")
                else:
                    self.write(cx, sy + 57, "DEAD WUMPUS", size=10, style="bold")
            elif element == "Gold":
                self.write(cx, sy + 57, "GOLD", size=12, style="bold")
        
        # 에이전트가 지금까지 탐험한 결과
        tags = []
        if cell in kb.visited:
            tags.append("Visited")
        if cell in kb.safe_cells:
            tags.append("Safe")
        
        if tags:
            self.write(cx, sy + 33, " / ".join(tags), size=9)
        
        pit_state = kb.pit_map.get(cell, "?")
        wumpus_state = kb.wumpus_map.get(cell, "?")
        self.write(cx, sy + 12, f"P:{pit_state} W:{wumpus_state}", size=8)
    
    def draw_agent(self, agent):
        sx, sy = self.cell_origin(agent.x, agent.y)
        cx = sx + self.cell_size / 2
        cy = sy + self.cell_size / 2

        symbol = {
            "East": "A>",
            "South": "Av",
            "West": "A<",
            "North": "A^"
        }.get(agent.get_direction_str(), "A")

        self.write(cx, cy - 8, symbol, size=22, style="bold")

    def draw_board(self, env, agent, kb):
        for y in range(1, 5):
            for x in range(1, 5):
                cell = (x, y)
                sx, sy = self.cell_origin(x, y)
                fill = self.get_cell_center(cell, env, kb)
                self.draw_rect(sx, sy, self.cell_size, self.cell_size, fill=fill)
                self.draw_cell_info(x, y, env, kb)
        self.draw_agent(agent)
    
    def format_percept(self, percept):
        if percept is None:
            return "None"
        
        names = ["Stench", "Breeze", "Glitter", "Bump", "Scream"]
        return "\n".join([f"- {name}: {value}" for name, value in zip(names, percept)])
    
    def draw_status(self, agent, percept, action, step, message, death_count):
        x = self.status_x
        y = self.status_y

        self.write(x, y + 90, "Wumpus World", size=19, align="left", style="bold")
        self.write(x, y + 55, f"Step: {step}", size=12, align="left")
        self.write(x, y + 30, f"Position: ({agent.x}, {agent.y})", size=12, align="left")
        self.write(x, y + 5, f"Direction: {agent.get_direction_str()}", size=12, align="left")
        self.write(x, y - 20, f"Arrows: {agent.arrows}", size=12, align="left")
        self.write(x, y - 45, f"Has Gold: {agent.has_gold}", size=12, align="left")
        self.write(x, y - 70, f"Deaths: {death_count}", size=12, align="left")

        self.write(x, y - 110, "Percept", size=13, align="left", style="bold")
        self.write(x, y - 245, self.format_percept(percept), size=10, align="left")

        self.write(x, y - 285, "Action", size=13, align="left", style="bold")
        self.write(x, y - 310, str(action), size=12, align="left")

        self.write(x, y - 350, "Message", size=13, align="left", style="bold")
        self.write(x, y - 375, message, size=10, align="left")

    def draw_legend(self):
        x = self.board_left
        y = self.board_bottom + self.cell_size * 4 + 25
        self.write(x, y + 20, "Legend", size=12, align="left", style="bold")
        self.write(x, y, "Visited=탐험함 / Safe=안전 추론 / P=Pit 추론 / W=Wumpus 추론", size=10, align="left")
        self.write(x, y - 18, "show_secret=True이면 실제 PIT/WUMPUS/GOLD도 함께 표시됨", size=10, align="left")
    
    def draw(self, env, agent, kb, percept=None, action="None", step=0, message="", death_count=0):
        try:
            self.pen.clear()
        except TclError:
            return
        except turtle.Terminator:
            return

        self.draw_board(env, agent, kb)
        self.draw_status(agent, percept, action, step, message, death_count)
        
        try:
            self.screen.update()
        except TclError:
            return
        except turtle.Terminator:
            return
    
    def wait(self):
        self.screen.mainloop()

