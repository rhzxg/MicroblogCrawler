from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.microsoft import EdgeChromiumDriverManager
import PIL.Image
import urllib.parse
import urllib.request
import webbrowser
import time
import re
import os
import io

# Constants
class Colors:
    RED = 31
    GREEN = 32
    YELLOW = 33
    BLUE = 34
    DEFAULT = 38

class GlobalVariables:
    # Global variables
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

    def PrintLog(log: str, color: int = Colors.DEFAULT) -> None:
        colorPrefix = "\033[" + str(color)
        colorSuffix = "\033[0m"

        if m_prevLog == log: 
            return
        m_prevLog = log

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

        errMsg = "Timeout! Please check your Internet connection and restart the program."
        self.WaitForEleLoadFinish(By.CLASS_NAME, "S_txt1", errMsg)

        childFolder = Utility.UnquoteDirectoryFromUrl(self.urlToBeCrawled)
        self.currFolderPath = self.parentFolder + childFolder + "/"
        Utility.CreateFolder(self.currFolderPath)

        #self.SaveAdditionalUrlInfo()

        self.LoginIn()

    def WaitForEleLoadFinish(self, method: str, key: str, errMsg: str = "") -> None:
        try:
            driverWait = WebDriverWait(self.browser, 60)
            driverWait.until(EC.presence_of_element_located((method, key)))
        except TimeoutException:
            if len(errMsg) != 0:
                Utility.PrintLog(errMsg, Colors.RED)

    def SaveAdditionalUrlInfo(self, info: str) -> None:
        with open(self.currFolderPath + "/AdditionalInfo.txt", "a", encoding="utf-8") as urlFileObject:
            urlFileObject.write(info + "\n\n")

    def LoginIn(self) -> None:
            qrCodeImage = None
            while True:
                if self.browser.find_elements(By.CLASS_NAME, 'S_txt1'):
                    a = self.browser.find_elements(By.CLASS_NAME, 'S_txt1')
                    try:
                        a[9].click()
                    except:
                        Utility.SleepFor(2)
                        continue
                
                while True:
                    try:
                        # click the login button
                        self.browser.find_elements(By.CLASS_NAME, "tab_bar")[0].find_elements(By.TAG_NAME, "a")[1].click()

                        #Utility.SleepFor(2)
                        qrCodeEleXpath = "/html/body/div[4]/div[2]/div[3]/div[2]/div[1]/img"
                        qrCodeEle = self.browser.find_elements(By.XPATH, qrCodeEleXpath)
                        qrCodeUrl = qrCodeEle[0].get_attribute("src")
                        response = urllib.request.urlopen(qrCodeUrl)
                        qrCodeImage = PIL.Image.open(io.BytesIO(response.read()))
                        qrCodeImage.show()
                        break
                    except:
                        #Utility.SleepFor(2)
                        continue

                self.WaitForEleLoadFinish(By.CLASS_NAME, "woo-badge-box")
                Utility.PrintLog("Page loaded successfully! Waiting for navigation...", Colors.GREEN)
               

    def Craw(self) -> None:
        self.browser.get(self.urlToBeCrawled)
        Utility.PrintLog("Navigating into detail pages...")


if __name__ == "__main__":
    try:
        crawler = MicrobolgCrawler()
    except KeyboardInterrupt:
        Utility.PrintLog("Program stopped by force!", Colors.RED)