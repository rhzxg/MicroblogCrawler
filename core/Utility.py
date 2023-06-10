import urllib
import time
import sys
import re
import os

# Colors
class Colors:
    red = 31
    green = 32
    yellow = 33
    blue = 34
    default = 38

# Constants
class Constants:
    itemsPerPage = 20

# Global variables
class GlobalVariables:
    prevLog = ""
    
class Utility:
    def TrimUrl(url: str) -> str:
        if len(re.findall(r"%23.*%23", url)) == 0 or len(re.findall(r"weibo\?q=", url)) == 0:
            Utility.PrintLog("The url is incorrect! Program exiting...", Colors.red)
            Utility.ExitProgram()

        url = url.replace("weibo?q=", "hot?q=")

        # remove all key-value argument pairs
        pattern = r"&\w+=\w+"
        re.sub(pattern, "", url)

        # add sort by heat arguments
        arguementSuffixs = [
            "&xsort=hot",
            "&suball=1",
            "&tw=hotweibo",
            "&Refer=weibo_hot"]
        for arguement in arguementSuffixs:
            url += arguement

        return url
    
    def UnquoteDirectoryFromUrl(url: str) -> str:
        pattern = r"%23.*%23"
        base64Title = re.findall(pattern, url)
        if len(base64Title) == 0:
            return "ErrorFolder"
        
        directory = urllib.parse.unquote(base64Title[0])
        return directory

    def CreateFolder(path: str) -> None:
        try:
            os.mkdir(path)
        except:
            pass

    def PrintLog(log: str, color: int = Colors.default, overwrite: bool = False) -> None:
        if GlobalVariables.prevLog == log: 
            return
        prevLogLength = len(GlobalVariables.prevLog)
        currLogLength = len(log)
        
        colorPrefix = "\033[{}m".format(str(color))
        colorSuffix = "\033[0m"
        
        # make log overlap
        logWithColor = colorPrefix + log + colorSuffix
        if overwrite:
            logWithColor = "\r" + logWithColor
            if len(log) < prevLogLength:
                logWithColor += " " * (prevLogLength - currLogLength)
        
        print(logWithColor)

        GlobalVariables.prevLog = log

    def SleepFor(sec: int) -> None:
        time.sleep(sec)

    def SerializeEmojy(content: str) -> str:
        content = content.replace("\n", "").replace(" ", "")

        content = re.sub('笑cry', '[笑哭]', content)
        content = re.sub('\[打call\]', '[打电话]', content)
        content = re.sub('\[good\]', '[挺好]', content)
        content = re.sub('\[ok\]', '[棒]', content)
        content = re.sub('\[doge\]', '[狗头]', content)
        content = re.sub('<a(.*)">@', " @", content)
        content = re.sub('</a>:', " ", content)
        
        images = re.findall('alt="\[([\u4e00-\u9fa5]*)\]', content)
        for index in range(len(images)):
            content = re.subn('<img(.*?)>', "[" + images[index] + "]", content, 1)[0]
        return content
    
    def ExitProgram() -> None:
        sys.exit(-1)