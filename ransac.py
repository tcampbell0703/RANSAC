import numpy as np
from sklearn import linear_model
import math

#General TODO:
"""
  - should optimize arrays and things for computational eff at some point

  - collect all parameters and have a set fucntion:
    - cos() matching tolerance for clean
    - RANSAC params, currently using only stop prob
    - number of ouliers found stopping criteriea for ransacking
    - number of ransacks or min number of points where to stop ransacking
"""

class ransacked_track:
    """
    2D track found while ransacing the event
    """
    #TODO:
    """
    change hit indecies to a hit mask relative to the original indecies?
    """
    def __init__(self, in_hits, slope, intercept):
        self.hit_indecies = []
        for xx in in_hits:
            self.hit_indecies.append(xx)
        self.slope = slope[0]
        self.intercept = intercept
        self.compare_n_hits = len(self.hit_indecies)
    def add_track(self, in_track):
        if in_track.compare_n_hits > self.compare_n_hits:
            self.slope = in_track.slope
            self.intercept = in_track.intercept
            self.compare_n_hits = in_track.compare_n_hits
        for xx in in_track.hit_indecies:
            self.hit_indecies.append(xx)
    def add_hit(self, index):
        self.hit_indecies.append(index)

class viking:
    """
    for pillaging events for tracks like clusters
    """

    def __init__(self):
        self.unused_hits = []
        self.n_ransacs = 0
        self.ransacked_tracks = []

    def set_data(self, X_in, y_in):
        self.X_in = np.ndarray((len(X_in),1))
        self.y_in = np.ndarray(len(y_in))
        for ii, xx in enumerate(X_in):
            self.X_in[ii][0] = xx
        for ii, xx in enumerate(y_in):
            self.y_in[ii] = xx
        self.hit_indecies_in = np.ndarray(len(self.X_in))
        for ii in range(len(self.hit_indecies_in)):
            self.hit_indecies_in[ii] = ii

    def scale_data(self):
        x_min = 555e10
        for xx in self.X_in:
            if xx[0] < x_min:
                x_min = xx[0]
        y_min = 555e10
        for xx in self.y_in:
            if xx < y_min:
                y_min = xx
        for ii in range(len(self.X_in)):
            self.X_in[ii][0] = self.X_in[ii][0] - x_min
        for ii in range(len(self.y_in)):
            self.y_in[ii] = self.y_in[ii] - y_min

    def ransack(self):
        if self.n_ransacs == 0:
            self.X = self.X_in
            self.y = self.y_in
            self.hit_indecies = self.hit_indecies_in
        self.n_ransacs += 1

        #this_ransac = linear_model.RANSACRegressor(residual_threshold=2., stop_probability=0.99)
        this_ransac = linear_model.RANSACRegressor(stop_probability=0.9)
        try:
            this_ransac.fit(self.X, self.y)
        except:
            return
        inlier_mask = this_ransac.inlier_mask_
        outlier_mask = np.logical_not(inlier_mask)
        ninlier = 0
        for xx in inlier_mask:
            if xx:
                ninlier += 1
        if (len(inlier_mask) - ninlier) < 1:
            #save track hypothesis
            this_track = ransacked_track(self.hit_indecies, this_ransac.estimator_.coef_, 
                    this_ransac.estimator_.intercept_)
            self.ransacked_tracks.append(this_track)
            #set start ransacking again with unused hits
            self.X = np.ndarray((len(self.unused_hits),1))
            self.y = np.ndarray(len(self.unused_hits))
            self.hit_indecies = np.ndarray(len(self.unused_hits))
            for ii in range(len(self.X)):
                self.X[ii][0] = self.X_in[int(self.unused_hits[ii])][0]
            for ii in range(len(self.y)):
                self.y[ii] = self.y_in[int(self.unused_hits[ii])]
            for ii in range(len(self.hit_indecies)):
                self.hit_indecies[ii] = self.unused_hits[ii]
            self.unused_hits = []

        else:
            for xx in self.hit_indecies[outlier_mask]:
                self.unused_hits.append(xx)

            self.X = self.X[inlier_mask]
            self.y = self.y[inlier_mask]
            self.hit_indecies = self.hit_indecies[inlier_mask]

        if self.n_ransacs > 100 or len(self.X) < 5:
            return

        self.ransack()

    def get_unused_hits(self):
        self.unused_hits = [ii for ii in range(len(self.X_in))]
        for track in self.ransacked_tracks:
            for hit in track.hit_indecies:
                idel = -1
                for iuhit, uhit in enumerate(self.unused_hits):
                    if uhit == hit:
                        idel = iuhit
                        break
                if idel >= 0:
                    del self.unused_hits[idel]
        return self.unused_hits

    def get_tracks(self):
        return self.ransacked_tracks

    def clean_tracks(self):
        def cos(track1, track2):
            a1 = track1.slope
            a2 = track2.slope
            return (1+a1*a2)/(math.sqrt(1+a1*a1)*math.sqrt(1+a2*a2))
        out_tracks = []
        used_tracks = []
        tracks = self.get_tracks()
        for ii, this_track in enumerate(self.get_tracks()):
            is_used = False 
            for xx in used_tracks:
                if ii == int(xx):
                    is_used = True
                    break
            if is_used:
                continue
            used_tracks.append(ii)
            for jj, that_track in enumerate(self.get_tracks()):
                is_used = False 
                for xx in used_tracks:
                    if jj == int(xx):
                        is_used = True
                        break
                if is_used:
                    continue
                if abs(cos(tracks[ii], tracks[jj])) > 0.85:
                    this_track.add_track(that_track)
                    used_tracks.append(jj)
            out_tracks.append(this_track)
        self.ransacked_tracks = out_tracks

    def grow_tracks(self):
        evt_closest_indecies = []
        for ii in range(len(self.X_in)):
            x = self.X_in[ii][0]
            y = self.y_in[ii] 
            min_dist = 555e10
            min_index = -1
            for ii, xx in enumerate(self.ransacked_tracks):
                a = xx.slope
                b = xx.intercept
                dist = abs(a*x-y+b)/(math.sqrt(a*a+1))
                if dist < min_dist:
                    min_dist = dist
                    min_index = ii
            evt_closest_indecies.append(min_index)
            for ii in range(len(self.ransacked_tracks)):
                self.ransacked_tracks[ii].hit_indecies.clear()
            for ii, xx in enumerate(evt_closest_indecies):
                if xx == -1:
                    continue
                self.ransacked_tracks[int(xx)].add_hit(ii)

    def get_track_indecies(self):
        evt_closest_indecies = []
        for ii in range(len(self.X_in)):
            x = self.X_in[ii][0]
            y = self.y_in[ii] 
            min_dist = 555e10
            min_index = -1
            evt_dist = [min_index, min_dist]
            for ii, xx in enumerate(self.ransacked_tracks):
                a = xx.slope
                b = xx.intercept
                dist = abs(a*x-y+b)/(math.sqrt(a*a+1))
                if dist < min_dist:
                    min_dist = dist
                    min_index = ii
                evt_dist = [min_index, min_dist]
            evt_closest_indecies.append(evt_dist)
        return evt_closest_indecies

