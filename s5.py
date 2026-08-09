def minimum():
    numbers = []
    for i in range(3):
        Input = int(input(f"enter number {i+1} : "))
        numbers.append(Input)
    Min = min(numbers)
    return(f"minimum is : {Min}")


def maximum():
    numbers = []
    for i in range(3):
        Input = int(input(f"enter number {i+1} : "))
        numbers.append(Input)
    Max = max(numbers)
    return(f"minimum is : {Max}")


def avg():
    numbers = []
    for i in range(3):
        Input = int(input(f"enter number {i+1} : "))
        numbers.append(Input)
    Avg = sum(numbers) / len(numbers)
    return(f"avg is : {Avg}")


def sums():
    numbers = []
    for i in range(3):
        Input = int(input(f"enter number {i+1} : "))
        numbers.append(Input)
    Sum = sum(numbers)
    return(f"sum is : {Sum}")


choice = int(input("select def (1-4) : "))
print(choice)
if choice == 1:
    print(minimum())
elif choice == 2:
    print(maximum())
elif choice == 3:
    print(avg())
elif choice == 4:
    print(sums())
else:
    print("invalid number!")