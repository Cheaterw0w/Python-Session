mark = []
for i in range(5):
    score = int(input(f"enter exam mark {i+1} : "))
    mark.append(score)


avg = sum(mark) / len(mark)

variance = 0

for score in mark:
    variance += (score - avg) ** 2

variance = variance / len(mark)

print(f"variance : {variance}")
print(f"your avg : {avg}")
minimum = min(mark)
print(f"your minimum score is : {minimum}")
maximum = max(mark)
print(f"your minimum score is : {maximum}")
    
    
    