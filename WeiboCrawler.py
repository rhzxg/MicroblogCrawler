from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.microsoft import EdgeChromiumDriverManager
import PIL.Image
import urllib.parse
import urllib.request
import time
import re
import os
import io

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
    m_prevLog = ""

class Utility:
    def TrimUrl(url: str) -> str:
        # remove all key-value argument pair
        pattern = r"&\w+=\w+"
        re.sub(pattern, "", url)

        # add sort by heat arguments
        arguementSuffixs = [
            "&xsort=hot",
            "&suball=1",
            "&tw=hotweibo",
            "&Refer=hot_hot"]
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

    def PrintLog(log: str, color: int = Colors.default) -> None:
        if GlobalVariables.m_prevLog == log: 
            return
        GlobalVariables.m_prevLog = log
        
        colorPrefix = "\033[" + str(color)
        colorSuffix = "\033[0m"
        print(colorPrefix + log + colorSuffix)

    def SleepFor(sec: int) -> None:
        time.sleep(sec)

    def SerializeEmojy(content: str) -> str:
        content = re.sub('笑cry', '笑哭', content)
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


class MicrobolgCrawler:
    def __init__(self) -> None:
        self.Initialize()
        self.StartSession()

    def Initialize(self):
        self.currFolderPath = "ErrorFolder"
        self.parentFolder = "crawled/"
        
        edgeOptions = webdriver.EdgeOptions()
        edgeOptions.add_experimental_option("excludeSwitches", ["enable-logging"])
        self.noImageMode = True
        if self.noImageMode:
            edgeOptions.use_chromium = True # is this necessary?
            noImageConfig = {"profile.managed_default_content_settings.images": 2}
            edgeOptions.add_experimental_option("prefs", noImageConfig)

        self.urlToBeCrawled = Utility.TrimUrl(input("Input a Microblog url: "))
        print(self.urlToBeCrawled)

        webDriverPath = EdgeChromiumDriverManager(path="driver/").install()
        self.browser = webdriver.Edge(webDriverPath, options=edgeOptions)

    def StartSession(self) -> None:
        self.browser.delete_all_cookies()
        self.browser.get("https://weibo.com/login.php")

        self.WaitPageLoadFinish()

        childFolder = Utility.UnquoteDirectoryFromUrl(self.urlToBeCrawled)
        self.currFolderPath = self.parentFolder + childFolder + "/"
        Utility.CreateFolder(self.currFolderPath)

        self.SaveAdditionalUrlInfo(self.urlToBeCrawled)

        self.Login()

        self.Crawl()

    def WaitPageLoadFinish(self) -> None:
        try:
            driverWait = WebDriverWait(self.browser, 60)
            driverWait.until(lambda: self.browser.execute_script("return document.readyState") == "complete")
        except TimeoutException:
            errMsg = "Timeout when waitting the page to be loaded! Please check the network connection and restart the program!"
            Utility.PrintLog(errMsg, Colors.red)

    def WaitElementLoadFinish(self, method: str, key: str, errMsg: str = "") -> None:
        try:
            driverWait = WebDriverWait(self.browser, 60)
            driverWait.until(EC.presence_of_element_located((method, key)))
        except TimeoutException:
            if len(errMsg) != 0:
                Utility.PrintLog(errMsg, Colors.red)

    def SaveAdditionalUrlInfo(self, info: str) -> None:
        with open(self.currFolderPath + "/AdditionalInfo.txt", "a", encoding="utf-8") as urlFileObject:
            urlFileObject.write(info + "\n\n")

    def Login(self) -> None:
            qrCodeImage = None
            while True:
                if self.browser.find_elements(By.CLASS_NAME, 'S_txt1'):
                    buttons = self.browser.find_elements(By.CLASS_NAME, 'S_txt1')
                    try:
                        # click the login button
                        buttons[9].click()
                        break
                    except:
                        Utility.SleepFor(2)
                        continue
                
                while True:
                    try:
                        self.browser.find_elements(By.CLASS_NAME, "tab_bar")[0].find_elements(By.TAG_NAME, "a")[1].click()

                        Utility.SleepFor(2)
                        qrCodeEleXpath = "/html/body/div[4]/div[2]/div[3]/div[2]/div[1]/img"
                        qrCodeEle = self.browser.find_elements(By.XPATH, qrCodeEleXpath)
                        qrCodeUrl = qrCodeEle[0].get_attribute("src")
                        response = urllib.request.urlopen(qrCodeUrl)
                        qrCodeImage = PIL.Image.open(io.BytesIO(response.read()))
                        qrCodeImage.show()
                        break
                    except:
                        Utility.SleepFor(2)
                        continue

                self.WaitElementLoadFinish(By.CLASS_NAME, "woo-badge-box")
                Utility.PrintLog("Login succeeded! Navigating...", Colors.green)
                qrCodeImage.close()

    def Crawl(self) -> None:
        self.browser.get(self.urlToBeCrawled)
        Utility.PrintLog("Navigating to the page to be crawled...")

        pageCount = self.GetPageCount()
        for pageNumber in range(1, pageCount + 1):
            for itemNumber in range(1, Constants.itemsPerPage + 1):
                Utility.PrintLog("Crawling page {}, item {}.".format(pageNumber, itemNumber), Colors.green)

                self.WaitPageLoadFinish()
                moreBtnXPath = "/html/body/div[1]/div[2]/div/div[2]/div[1]/div[3]/div[{}]/div/div[2]/ul/li[2]/a".format(itemNumber)
                btnLinkXPath = "/html/body/div[1]/div[2]/div/div[2]/div[1]/div[3]/div[{}]/div/div[3]/div/div[3]/a".format(itemNumber)
                moreButton = self.browser.find_elements(By.XPATH, moreBtnXPath)
                if len(moreButton) != 0:
                    Utility.PrintLog("There is no more page! Cleaning up...", Colors.red)
                    break

                

        
    def GetPageCount(self) -> int:
        pageListXPath =  "/html/body/div[1]/div[2]/div/div[2]/div[1]/div[5]/div/span/ul"
        pageList = self.browser.find_elements(By.XPATH, pageListXPath)
        return len(pageList)

if __name__ == "__main__":
    try:
        crawler = MicrobolgCrawler()
    except KeyboardInterrupt:
        Utility.PrintLog("Program stopped by force!", Colors.red)