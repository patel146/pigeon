#!/usr/bin/env python3
# Author: Emmanuel Odeke <odeke@ualberta.ca>

import time
import threading
import multiprocessing

class JobRunner(object):
    def __init__(self):
        self.__spawnedThreadList = []

    def locker(self, func, lock):
        def __anon(*args, **kwargs):
            hasLockAttrs = hasattr(lock, 'acquire') and hasattr(lock, 'release')

            # If already held, don't block/wait until lock is released
            # by current holder Just go to the else-clause and the
            # appropriate action will follow
            if hasLockAttrs and lock.acquire(False):
                # print('\033[47mAcquired lock for func:', func, '\033[00m')
                results = dict()
                try:
                    results['data'] = func(*args, **kwargs)
                except Exception as ex:
                    print('Exception', ex, func)
                    results['error'] = ex
                finally:
                    # Release the lock
                    # print('\033[46mReleased lock for func:', func, '\033[00m')
                    lock.release()
                return results
            else:
                print('\033[41mCould not acquire lock. Try again\033[00m', func)
                if hasLockAttrs:
                    return dict(
                        needsRetry=True,
                        error='Could not acquire lock. Try again later'
                    )
                else:
                    return dict(
                        error="Lock object must have methods 'acquire' and 'release'"
                    )

        return __anon

    def retryable(self, func, timeout=0.2):
        def __functor(*args, **kwargs):
            results = func(*args, **kwargs)
            if results and hasattr(results, 'get'):
                data = results.get('data', None)
                if results.get('needsRetry', False):
                    # print('Successful response from ', func, data)
                    print('\033[33mRetrying after', timeout, ' secs\033[00m')
                    time.sleep(timeout)
                    return __functor(*args, **kwargs)
                else:
                    return data
            else:
                msg = "Couldn't retry as 'get' method undefined for data"
                return dict(results=results, msg=msg)

        return __functor

    def __run(self, func, callback, *args, **kwargs):
        functor = self.retryable(func)
        results = functor(*args, **kwargs)
        if callback and hasattr(callback, '__call__'):
            return callback(results)
        else:
            return results

    def __runASync(self, func, callback, *args, **kwargs):
        runnable = threading.Thread(
            target=self.__run, args=(func, callback, args, kwargs,)
        )
        runnable.start()
        self.__spawnedThreadList.append(runnable)

    def __runSync(self, func, *args, **kwargs):
        return self.__run(func, None, *args, **kwargs)

    def run(self, func, lock, callback, *args, **kwargs):
        __functor = self.locker(func, lock if lock else multiprocessing.RLock())
        if callback:
            return self.__runASync(__functor, callback, *args, **kwargs)
        else:
            return self.__runSync(__functor, *args, **kwargs)

    def close(self):
        for i, th in enumerate(self.__spawnedThreadList):
            if th.isAlive():
                print('\033[42mJoining thread: #', i, th, '\033[00m')
                th.join()

def main():
    sharedResource = dict()
    def decrementByOne(*args, **kwargs):
        print('before', sharedResource, args, kwargs)
        sharedResource[2] = sharedResource.get(2, 1) - 1
        print('after', sharedResource)

    def incrementByTwo(*args, **kwargs):
        print('before', sharedResource, args, kwargs)
        sharedResource[2] = sharedResource.get(2, 0) + 2
        print('after', sharedResource)

    def printResource(*args, **kwargs):
        print(sharedResource, args, kwargs)

    runner = JobRunner()

    while sharedResource.get(2, 0) < 30:
        runner.run(incrementByTwo, None, printResource)
        runner.run(decrementByOne, None, printResource)

if __name__ == '__main__':
    main()
