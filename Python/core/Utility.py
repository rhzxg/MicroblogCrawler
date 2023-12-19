import re
import os
import sys
import time
import urllib

# Constants
class Constant:
    itemsPerPage = 20
    fetchTimeLimit = 3

    # Crawl Mode
    class CrawlMode:
        singleItem = 0
        multiItem = 1

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
        timeout = 5

# Global variables
class GlobalVariables:
    prevLog = ""
    id2GenderDict = {}
    
class Utility:
    singleItemPattern = r"\d+\/[a-zA-Z\d]+"
    multiItemPattern = r"%23.*%23"

    def DetectCrawlMode(url: str) -> Constant.CrawlMode:
        if len(re.findall(Utility.singleItemPattern, url)) != 0:
            Utility.PrintLog("Crawl mode: Single-Item", Constant.Color.blue)
            return Constant.CrawlMode.singleItem
        elif len(re.findall(Utility.multiItemPattern, url)) != 0 and len(re.findall(r"weibo\?q=", url)) != 0:
            Utility.PrintLog("Crawl mode: Multi-Item", Constant.Color.blue)
            return Constant.CrawlMode.multiItem
        
        Utility.PrintLog("The url is incorrect! Program exiting...", Constant.Color.red)
        Utility.ExitProgram()

    def TrimUrl(url: str, crawlMode: Constant.CrawlMode) -> str:
        if crawlMode == Constant.CrawlMode.singleItem:
            # remove trailing argument if any
            pattern = r"\?cid=\d+"
            url = re.sub(pattern, "", url)
        elif crawlMode == Constant.CrawlMode.multiItem:
            url = url.replace("weibo?q=", "hot?q=")

            # remove all key-value argument pairs
            pattern = r"&\w+=\w+"
            url = re.sub(pattern, "", url)

            # add sort by heat arguments
            arguementSuffixs = [
                "&xsort=hot",
                "&suball=1",
                "&tw=hotweibo",
                "&Refer=weibo_hot"]
            for arguement in arguementSuffixs:
                url += arguement

        return url
    
    def UnquoteDirectoryFromUrl(url: str, crawlMode: Constant.CrawlMode) -> str:
        folderName = "DefaultFolder"
        if crawlMode == Constant.CrawlMode.singleItem:
            patternTitle = re.findall(Utility.singleItemPattern, url)
            if len(patternTitle) != 0:
                folderName = re.sub(r"/", "-", patternTitle[0])
        elif crawlMode == Constant.CrawlMode.multiItem:
            base64Title = re.findall(Utility.singleItemPattern, url)
            if len(base64Title) != 0:
                folderName = urllib.parse.unquote(base64Title[0])
        return folderName

    def CreateFolder(path: str) -> None:
        try:
            os.makedirs(path, exist_ok=True)
        except:
            Utility.PrintLog("Folder created failed! Program exiting...", Constant.Color.red)
            Utility.ExitProgram()

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

    def SleepFor( sec: int) -> None:
        time.sleep(sec)

    def MakeContentReadable(content: str) -> str:
        content = content.replace("\n", "").replace(" ", "")
        
        # remove emoji link
        emojis = re.findall("alt=\"\[(.*?)\]", content)
        for index in range(len(emojis)):
            content = re.subn("<img(.*?)>", "[" + emojis[index] + "]", content, 1)[0]

        # remove <a></a> tag links
        tags = re.findall("<a[^>]*>(.*?)</a>", content)
        for index in range(len(tags)):
            content = re.subn("<a[^>]*>(.*?)</a>", tags[index] + " ", content, 1)[0]

        # remove <img> tag links
        content = re.sub("<img(.*)>", "", content)

        return content
    
    def SeperateTimeAndIPAddress(mixedStr: str) -> list:
        pattern = r"(\d.*\d) 来自(.*)"
        match = re.search(pattern, mixedStr)
        if match:
            time = match.group(1)
            location = match.group(2)
            return [time, location]
        return [mixedStr, "Unknown"]
    
    def ExitProgram() -> None:
        input()
        exit()