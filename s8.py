import random

op = ["paper", "rock", "sisser"]
win = {"paper": "rock", "sisser": "paper", "rock": "sisser"}

pointW = 0
pointL = 0
draw = 0
play = 0
cw = int(input("How many rounds do you want to play? "))

while play < cw:
    a = random.choice(op)
    me = input("choice (rock/paper/sisser/exit/status): ")
    
    if me == "exit":
        break
    
    if me == "status":
        if play > 0:
            wr = (pointW / play) * 100
            print(f"lose: {pointL}, win: {pointW}, draw: {draw}, play: {play}/{cw}")
        else:
            print(f"No games played yet! play: 0/{cw}")
        continue
    
    if me not in op:
        print("invalid value")
        continue
    
    play = play + 1
    
    if me == a:
        draw = draw + 1
        print("draw 🤝")
    elif win[me] == a:
        pointW = pointW + 1
        print(f"win! you {me}, pc {a}")
    else:
        pointL = pointL + 1
        print(f"you lose, pc {a}")

print(f"\n{'='*30}")
print(f"Final Result")
print(f"{'='*30}")
print(f"Played: {play} of {cw}")
print(f"Wins: {pointW} | Losses: {pointL} | Draws: {draw}")

