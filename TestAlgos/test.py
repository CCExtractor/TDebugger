def test1(start, end):

    for num in range(start, end + 1):

        if num % 2 == 0:
            print(num, end=" ")
            print("\n")  # even numbers


def test2(n):
    for i in range(2, n):
        for j in range(2, int(i**.5)+1):
            if i % j == 0:
                break
        else:
            print(i)
# prime numbers