def cluster_hits(vikings, hit_data):

    x = hit_data[0]
    y = hit_data[1]
    z = hit_data[2]

    cluster_X = np.ndarray((len(x),len(vikings)))

    for ii, viking in enumerate(vikings):
        track_indecies = viking.get_track_indecies()
        for jj, index in enumerate(track_indecies):
            cluster_X[jj][ii] = index[0]

    clusters = []
    for xx in cluster_X:
        cluster = 10000*xx[0] + 100*xx[1] + xx[2]
        seen_before = False
        for cc in clusters:
            if cc == cluster:
                seen_before = True
                break
        if not seen_before:
            clusters.append(cluster)

    clusters_count = [0 for ii in range(len(clusters))]
    for xx in cluster_X:
        cluster = 10000*xx[0] + 100*xx[1] + xx[2]
        for ii, cc in enumerate(clusters):
            if cluster == cc:
                clusters_count[ii] += 1
                break

    hc_clusters = []
    for ii in range(len(clusters)):
        if clusters_count[ii] >= 10:
            hc_clusters.append(clusters[ii])


    evt_labels = []
    for xx in cluster_X:
        cluster = 10000*xx[0] + 100*xx[1] + xx[2]
        was_hc = False
        for ii, cc in enumerate(hc_clusters):
            if cluster == cc:
                evt_labels.append(ii)
                was_hc = True
                break
        if not was_hc:
            evt_labels.append(-1)

    are_unused = True
    attempts = 0
    while are_unused and attempts < 100:
        attempts += 1
        are_unused = False
        for ii, xx in enumerate(evt_labels):
            if xx == -1:
                are_unused = True
                min_dist = 555e10
                for jj in range(len(x)):
                    dist = (x[ii]-x[jj])*(x[ii]-x[jj])
                    dist += (y[ii]-y[jj])*(y[ii]-y[jj])
                    dist += (z[ii]-z[jj])*(z[ii]-z[jj])
                    if dist < min_dist:
                        min_dist = dist
                        evt_labels[ii] = evt_labels[jj]

    return evt_labels


