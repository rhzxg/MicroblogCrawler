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

    def MakeContentReadable(content: str) -> str:
        content = content.replace("\n", "").replace(" ", "")
        
        # remove emoji link
        emojis = re.findall("alt=\"(\[.*?)\]", content)
        for index in range(len(emojis)):
            content = re.subn("<img(.*?)>", "[" + emojis[index] + "]", content, 1)[0]

        # remove tag links
        tags = re.findall("<a[^>]*>(.*?)</a>", content)
        for index in range(len(emojis)):
            content = re.subn("<a[^>]*>(.*?)</a>", tags[index], content, 1)[0]

        # remove at links
        ats = re.findall("<a(.*)>@.*?</a>", content)
        for index in range(len(ats)):
            content = re.subn("<a(.*)>@.*?</a>", ats[index], content, 1)[0]
        
        return content
    
    def ExitProgram() -> None:
        sys.exit(-1)