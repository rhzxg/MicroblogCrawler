import os
import json
import time
from core.Utility import *

class CookieManager:
    def __init__(self):
        self.expiryKey = "expiry"
        self.cookieKey = "cookies"
        self.cookieFilePath = os.path.join(os.getcwd(), ".cookies")
        self.crawModeLut = ["singleItem", "multiItem"]

    def SaveCookies(self, cookies: list, crawMode: Constant.CrawlMode) -> None:
        with open(self.cookieFilePath, "w") as cookieFileObj:
            wrapper = {}
            wrapper[self.crawModeLut[crawMode]][self.expiryKey] = int(time.time()) + 3600 * 24
            wrapper[self.crawModeLut[crawMode]][self.cookieKey] = cookies
            
            json.dump(wrapper, cookieFileObj)

    def ReadCookies(self, crawMode: Constant.CrawlMode) -> list:
        if os.path.exists(self.cookieFilePath):
            with open(self.cookieFilePath, "r") as cookieFileObj:
                rawCookies = json.load(cookieFileObj)
                if self.crawModeLut[crawMode] in rawCookies:
                    if self.expiryKey in rawCookies[self.crawModeLut[crawMode]]:
                        if int(time.time() - 3600) < float(rawCookies[self.expiryKey]):
                            # would not expire in 1 hour
                            return rawCookies[self.cookieKey]
        return list()