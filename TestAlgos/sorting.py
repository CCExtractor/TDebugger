def bubble_sort(lst):
    for iter_num in range(len(lst) - 1, 0, -1):
        for idx in range(iter_num):
            if lst[idx] > lst[idx + 1]:
                temp = lst[idx]
                lst[idx] = lst[idx + 1]
                lst[idx + 1] = temp


def merge_sort(lst):
    if len(lst) <= 1:
        return lst
    middle = len(lst) // 2
    left_list = lst[:middle]
    right_list = lst[middle:]

    left_list = merge_sort(left_list)
    right_list = merge_sort(right_list)
    return list(merge(left_list, right_list))


def merge(left_half, right_half):
    res = []
    while len(left_half) != 0 and len(right_half) != 0:
        if left_half[0] < right_half[0]:
            res.append(left_half[0])
            left_half.remove(left_half[0])
        else:
            res.append(right_half[0])
            right_half.remove(right_half[0])
    if len(left_half) == 0:
        res = res + right_half
    else:
        res = res + left_half
    return res


def insertion_sort(lst):
    for i in range(1, len(lst)):
        j = i - 1
        nxt_element = lst[i]
        while (lst[j] > nxt_element) and (j >= 0):
            lst[j + 1] = lst[j]
            j = j - 1
        lst[j + 1] = nxt_element


def shell_sort(lst):
    gap = len(lst) // 2
    while gap > 0:
        for i in range(gap, len(lst)):
            temp = lst[i]
            j = i
            while j >= gap and lst[j - gap] > temp:
                lst[j] = lst[j - gap]
                j = j - gap
            lst[j] = temp
        gap = gap // 2


def selection_sort(lst):
    for idx in range(len(lst)):
        min_idx = idx
        for j in range(idx + 1, len(lst)):
            if lst[min_idx] > lst[j]:
                min_idx = j
        lst[idx], lst[min_idx] = lst[min_idx], lst[idx]
#From https://www.tutorialspoint.com/python_data_structure/python_sorting_algorithms.htm

def binary_search(arr, l, r, x):
    while l <= r:
        mid = l + (r - l) // 2
        if arr[mid] == x:
            return mid
        elif arr[mid] < x:
            l = mid + 1
        else:
            r = mid - 1
    return -1
# From https://www.geeksforgeeks.org/binary-search/

def knapsack(W, wt, val, n):
    if n == 0 or W == 0:
        return 0

    if wt[n - 1] > W:
        return knapsack(W, wt, val, n - 1)
    else:
        return max(val[n - 1] + knapsack(W - wt[n - 1], wt, val, n - 1), knapsack(W, wt, val, n - 1))
# From https://www.geeksforgeeks.org/python-program-for-dynamic-programming-set-10-0-1-knapsack-problem/