import numpy as np
from matplotlib import pyplot as plt

from sklearn import linear_model, datasets

import csv


filepath = "./csv/train_0011.csv"

X_data = []
y_data = []
with open(filepath) as csv_file:
    csv_reader = csv.reader(csv_file, delimiter=',')
    line_count = 0
    for row in csv_reader:
        used_row = True
        for ii, xx in enumerate(row):
            if ii == 0:
                if int(xx) < 2:
                    used_row = False
                    break
            if ((ii-1)%4) == 1:
                X_data.append(float(xx))
            elif ((ii-1)%4) == 2:
                y_data.append(float(xx))
        if used_row:
            n_nonzero = 0
            for ii in range(len(X_data)):
                if X_data[ii] == 0 and y_data[ii] == 0:
                    continue
                n_nonzero += 1
            if n_nonzero > 50 and n_nonzero<400:
                line_count += 1
            if line_count == 2:
                break
            else:
                X_data.clear()
                y_data.clear()

X = np.ndarray((n_nonzero,1))
y = np.ndarray(n_nonzero)

idata = 0
for ii in range(len(X_data)):
    if X_data[ii] == 0 and y_data[ii] == 0:
        continue 
    X[idata][0] = X_data[ii]
    y[idata] = y_data[ii] 
    idata += 1

np.save('test_X_data.npy', X)
np.save('test_y_data.npy', y)

unused_X = []
unused_y = []

for iteration in range(10):
    ransac = linear_model.RANSACRegressor()
    ransac.fit(X, y)
    inlier_mask = ransac.inlier_mask_
    outlier_mask = np.logical_not(inlier_mask)
    ninlier = 0
    for xx in inlier_mask:
        if xx:
            ninlier += 1
    if (len(inlier_mask) - ninlier) < 4:
        break
    print(ninlier, "kept out of", len(inlier_mask), ".  fraction:", ninlier/len(inlier_mask))

    line_X = np.ndarray((1000,1))
    xline_point = X.min()
    iline = 0
    while xline_point < X.max():
        if iline < 1000:
            line_X[iline][0] = xline_point
            iline += 1
        xline_point += (X.max() - X.min())/1000

    line_y_ransac = ransac.predict(line_X)

    plt.figure()
    lw = 2
    plt.scatter(X[inlier_mask], y[inlier_mask], color='yellowgreen', marker='.',
                label='Inliers')
    plt.scatter(X[outlier_mask], y[outlier_mask], color='gold', marker='.',
                label='Outliers')
    plt.plot(line_X, line_y_ransac, color='cornflowerblue', linewidth=lw,
             label='RANSAC regressor')
    plt.legend()
    plt.xlabel("X")
    plt.ylabel("Y")
    savestr = "./RANSAC_test"
    savestr += str(iteration)
    savestr += ".png"
    plt.savefig(savestr)

    for xx in X[outlier_mask]:
        unused_X.append(xx[0])
    for xx in y[outlier_mask]:
        unused_y.append(xx)

    X = X[inlier_mask]
    y = y[inlier_mask]

    print(len(X))

X = np.ndarray((len(unused_X),1))
y = np.ndarray(len(unused_y))

if len(X) != len(y):
    print("u dun fvked up")
    exit()

for ii, xx in enumerate(unused_X):
    X[ii][0] = xx
    y[ii] = unused_y[ii]

