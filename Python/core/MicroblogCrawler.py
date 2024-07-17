from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.microsoft import EdgeChromiumDriverManager
from core.Utility import *
from core.ExcelSerializer import *
from core.CookieManager import *
import PIL.Image
import urllib.parse
import urllib.request
import io
import json
import pyperclip

class MicrobolgCrawler:
    def __init__(self) -> None:
        self.Initialize()
        self.StartSession()

    def Initialize(self):
        self.currFolderPath = "ErrorFolder"
        self.parentFolder = "./crawled/"

        edgeOptions = webdriver.EdgeOptions()
        edgeOptions.use_chromium = True # is this necessary?
        edgeOptions.add_experimental_option("prefs", {"profile.managed_default_content_settings.images": 2}) # hide images
        edgeOptions.add_argument("--no-proxy-server") # disable proxy
        edgeOptions.add_experimental_option("useAutomationExtension", False) # disable automation alert
        edgeOptions.add_experimental_option("excludeSwitches", ["enable-logging", "enable-automation"]) #disable logging & alert
        
        url = input("Input a Microblog link: ")
        self.crawlMode = Utility.DetectCrawlMode(url)
        self.urlToBeCrawled = Utility.TrimUrl(url, self.crawlMode)

        webDriverPath = EdgeChromiumDriverManager(path="driver/").install()
        self.browser = webdriver.Edge(webDriverPath, options=edgeOptions)

    def StartSession(self) -> None:
        self.browser.get("https://weibo.com/login.php")
        childFolder = Utility.UnquoteDirectoryFromUrl(self.urlToBeCrawled, self.crawlMode)
        self.currFolderPath = os.path.join(self.parentFolder, childFolder)
        Utility.CreateFolder(self.currFolderPath)

        self.Login()

        self.Crawl()

    def WaitElementLoadFinish(self, method: str, key: str, timeout : float = 60, errMsg: str = "") -> bool:
        try:
            driverWait = WebDriverWait(self.browser, timeout)
            driverWait.until(EC.presence_of_element_located((method, key)))
            Utility.SleepFor(Constant.TimeSpan.normal)
            return False
        except TimeoutException:
            if len(errMsg) != 0:
                Utility.PrintLog(errMsg, Constant.Color.red)
            return True

    def Login(self) -> None:
            cookieManager = CookieManager()
            cookies = cookieManager.ReadCookies(self.crawlMode)
            if False and len(cookies) != 0:
                self.browser.delete_all_cookies()
                for cookie in cookies:
                    self.browser.add_cookie(cookie)
                self.browser.refresh()
                Utility.PrintLog("Login succeeded by using cookies! Redirecting...", Constant.Color.green)
            else:
                mainHandle = self.browser.current_window_handle
                
                loginBtnPath = r"/html/body/div/div[2]/div[1]/div[1]/div[2]/div/button"
                self.WaitElementLoadFinish(By.XPATH, loginBtnPath)
                self.browser.find_element(By.XPATH, loginBtnPath).click()
                
                handles = self.browser.window_handles
                if len(handles) <= 1:
                    log = "Could not find the login window!"
                    Utility.PrintLog(log, Constant.Color.red)
                    Utility.ExitProgram()
                else:
                    log = "Found {} popup window handle(s).".format(len(handles) - 1)
                    Utility.PrintLog(log, Constant.Color.green)

                for index in range(len(handles)):
                    handle = handles[index]
                    if handle == mainHandle:
                        continue

                    self.browser.switch_to.window(handle)
                    if not self.browser.current_url.startswith("https://passport.weibo.com/sso/"):
                        Utility.PrintLog("Skipping the unexpected popup window...", Constant.Color.green)
                        continue
                    else:
                        Utility.PrintLog("Switching to pupup window No. {}...".format(index), Constant.Color.green)

                    qrCodeImage = None
                    try:
                        qrCodeEleXpath = "/html/body/div/div/div/div[2]/div[1]/div[2]/div/img"
                        self.WaitElementLoadFinish(By.XPATH, qrCodeEleXpath, 10, "Timed out while getting QR code!")
                        qrCodeEle = self.browser.find_element(By.XPATH, qrCodeEleXpath)
                        qrCodeUrl = qrCodeEle.get_attribute("src")
                        response = urllib.request.urlopen(qrCodeUrl)
                        qrCodeImage = PIL.Image.open(io.BytesIO(response.read()))
                        qrCodeImage.show()
                        break
                    except:
                        if index == len(handles) - 1:
                            errMsg = "Error occurred while getting QR code. Please restart the program!"
                            Utility.PrintLog(errMsg, Constant.Color.red)
                            Utility.ExitProgram()
                        else:
                            continue

                Utility.PrintLog("Switching back...", Constant.Color.green)
                self.browser.switch_to.window(mainHandle)

                self.WaitElementLoadFinish(By.CLASS_NAME, "woo-badge-box")
                Utility.PrintLog("Login succeeded! Redirecting...", Constant.Color.green)
                # qrCodeImage.close()

                # cookieManager.SaveCookies(self.browser.get_cookies())

    def Crawl(self) -> None:
        if self.crawlMode == Constant.CrawlMode.singleItem:
            formatedTime = time.strftime("%Y%m%d%H%M%S", time.localtime())
            self.CrawlOnDetailedPage(self.urlToBeCrawled, formatedTime)
        elif self.crawlMode == Constant.CrawlMode.multiItem:
            self.browser.get(self.urlToBeCrawled)
            Utility.PrintLog("Redirecting to the page to be crawled...")

            pageCount = self.GetPageCount()
            Utility.PrintLog("Found {} page(s).".format(pageCount))
            for pageNumber in range(1, pageCount + 1):
                for itemNumber in range(1, Constant.itemsPerPage + 1):
                    Utility.PrintLog("Crawling page {}, item {}.".format(pageNumber, itemNumber), Constant.Color.green)

                    Utility.SleepFor(Constant.TimeSpan.normal)

                    # click the comment button if there is one
                    commentBtnXPath = "/html/body/div[1]/div[2]/div/div[2]/div[1]/div[3]/div[{}]/div/div[2]/ul/li[2]/a".format(itemNumber)
                    commentButton = self.browser.find_elements(By.XPATH, commentBtnXPath)
                    if len(commentButton) == 0:
                        Utility.PrintLog("There is no more blogs! Cleaning up...", Constant.Color.red)
                        continue
                    else:
                        try:
                            commentButton[0].click()
                        except:
                            Utility.PrintLog("Wrong button would be clicked. Skipping...", Constant.Color.default, True)
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

                if pageNumber < pageCount - 1:
                    # click next page button
                    nextPageBtn = self.browser.find_elements(By.CLASS_NAME, "m-page")[0].find_element(
                        By.CLASS_NAME, "next")
                    self.browser.execute_script("window.scrollTo(0,document.body.scrollHeight);", nextPageBtn)
                    nextPageBtn.click()
                    Utility.SleepFor(Constant.TimeSpan.long)

        Utility.PrintLog("Program finished. Hit Enter key to exit.", Constant.Color.blue)
        input()
        self.browser.close()
        exit()

    def GetPageCount(self) -> int:
        try:
            Utility.SleepFor(2)
            pages = self.browser.find_element(By.CLASS_NAME, "s-scroll").find_elements(By.TAG_NAME, "li")
            return 1 if (len(pages)) == 0 else len(pages)
        except:
            return 1
        
    def GetUserGenderByID(self, userID: str) -> str:
        return "Unknown"
        if userID in GlobalVariables.id2GenderDict:
            return GlobalVariables.id2GenderDict[userID]

        GlobalVariables.id2GenderDict[userID] = "Unknown"
        api = "https://weibo.com/ajax/profile/info?uid=" + userID
        try:
            self.browser.execute_script("window.open('" + api + "', '_blank');")
            self.browser.switch_to.window(self.browser.window_handles[1])
            # it may take longer to call this api for the first time
            # then normally it would not take more than 300ms per identical user
            userInfoXPath = "/html/body"
            self.WaitElementLoadFinish(By.XPATH, userInfoXPath, Constant.TimeSpan.timeout)
            rawUserInfoEle = self.browser.find_elements(By.XPATH, userInfoXPath)
            if len(rawUserInfoEle) > 0:
                rawUserInfo = rawUserInfoEle[0].find_elements(By.XPATH, "./*[1]")[0].get_attribute("innerText")
                userInfoJson = json.loads(rawUserInfo)
                genderDesc = userInfoJson.get("data", {}).get("user", {}).get("gender", "Unknown")
                if genderDesc == "m":
                    GlobalVariables.id2GenderDict[userID] = "Male"
                elif genderDesc == "f":
                    GlobalVariables.id2GenderDict[userID] = "Female"
            else:
                GlobalVariables.id2GenderDict[userID] = "Unknown"
        except:
            Utility.PrintLog("Get user gender timed out! Skipping...", Constant.Color.yellow)
        finally:
            self.browser.close()
            self.browser.switch_to.window(self.browser.window_handles[0])
            
        return GlobalVariables.id2GenderDict[userID]


    def CrawlOnCurrentPage(self, itemIndex: int, fileName: str) -> None:
        Utility.PrintLog("Crawling on current page...")

        excelSerializer = ExcelSerializer()

        mainContent = self.browser.find_elements(By.CLASS_NAME, "txt")[itemIndex].get_attribute("innerText")
        mainContent = Utility.MakeContentReadable(mainContent)

        # call anonymous JavaScript function to copy the real url 
        self.browser.find_elements(By.CSS_SELECTOR, ".menu.s-fr")[itemIndex].find_elements(
            By.TAG_NAME, "li")[3].find_elements(By.TAG_NAME, "a")[0].click()
        microblogUrl = pyperclip.paste()

        excelSerializer.WriteMainContent(mainContent, microblogUrl)

        comments = None
        exception = False
        try:
            comments = self.browser.find_elements(By.CLASS_NAME, "card-wrap")[itemIndex].find_elements(
                By.CLASS_NAME, "list")[0].find_elements(By.CLASS_NAME, "card-review")
        except:
            exception = True

        if exception or len(comments) == 0:
            excelSerializer.WriteLine(["", "", "", "", "", "", "No one commented on this blog."])
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
                userID = re.search('/u/(\d+)', rawUserID).group(1)
                userName = baseNodeEle.find_elements(By.CLASS_NAME, "txt")[0].find_elements(
                    By.TAG_NAME, "a")[0].get_attribute("innerText")
                userGender = self.GetUserGenderByID(userID)
                mixedTimeIP = baseNodeEle.find_elements(By.CLASS_NAME, "fun")[0].find_elements(
                    By.CLASS_NAME, "from")[0].get_attribute("innerText")
                seperatedTimeIP = Utility.SeperateTimeAndIPAddress(mixedTimeIP)
                postTime = seperatedTimeIP[0]
                ipAddress = seperatedTimeIP[1]
                rawComment = baseNodeEle.find_elements(By.CLASS_NAME, "txt")[0].get_attribute("innerHTML")[1:].strip()
                comment = Utility.MakeContentReadable(rawComment)
                
                excelSerializer.WriteLine([contentType, likeCount, userID, userName, userGender, postTime, ipAddress, comment])

        excelSerializer.Save(self.currFolderPath, fileName)
        excelSerializer.Close()

    def CrawlOnDetailedPage(self, url: str, fileName: str) -> None:
        Utility.PrintLog("Crawling on detailed page. Redirecting...")
        self.browser.get(url)

        excelSerializer = ExcelSerializer()

        mainContent = self.browser.find_elements(By.CLASS_NAME, "detail_wbtext_4CRf9")[0].get_attribute("innerText")
        mainContent = Utility.MakeContentReadable(mainContent)

        excelSerializer.WriteMainContent(mainContent, url)

        unavailableXPath = "/html/body/div/div[1]/div[2]/div[2]/main/div[1]/div/div[2]/div[2]/div[3]/div[2]"
        if len(self.browser.find_elements(By.XPATH, unavailableXPath)):
            Utility.PrintLog("The comments on this page are unavailable. Skipping...")

            excelSerializer.WriteLine(["", "", "", "", "", "", "Comments are unavailable."])
            excelSerializer.Save(self.currFolderPath, fileName)
            excelSerializer.Close()
            
            self.browser.back()
            return
        
        hashSet = set()
        fetchTimes = 1
        btnClicked = False
        while fetchTimes <= Constant.fetchTimeLimit:
            self.WaitElementLoadFinish(By.CLASS_NAME, "wbpro-list")
            renderedContents = self.browser.find_elements(By.CLASS_NAME, "wbpro-list")

            for index in range(len(renderedContents)):
                rawContentEle = None
                userID = None
                postTime = None
                try:
                    rawContentEle = renderedContents[index]
                    rawUserID = rawContentEle.find_elements(By.TAG_NAME, "a")[1].get_attribute("href")
                    userID = re.search('/u/(\d+)', rawUserID).group(1)
                    mixedTimeIP = rawContentEle.find_elements(By.CLASS_NAME, "info")[0].find_elements(By.TAG_NAME, "div")[0].get_attribute(
                    "innerText")
                    seperatedTimeIP = Utility.SeperateTimeAndIPAddress(mixedTimeIP)
                    postTime = seperatedTimeIP[0]
                    ipAddress = seperatedTimeIP[1]

                except:
                    Utility.PrintLog("Element not being attached error. Skipping...", Constant.Color.default, True)
                    continue

                hash = userID + postTime
                if hash in hashSet:
                    Utility.PrintLog("Main comment already crawled. Skipping...", Constant.Color.default, True)
                    continue
                hashSet.add(hash)

                moreButton = rawContentEle.find_elements(By.CLASS_NAME, "text")
                if len(moreButton) and len(moreButton[-1].find_elements(By.CLASS_NAME, "woo-font")):
                    # frame
                    # -----------------------------------------------------------------------
                    try:
                        moreButton[-1].find_elements(By.CLASS_NAME, "woo-font")[0].click()
                    except:
                        Utility.PrintLog("Wrong button would be clicked. Skipping...", Constant.Color.default, True)
                        continue

                    Utility.PrintLog("Opening a frame for more info...", Constant.Color.default, True)

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
                    rawFcUserID = base_wrapper.find_elements(By.TAG_NAME, "a")[0].get_attribute("href")
                    fcUserID = re.search('/u/(\d+)', rawFcUserID).group(1)
                    fcUserName = base_wrapper.find_elements(By.TAG_NAME, "a")[0].get_attribute("innerText").lstrip()
                    fcUserGender = self.GetUserGenderByID(fcUserID)
                    fcMixedTimeIP = fBaseNodeEle.find_elements(By.CLASS_NAME, "item1in")[0].find_elements(
                        By.CLASS_NAME, "info")[0].find_elements(By.TAG_NAME, "div")[0].get_attribute(
                        "innerText")
                    fcSeperatedTimeIP = Utility.SeperateTimeAndIPAddress(fcMixedTimeIP)
                    fcPostTime = fcSeperatedTimeIP[0]
                    fcIPAddress = fcSeperatedTimeIP[1]
                    fcRawContent = base_wrapper.find_elements(By.TAG_NAME, "span")[-1].get_attribute(
                        "innerHTML")
                    fcContent = Utility.MakeContentReadable(fcRawContent)
                    
                    excelSerializer.WriteLine([fcContentType, fcLikeCount, fcUserID, fcUserName, fcUserGender, fcPostTime, fcIPAddress, fcContent])

                    # dump the replies in the frame
                    fHashSet = set()
                    fFetchTimes = 1
                    while fFetchTimes <= Constant.fetchTimeLimit:                      
                        fRenderedContents = fBaseNodeEle.find_elements(By.CLASS_NAME, "vue-recycle-scroller__item-view")
                        for fIndex in range(len(fRenderedContents)):
                            fRawContentElement = fRenderedContents[fIndex]
                            rawFUserID = fRawContentElement.find_elements(By.TAG_NAME, "a")[0].get_attribute("href")
                            fUserID = re.search('/u/(\d+)', rawFUserID).group(1)
                            fMixedTimeIP = fRawContentElement.find_elements(By.CLASS_NAME, "info")[0].find_elements(
                                By.TAG_NAME, "div")[0].get_attribute("innerText")
                            fSeperatedTimeIP = Utility.SeperateTimeAndIPAddress(fMixedTimeIP)
                            fPostTime = fSeperatedTimeIP[0]
                            fIPAddress = fSeperatedTimeIP[1]
                            
                            fHash = fUserID + fPostTime
                            if fHash in fHashSet:
                                Utility.PrintLog("Reply already crawled, skipping...", Constant.Color.default, True)
                                continue
                            fHashSet.add(fHash)

                            fContentType = "r"
                            fRawLikeCount = fRawContentElement.find_elements(By.CLASS_NAME, "info")[0].find_elements(
                                By.CLASS_NAME, "woo-like-count")
                            fLikeCount = fRawLikeCount[0].get_attribute("innerText") if len(fRawLikeCount) else '0'
                            fUserName = fRawContentElement.find_elements(By.TAG_NAME, "a")[0].get_attribute("innerText")
                            fUserGender = self.GetUserGenderByID(fUserID)
                            fRawContent = fRawContentElement.find_elements(By.CLASS_NAME, "text")[0].find_elements(
                                By.TAG_NAME, "span")[-1].get_attribute("innerHTML")
                            fContent = Utility.MakeContentReadable(fRawContent)

                            excelSerializer.WriteLine([fContentType, fLikeCount, fUserID, fUserName, fUserGender, fPostTime, fIPAddress, fContent])

                        fYAxis = self.browser.find_elements(By.CLASS_NAME, "ReplyModal_scroll3_2kADQ")[0].get_attribute(
                            'scrollTop')
                        self.browser.execute_script(
                            "document.getElementsByClassName('ReplyModal_scroll3_2kADQ')[0].scrollBy(0, 250)")
                        Utility.SleepFor(Constant.TimeSpan.normal)
                        if fYAxis == self.browser.find_elements(By.CLASS_NAME, "ReplyModal_scroll3_2kADQ")[0].get_attribute(
                                'scrollTop'):
                            fFetchTimes += 1
                        else:
                            fFetchTimes = 1

                    # don't forget to close this frame.
                    self.browser.find_elements(By.CLASS_NAME, "wbpro-layer")[0].find_elements(By.TAG_NAME, "i")[0].click()
                    
                    # end of frame
                    # -----------------------------------------------------------------------
                else:
                    # main comment exsist definitely
                    rawLikeCount = rawContentEle.find_elements(By.CLASS_NAME, "item1in")[0].find_elements(
                            By.CLASS_NAME, "info")[0].find_elements(By.CLASS_NAME, "woo-like-count")
                    likeCount = rawLikeCount[0].get_attribute("innerText") if len(rawLikeCount) else '0'
                    userName = rawContentEle.find_elements(By.TAG_NAME, "a")[1].get_attribute("innerText")
                    userGender = self.GetUserGenderByID(userID)
                    rawContent = rawContentEle.find_elements(By.CLASS_NAME, "text")[0].find_elements(
                        By.TAG_NAME, "span")[-1].get_attribute("innerHTML")
                    content = Utility.MakeContentReadable(rawContent)

                    # attached reply may not exsit
                    outsideFrameReplyEles = rawContentEle.find_elements(By.CLASS_NAME, "list2")[0].find_elements(
                        By.CLASS_NAME, "item2")
                    contentType = "c-o" if len(outsideFrameReplyEles) == 0 else "c"

                    excelSerializer.WriteLine([contentType, likeCount, userID, userName, userGender, postTime, ipAddress, content])

                    # attached reply(replies) outside frame
                    for ofIndex in range(len(outsideFrameReplyEles)):
                        outsideFrameReplyEle = outsideFrameReplyEles[ofIndex]
                        ofRawReplyElement = outsideFrameReplyEle.find_elements(By.CLASS_NAME, "con2")[0]
                        rawOfUserID = ofRawReplyElement.find_elements(By.TAG_NAME, "a")[0].get_attribute("href")
                        ofUserID = re.search('/u/(\d+)', rawOfUserID).group(1)
                        ofMixedTimeIP = ofRawReplyElement.find_elements(By.CLASS_NAME, "info")[0].find_elements(
                            By.TAG_NAME, "div")[0].get_attribute("innerText")
                        ofSeperatedTimeIP = Utility.SeperateTimeAndIPAddress(ofMixedTimeIP)
                        ofPostTime = ofSeperatedTimeIP[0]
                        ofIPAddress = ofSeperatedTimeIP[1]

                        ofContentType = "r"
                        ofRawLikeCount = ofRawReplyElement.find_elements(By.CLASS_NAME, "info")[0].find_elements(
                            By.CLASS_NAME, "woo-like-count")
                        ofLikeCount = ofRawLikeCount[0].get_attribute("innerText") if len(ofRawLikeCount) else '0'
                        ofUserName = ofRawReplyElement.find_elements(By.TAG_NAME, "a")[0].get_attribute("innerText")
                        ofUserGender = self.GetUserGenderByID(ofUserID)
                        ofRawContent = ofRawReplyElement.find_elements(By.CLASS_NAME, "text")[0].find_elements(
                            By.TAG_NAME, "span")[-1].get_attribute("innerHTML")
                        ofContent = Utility.MakeContentReadable(ofRawContent)

                        excelSerializer.WriteLine([ofContentType, ofLikeCount, ofUserID, ofUserName, ofUserGender, ofPostTime, ofIPAddress, ofContent])

            yAxis = self.browser.find_elements(By.TAG_NAME, "html")[0].get_attribute("scrollTop")
            self.browser.execute_script("window.scrollBy(0, 250);")
            Utility.SleepFor(Constant.TimeSpan.normal)
            if yAxis == self.browser.find_elements(By.TAG_NAME, "html")[0].get_attribute("scrollTop"):
                fetchTimes += 1
            else:
                fetchTimes = 1

        excelSerializer.Save(self.currFolderPath, fileName)
        excelSerializer.Close()
        
        Utility.PrintLog("Current page is finished. Redirecting back...\n", Constant.Color.default, True)
        self.browser.back()