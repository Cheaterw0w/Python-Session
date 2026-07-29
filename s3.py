age = (int(input("enter your age : ")))

if age < 18:
    print("you under 18")
else:
    midterm = (int(input("enter your midterm exam mark : ")))
    while midterm > 100:
        print("please enter a valid score")
        midterm = (int(input("enter your midterm exam mark : ")))


    finalterm = (int(input("enter your final exam mark : ")))
    while finalterm > 100:
        print("please enter a valid score")
        finalterm = (int(input("enter your final exam mark : ")))
 
    res = (midterm + finalterm) // 2
    if res < 50:
        print("fail")
    elif res >= 50 and res < 70:
        print("passed")
    elif res >= 70 and res <= 100:
        print("excellent")
   

    
    