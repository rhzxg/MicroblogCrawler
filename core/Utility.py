import re
import os
import sys
import time
import urllib

# Constants
class Constant:
    itemsPerPage = 20
    fetchTimeLimit = 3

    # Colors
    class Color:
        red = 31
        green = 32
        yellow = 33
        blue = 34
        default = 38
    
    # Time spans
    class TimeSpan:
        short = 0.5
        normal = 1
        long = 2

# Global variables
class GlobalVariables:
    prevLog = ""
    
class Utility:
    def TrimUrl(url: str) -> str:
        if len(re.findall(r"%23.*%23", url)) == 0 or len(re.findall(r"weibo\?q=", url)) == 0:
            Utility.PrintLog("The url is incorrect! Program exiting...", Constant.Color.red)
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

    def PrintLog(log: str, color: int = Constant.Color.default, overwrite: bool = False) -> None:
        if GlobalVariables.prevLog == log: 
            return
        prevLogLength = len(GlobalVariables.prevLog)
        currLogLength = len(log)
        
        colorPrefix = "\033[{}m".format(str(color))
        colorSuffix = "\033[0m"
        
        # make log overlap
        logWithColor = colorPrefix + log + colorSuffix
        if overwrite:
            sys.stdout.write("\r")
            if len(log) < prevLogLength:
                logWithColor += " " * (prevLogLength - currLogLength)
        else:
            logWithColor += "\n"
        
        sys.stdout.write(logWithColor)
        sys.stdout.flush()

        GlobalVariables.prevLog = log

    def SleepFor(sec: int) -> None:
        time.sleep(sec)

    def MakeContentReadable(content: str) -> str:
        content = content.replace("\n", "").replace(" ", "")
        
        # remove emoji link
        emojis = re.findall("alt=\"\[(.*?)\]", content)
        for index in range(len(emojis)):
            content = re.subn("<img(.*?)>", "[" + emojis[index] + "]", content, 1)[0]

        # remove at links
        ats = re.findall("<a(.*)>@.*?</a>", content)
        for index in range(len(ats)):
            content = re.subn("<a(.*)>@.*?</a>", ats[index] + " ", content, 1)[0]

        # remove tag links
        tags = re.findall("<a[^>]*>(.*?)</a>", content)
        for index in range(len(tags)):
            content = re.subn("<a[^>]*>(.*?)</a>", tags[index], content, 1)[0]

        return content
    
    def ExitProgram() -> None:
        input()
        sys.exit(-1)