#!/usr/bin/env python3
# Author: Emmanuel Odeke <odeke@ualberta.ca>

import os
import time
import math
import threading

isCallable = lambda obj: hasattr(obj, '__call__')
isCallableAttr = lambda obj, attr: hasattr(obj, attr) and isCallable(getattr(obj, attr))

pathExists = lambda qPath: qPath and os.path.exists(qPath)
accessTimeChecker = lambda path: os.path.getatime(path)
creationTimeChecker = lambda path: os.path.getctime(path)

class DirWatch:
    def __init__(self, dirPath=None, sleepTimeout=10):
        if not pathExists(dirPath):
            raise Exception("Unknown directory")

        self.__pathToWatch = dirPath
        self.__sleepTimeout = sleepTimeout or 10
        self.__eventMemoizer = dict()
        self.__purgeableAction = lambda p: 'Purgeable: %s'%(p)
        self.__retainableAction = lambda p: 'Fresh: %s'%(p)
        
    def setOnPurgeableDetected(self, onPurge):
        self.__purgeableAction = onPurge

    def getPurgeableDetected(self):
        return self.__purgeableAction

    def setOnRetainableDetected(self, onRetain):
        self.__retainableAction = onRetain

    def getRetainableDetected(self):
        return self.__retainableAction

    def getPaths(self, lastSaveTime=0, statTimeAccessor=creationTimeChecker, maxDepth=-1):
        freshPaths = []
        purgeable = []
        for root, dirs, paths in os.walk(self.__pathToWatch):
            for path in paths:
                joinedPath = os.path.join(os.path.abspath(root), path)
                if statTimeAccessor(joinedPath) >= lastSaveTime:
                    freshPaths.append(joinedPath)
                else:
                    purgeable.append(joinedPath)

            if hasattr(maxDepth, '__divmod__') and maxDepth >= 0:
                maxDepth = math.floor(maxDepth)
                if maxDepth == 0: break
                else: maxDepth -= 1

        freshTh = purgeTh = None
        
        if purgeable:
            purgeTh = self.runByEventTrigger(
                self.__handleByBucket, purgeable, self.__purgeableAction,
            )
            purgeTh.start()

        if freshPaths:
            freshTh = self.runByEventTrigger(
                self.__handleByBucket, freshPaths, self.__retainableAction,
            )
            freshTh.start()

        return freshTh, purgeTh

    def __handleByBucket(self, eventHandler, elemBucket, generalAction):
        for elem in elemBucket:
            try:
                generalAction(elem)
            except Exception as e:
                print(e)

    def __handleRun(self, associatedEvent, *args):
        threshTime = args[0] if args else 0
        maxDepth = args[1] if len(args) > 1 else -1
        while not associatedEvent.is_set():
            freshTh, purgeTh = self.getPaths(threshTime, maxDepth=maxDepth) 
            print('\033[92mSleeping for ', self.__sleepTimeout, '\033[00m')
            threshTime = time.time()
            associatedEvent.wait(self.__sleepTimeout)

        print('\033[92mExiting now\033[00m')

    def __kill(self, eventHandler):
        if isCallableAttr(eventHandler, 'set'):
            print('\033[93mInvoking \'set\' method to kill thread\033[00m')
            return eventHandler.set() or True
        else:
            print('\033[31mCannot invoke \'set\' of eventHandler', eventHandler, '\033[00m')
            return False

    def kill(self, th):
        eventHandler = self.__eventMemoizer.get(th, None)
        if self.__kill(eventHandler):
            if isCallableAttr(th, 'join'):
                if isCallableAttr(th, 'isAlive') and th.isAlive():
                    th.join()

                print('\033[42mSuccessfully exited', th, '\033[00m')
            else:
                print('\033[91mCould not join', th, '\033[00m')
        else:
            print('\033[42mFailed to exit', th, '\033[00m')

    def killAll(self):
        for th in self.__eventMemoizer:
            self.kill(th)

    def bootStrap(self, thresholdTime):
        runner = self.runByEventTrigger(self.__handleRun, thresholdTime)
        if isCallableAttr(runner, 'start'):
            print('Starting', runner)
            runner.start()
        return runner

    def runByEventTrigger(self, func, *args):
        associatedEvent = threading.Event()
        # Usage of the above credited to a post on StackOverflow
        patchedArgs = (associatedEvent,) + args
        runner = threading.Thread(
            target=func, args=patchedArgs
        )
        self.__eventMemoizer[runner] = associatedEvent
        return runner

def main():
    dW = DirWatch('.')
    runner = dW.bootStrap(time.time())

    try:
        while runner.isAlive():
            time.sleep(2)
    except KeyboardInterrupt:
        dW.killAll()
    finally:
        print('Bye now..')

if __name__ == '__main__':
    main()
