from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.microsoft import EdgeChromiumDriverManager
from .Utility import *
from .ExcelSerializer import *
import PIL.Image
import urllib.parse
import urllib.request
import io

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

        self.urlToBeCrawled = Utility.TrimUrl(input("Input a Microblog link: "))

        webDriverPath = EdgeChromiumDriverManager(path="driver/").install()
        self.browser = webdriver.Edge(webDriverPath, options=edgeOptions)

    def StartSession(self) -> None:
        self.browser.delete_all_cookies()
        self.browser.get("https://weibo.com/login.php")

        childFolder = Utility.UnquoteDirectoryFromUrl(self.urlToBeCrawled)
        self.currFolderPath = self.parentFolder + childFolder + "/"
        Utility.CreateFolder(self.currFolderPath)

        self.SaveAdditionalUrlInfo(self.urlToBeCrawled)

        #self.WaitPageLoadFinish()

        self.Login()

        self.Crawl()

    def WaitPageLoadFinish(self) -> None:
        try:
            driverWait = WebDriverWait(self.browser, 60)
            driverWait.until(lambda a: self.browser.execute_script("return document.readyState") == "complete")
        except TimeoutException:
            errMsg = "Timeout while waiting for the page to be loaded! Please check the network connection and restart the program!"
            Utility.PrintLog(errMsg, Colors.red)

    def WaitElementLoadFinish(self, method: str, key: str, timeout : float = 60, errMsg: str = "") -> bool:
        try:
            driverWait = WebDriverWait(self.browser, timeout)
            driverWait.until(EC.presence_of_element_located((method, key)))
            Utility.SleepFor(0.5)
            return False
        except TimeoutException:
            if len(errMsg) != 0:
                Utility.PrintLog(errMsg, Colors.red)
            return True

    def SaveAdditionalUrlInfo(self, info: str) -> None:
        if not os.path.exists(self.currFolderPath):
            os.makedirs(self.currFolderPath)
        with open(self.currFolderPath + "AdditionalInfo.txt", "a", encoding="utf-8") as urlFileObject:
            urlFileObject.write(info + "\n\n")

    def Login(self) -> None:
            qrCodeImage = None
            try:
                loginBtnPath = r"/html/body/div[1]/div[1]/div/div[1]/div/div/div[3]/div[2]/ul/li[3]/a"
                self.WaitElementLoadFinish(By.XPATH, loginBtnPath)
                self.browser.find_element(By.XPATH, loginBtnPath).click()

                self.WaitElementLoadFinish(By.CLASS_NAME, "tab_bar")
                self.browser.find_elements(By.CLASS_NAME, "tab_bar")[0].find_elements(By.TAG_NAME, "a")[1].click()
                
                qrCodeEleXpath = "/html/body/div[4]/div[2]/div[3]/div[2]/div[1]/img"
                self.WaitElementLoadFinish(By.XPATH, qrCodeEleXpath)
                qrCodeEle = self.browser.find_element(By.XPATH, qrCodeEleXpath)
                qrCodeUrl = qrCodeEle.get_attribute("src")
                response = urllib.request.urlopen(qrCodeUrl)
                qrCodeImage = PIL.Image.open(io.BytesIO(response.read()))
                qrCodeImage.show()
            except:
                errMsg = "Error occurred while getting the QR code. Please restart the program!"
                Utility.PrintLog(errMsg, Colors.red)
                Utility.ExitProgram()
                
            self.WaitElementLoadFinish(By.CLASS_NAME, "woo-badge-box")
            Utility.PrintLog("Login succeeded! Redirecting...", Colors.green)
            qrCodeImage.close()

    def Crawl(self) -> None:
        self.browser.get(self.urlToBeCrawled)
        Utility.PrintLog("Redirecting to the page to be crawled...")

        pageCount = self.GetPageCount()
        Utility.PrintLog("Found {} pages.".format(pageCount))
        for pageNumber in range(1, pageCount + 1):
            for itemNumber in range(1, Constants.itemsPerPage + 1):
                Utility.PrintLog("Crawling page {}, item {}.".format(pageNumber, itemNumber), Colors.green)

                self.WaitPageLoadFinish()

                # click the comment button if there is one
                commentBtnXPath = "/html/body/div[1]/div[2]/div/div[2]/div[1]/div[3]/div[{}]/div/div[2]/ul/li[2]/a".format(itemNumber)
                commentButton = self.browser.find_elements(By.XPATH, commentBtnXPath)
                if len(commentButton) == 0:
                    Utility.PrintLog("There is no more blogs! Cleaning up...", Colors.red)
                    continue
                else:
                    try:
                        commentButton[0].click()
                    except:
                        Utility.PrintLog("Wrong button would be clicked. Skipping...", Colors.default, True)
                        continue

                # click the show more button if there is one
                showMoreBtnXPath = "/html/body/div[1]/div[2]/div/div[2]/div[1]/div[3]/div[{}]/div/div[3]/div/div[3]/a".format(itemNumber)
                timeout = self.WaitElementLoadFinish(By.XPATH, showMoreBtnXPath, 5)
                fileName = "page" + str(pageNumber) + "-item" + str(itemNumber)
                if timeout:
                    self.CrawlOnCurrentPage(itemNumber - 1, fileName)
                else:
                    showMoreButton = self.browser.find_element(By.XPATH, showMoreBtnXPath)
                    url = showMoreButton.get_attribute("href")
                    self.CrawlOnDetailedPage(url, fileName)

        Utility.PrintLog("Program finished. Hit Enter key to exit.", Colors.blue)
        input()
        self.browser.close()

    def GetPageCount(self) -> int:
        try:
            Utility.SleepFor(2)
            pages = self.browser.find_element(By.CLASS_NAME, "s-scroll").find_elements(By.TAG_NAME, "li")
            return 1 if (len(pages)) == 0 else len(pages)
        except:
            return 1

    def CrawlOnCurrentPage(self, itemIndex: int, fileName: str) -> None:
        Utility.PrintLog("Crawling on current page...")

        excelSerializer = ExcelSerializer()

        mainContent = self.browser.find_elements(By.CLASS_NAME, "txt")[itemIndex].get_attribute("innerText")
        mainContent = Utility.MakeContentReadable(mainContent)

        excelSerializer.WriteMainContent(mainContent)

        comments = None
        exception = False
        try:
            comments = self.browser.find_elements(By.CLASS_NAME, "card-wrap")[itemIndex].find_elements(
                By.CLASS_NAME, "list")[0].find_elements(By.CLASS_NAME, "card-review")
        except:
            exception = True

        if exception or len(comments) == 0:
            excelSerializer.WriteLine(["", "", "", "", "", "No one commented on this blog."])
            excelSerializer.Save(self.currFolderPath, fileName)
            excelSerializer.Close()
            return
        else:
            for index in range(len(comments)):
                baseNodeEle = comments[index].find_elements(By.CLASS_NAME, "content")[0]
                contentType = "c-o"
                rawLikeCount = baseNodeEle.find_elements(By.CLASS_NAME, "fun")[0].find_elements(
                    By.TAG_NAME, "li")[-1].find_elements(By.TAG_NAME, "span")[0].get_attribute("innerText")
                likeCount = rawLikeCount if len(rawLikeCount) else '0'
                # raw_wbid be like: //weibo.com/u/xxx?refer...
                # What we need is only the xxx between u/ and ?refer.
                rawUserID = baseNodeEle.find_elements(By.CLASS_NAME, "txt")[0].find_elements(
                    By.TAG_NAME, "a")[0].get_attribute("href")
                userID = re.findall('/u/[0-9]*\?', rawUserID)[0][3:-1]
                userName = baseNodeEle.find_elements(By.CLASS_NAME, "txt")[0].find_elements(
                    By.TAG_NAME, "a")[0].get_attribute("innerText")
                postTime = baseNodeEle.find_elements(By.CLASS_NAME, "fun")[0].find_elements(
                    By.CLASS_NAME, "from")[0].get_attribute("innerText")
                rawComment = baseNodeEle.find_elements(By.CLASS_NAME, "txt")[0].get_attribute("innerHTML")[1:].strip()
                comment = re.sub('<a.*</a>', "", rawComment)
                comment = Utility.MakeContentReadable(comment)

                excelSerializer.WriteLine([contentType, likeCount, userID, userName, postTime, comment])

        excelSerializer.Save(self.currFolderPath, fileName)
        excelSerializer.Close()

    def CrawlOnDetailedPage(self, url: str, fileName: str) -> None:
        Utility.PrintLog("Crawling on detailed page. Redirecting...")
        self.browser.get(url)

        excelSerializer = ExcelSerializer()

        mainContent = self.browser.find_elements(By.CLASS_NAME, "detail_wbtext_4CRf9")[0].get_attribute("innerText")
        mainContent = Utility.MakeContentReadable(mainContent)

        excelSerializer.WriteMainContent(mainContent)

        unavailableXPath = "/html/body/div/div[1]/div[2]/div[2]/main/div[1]/div/div[2]/div[2]/div[3]/div[2]"
        if len(self.browser.find_elements(By.XPATH, unavailableXPath)):
            Utility.PrintLog("The comments on this page are unavailable. Skipping...")

            excelSerializer.WriteMainContent(["", "", "", "", "", "Comments are unavailable."])
            excelSerializer.Save(self.currFolderPath, fileName)
            excelSerializer.Close()
            
            self.browser.back()
            return
        
        hashSet = set()
        comeToEnd = False
        fetchedAgain = False
        btnClicked = False

        while not (comeToEnd and fetchedAgain):
            if comeToEnd:
                fetchedAgain = True
            
            self.WaitElementLoadFinish(By.CLASS_NAME, "wbpro-list")
            renderedContents = self.browser.find_elements(By.CLASS_NAME, "wbpro-list")

            for index in range(len(renderedContents)):
                rawContentEle = None
                userID = None
                postTime = None
                try:
                    rawContentEle = renderedContents[index]
                    userID = rawContentEle.find_elements(By.TAG_NAME, "a")[1].get_attribute("href")[20:]
                    postTime = rawContentEle.find_elements(By.CLASS_NAME, "info")[0].find_elements(By.TAG_NAME, "div")[0].get_attribute(
                    "innerText")
                except:
                    Utility.PrintLog("Element not being attached error. Skipping...", Colors.default, True)
                    continue

                hash = userID + postTime
                if hash in hashSet:
                    Utility.PrintLog("Main comment already crawled. Skipping...", Colors.default, True)
                    continue
                hashSet.add(hash)

                moreButton = rawContentEle.find_elements(By.CLASS_NAME, "text")
                if len(moreButton) and len(moreButton[-1].find_elements(By.CLASS_NAME, "woo-font")):
                    # frame
                    # -----------------------------------------------------------------------
                    try:
                        moreButton[-1].find_elements(By.CLASS_NAME, "woo-font")[0].click()
                    except:
                        print("Wrong button would be clicked. Skipping...", Colors.default, True)
                        continue

                    Utility.PrintLog("Opening a frame for more info...", Colors.default, True)

                    if not btnClicked:
                        try:
                            self.browser.find_elements(By.CLASS_NAME, "ReplyModal_scroll3_2kADQ")[0].find_elements(
                                By.CLASS_NAME, "item")[0].click()
                            btnClicked = True
                        except:
                            btnClicked = True

                    # dump main comment in the frame first
                    # f stands for inside frame
                    # fc stands for inside frame comment
                    self.WaitElementLoadFinish(By.CLASS_NAME, "ReplyModal_scroll3_2kADQ")
                    fBaseNodeEle = self.browser.find_elements(By.CLASS_NAME, "ReplyModal_scroll3_2kADQ")[0].find_elements(
                        By.CLASS_NAME, "item1")[0]
                    base_wrapper = fBaseNodeEle.find_elements(By.CLASS_NAME, "item1in")[0].find_elements(
                    By.CLASS_NAME, "text")[0]
                    fcContentType = "c"
                    fcRawLikeCount = fBaseNodeEle.find_elements(By.CLASS_NAME, "item1in")[0].find_elements(
                        By.CLASS_NAME, "info")[0].find_elements(By.CLASS_NAME, "woo-like-count")
                    fcLikeCount = fcRawLikeCount[0].get_attribute("innerText") if len(fcRawLikeCount) else "0"
                    fcUserID = base_wrapper.find_elements(By.TAG_NAME, "a")[0].get_attribute("href")[20:]
                    fcUserName = base_wrapper.find_elements(By.TAG_NAME, "a")[0].get_attribute("innerText")
                    fcPostTime = fBaseNodeEle.find_elements(By.CLASS_NAME, "item1in")[0].find_elements(
                        By.CLASS_NAME, "info")[0].find_elements(By.TAG_NAME, "div")[0].get_attribute(
                        "innerText")
                    fcRawContent = base_wrapper.find_elements(By.TAG_NAME, "span")[-1].get_attribute(
                        "innerHTML")
                    fcContent = Utility.MakeContentReadable(fcRawContent)
                    
                    excelSerializer.WriteLine([fcContentType, fcLikeCount, fcUserID, fcUserName, fcPostTime, fcContent])

                    # dump the replies in the frame
                    fHashSet = set()
                    fComeToEnd = False
                    fFetchedAgain = False
                    while not (fComeToEnd and fFetchedAgain):                      
                        if (fComeToEnd):
                            fFetchedAgain = True

                        fRenderedContents = fBaseNodeEle.find_elements(By.CLASS_NAME, "vue-recycle-scroller__item-view")
                        for fIndex in range(len(fRenderedContents)):
                            fRawContentElement = fRenderedContents[fIndex]
                            fUserID = fRawContentElement.find_elements(By.TAG_NAME, "a")[0].get_attribute("href")[20:]
                            fPostTime = fRawContentElement.find_elements(By.CLASS_NAME, "info")[0].find_elements(
                                By.TAG_NAME, "div")[0].get_attribute("innerText")
                            
                            fHash = fUserID + fPostTime
                            if fHash in fHashSet:
                                Utility.PrintLog("Reply already crawled, skipping...", Colors.default, True)
                                continue
                            fHashSet.add(fHash)

                            fContentType = "r"
                            fRawLikeCount = fRawContentElement.find_elements(By.CLASS_NAME, "info")[0].find_elements(
                                By.CLASS_NAME, "woo-like-count")
                            fLikeCount = fRawLikeCount[0].get_attribute("innerText") if len(fRawLikeCount) else '0'
                            fUserName = fRawContentElement.find_elements(By.TAG_NAME, "a")[0].get_attribute("innerText")
                            fRawContent = fRawContentElement.find_elements(By.CLASS_NAME, "text")[0].find_elements(
                                By.TAG_NAME, "span")[-1].get_attribute("innerHTML")
                            fContent = Utility.MakeContentReadable(fRawContent)

                            excelSerializer.WriteLine([fContentType, fLikeCount, fUserID, fUserName, fPostTime, fContent])

                        fYAxis = self.browser.find_elements(By.CLASS_NAME, "ReplyModal_scroll3_2kADQ")[0].get_attribute(
                            'scrollTop')
                        self.browser.execute_script(
                            "document.getElementsByClassName('ReplyModal_scroll3_2kADQ')[0].scrollBy(0, 500)")
                        if fYAxis == self.browser.find_elements(By.CLASS_NAME, "ReplyModal_scroll3_2kADQ")[0].get_attribute(
                                'scrollTop'):
                            fComeToEnd = True

                    # don't forget to close this frame.
                    self.browser.find_elements(By.CLASS_NAME, "wbpro-layer")[0].find_elements(By.TAG_NAME, "i")[0].click()
                    
                    # end of frame
                    # -----------------------------------------------------------------------
                else:
                    contentType = "c-o"
                    rawLikeCount = rawContentEle.find_elements(By.CLASS_NAME, "item1in")[0].find_elements(
                            By.CLASS_NAME, "info")[0].find_elements(By.CLASS_NAME, "woo-like-count")
                    likeCount = rawLikeCount[0].get_attribute("innerText") if len(rawLikeCount) else '0'
                    userName = rawContentEle.find_elements(By.TAG_NAME, "a")[1].get_attribute("innerText")
                    rawContent = rawContentEle.find_elements(By.CLASS_NAME, "text")[0].find_elements(
                        By.TAG_NAME, "span")[-1].get_attribute("innerHTML")
                    content = Utility.MakeContentReadable(rawContent)

                    excelSerializer.WriteLine([contentType, likeCount, userID, userName, postTime, content])

            yAxis = self.browser.find_elements(By.TAG_NAME, "html")[0].get_attribute("scrollTop")
            self.browser.execute_script("window.scrollBy(0,500);")
            if yAxis == self.browser.find_elements(By.TAG_NAME, "html")[0].get_attribute("scrollTop"):
                comeToEnd = True

        excelSerializer.Save(self.currFolderPath, fileName)
        excelSerializer.Close()
        
        Utility.PrintLog("Current page is finished. Redirecting back...", Colors.default, True)
        self.browser.back()