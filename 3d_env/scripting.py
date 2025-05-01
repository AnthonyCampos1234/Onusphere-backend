# from run_env import items2

# total_volume = 0
# for item in items2:
#     total_volume += item.volume

# print(f"Total volume: {total_volume}")

import random

# gale = 0
# martin = 0

# for i in range(10000):
#     game = ''
#     while True:
#         flip = random.randint(0, 1)
#         if flip == 0:
#             game += 'H'
#         else:
#             game += 'T'
#         if len(game) >= 2:
#             if game[-2:] == 'TH':
#                 gale += 1
#                 break
#             if game[-2:] == 'HH':
#                 martin += 1
#                 break
        
# print(f"Gale: {gale}, Martin: {martin}")

jlist = []
for i in range(10000):
    p1 = 4
    p2 = 10
    p3 = 30
    for j in range(1000):
        p1 += random.randint(-1, 1)
        p2 += random.randint(-1, 1)
        p3 += random.randint(-1, 1)
        if p1 == p2 or p1 == p3 or p2 == p3:
            jlist.append(j)
            break
print(sum(jlist) / len(jlist))
