def test1(start, end):

    for num in range(start, end + 1):

        if num % 2 == 0:
            print(num, end=" ")
            print("\n")  # even numbers


def test2(n):
    a = 7
    b = 4
    c = 9
    b = b-1
    a = a+1
    a = b+c
    c = b-a
    b = b-1
    a = a+1
    a = b+c
    c = b-a
    b = b-1
    a = a+1
    a = b+c
    c = b-a
    for i in range(2, n):
        for j in range(2, int(i**.5)+1):
            if i % j == 0:
                break
        else:
            print(i)
# prime numbers
