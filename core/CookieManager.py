import os
import json
import time

class CookieManager:
    def __init__(self):
        self.expiryKey = "expiry"
        self.cookieKey = "cookies"
        self.cookieFilePath = os.path.join(os.getcwd(), ".cookies")

    def SaveCookies(self, cookies: list) -> None:
        with open(self.cookieFilePath, "w") as cookieFileObj:
            wrapper = {}
            wrapper[self.expiryKey] = int(time.time()) + 3600 * 24
            wrapper[self.cookieKey] = cookies
            
            json.dump(wrapper, cookieFileObj)

    def ReadCookies(self) -> list:
        if os.path.exists(self.cookieFilePath):
            with open(self.cookieFilePath, "r") as cookieFileObj:
                rawCookies = json.load(cookieFileObj)
                if self.expiryKey in rawCookies:
                    if int(time.time() - 3600) < float(rawCookies[self.expiryKey]):
                        # would not expire in 1 hour
                        return rawCookies[self.cookieKey]
        return list()