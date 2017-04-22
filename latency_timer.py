from time import clock
class LatencyTimer:
    thresh = 0.1 # required delay between plays
                 # - seems like timer.clock() might not be in seconds
    last_time = -1

    def __init__(self, thresh=None):
        if thresh is not None:
            self.thresh = thresh
        self.last_time = clock()

    def reset(self):
        #print "Resetting timer"
        self.last_time = clock()

    def check(self):
        current_time = clock()
        diff = current_time - self.last_time
        #print "Time since last timer reset: %f"%diff
        if diff > self.thresh:
            return True
        else:
            return False
