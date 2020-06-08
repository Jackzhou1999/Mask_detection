losslist = [1,2,3,4,5,6]
valloss = [1,3,4,5,3,2]

import matplotlib.pyplot as plt

plt.subplot()
plt.plot(range(len(losslist)), losslist, 'black', label='train')
plt.plot(range(len(valloss)), valloss, 'red', label='val')

plt.ylabel("loss")
plt.grid(True)
plt.show()
