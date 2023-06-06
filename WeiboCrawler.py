from selenium import webdriver
from selenium.webdriver.common.by import By
from webdriver_manager.microsoft import EdgeChromiumDriverManager
import webbrowser
import urllib.parse
import time
import re
import os


class CreeperExplode:
    def __init__(self) -> None:
        self.driverChoice = "driver/msedgedriver.exe"

        self.currentDirName = "faultDir"
        self.currentFolderLocation = "crawled/"
        self.CheckFolderExistence()

        self.noPicMode = True

        # 1. 单页模式 2. 多页模式
        self.crawMode = 1

        self.targetUrlList = list()

        self.InputUrls()

        Edge_options = webdriver.EdgeOptions()
        if self.noPicMode:
            Edge_options.use_chromium = True
            No_Image_loading = {"profile.managed_default_content_settings.images": 2}
            Edge_options.add_experimental_option("prefs", No_Image_loading)

        driver = EdgeChromiumDriverManager(path="driver/").install()
        self.browser = webdriver.Edge(driver, options=Edge_options)

        self.StartSession()

    def CheckFolderExistence(self) -> None:
        if self.currentFolderLocation[0:-1] not in os.listdir() or not os.path.isdir(os.path.abspath(self.currentFolderLocation)):
            os.mkdir(self.currentFolderLocation)

    def InputUrls(self):
        # while 1:
        #     currUrlInput = input("Please input the correct url (double Enter to confirm): ")
        #     if currUrlInput == "": break
        #     self.targetUrlList.append(currUrlInput)
        currUrlInput = input("请输入微博网址: ")

        if currUrlInput.find("%23") == -1 and not currUrlInput.endswith("#comment"):
            currUrlInput += "#comment"

        self.CheckCrawlMode(currUrlInput)

        if self.crawMode == 2 and currUrlInput.find("&xsort=hot") == -1:
            currUrlInput = "https://s.weibo.com/hot?q=" + currUrlInput[28:] + "&xsort=hot&suball=1&tw=hotweibo&Refer=hot_hot"
        
        self.targetUrlList.append(currUrlInput)

    def CheckCrawlMode(self, url: str):
        if url.endswith("#comment"):
            self.crawMode = 1
        else:
            self.crawMode = 2

        print("\033[0;35;40m" + ("Craw Mode: " + "Single-Page Mode" if self.crawMode == 1 else "Multi-Page Mode") + "\033[0m")

    @staticmethod
    def SleepFor(sec) -> None:
        """
        :param sec: second(s) to be waited
        :return: None
        """
        time.sleep(sec)

    @staticmethod
    def SerializeEmojy(reply: str) -> str:
        """
        Special cases:
        replace 笑cry with 笑哭
        replace 打call with 打电话
        replace good with 挺好
        replace ok with 棒
        replace doge with 狗头

        Replace <a href="/n/xxx">xxx</a>-> xxx,
        and replace emojy into raw character:
        <img xxx> -> [xxx]
        :param reply:
        :return:
        """
        reply = re.sub('笑cry', '笑哭', reply)
        reply = re.sub('\[打call\]', '[打电话]', reply)
        reply = re.sub('\[good\]', '[挺好]', reply)
        reply = re.sub('\[ok\]', '[棒]', reply)
        reply = re.sub('\[doge\]', '[狗头]', reply)
        reply = re.sub('<a(.*)">@', " @", reply)
        reply = re.sub('</a>:', " ", reply)
        b = re.findall('alt="\[([\u4e00-\u9fa5]*)\]', reply)
        for i in range(len(b)):
            reply = re.subn('<img(.*?)>', "[" + b[i] + "]", reply, 1)[0]
        return reply

    def WaitUntilLoaded(self) -> None:
        """
        Program hangs until page is loaded
        :return: None
        """
        while 1:
            if self.browser.find_elements(By.CLASS_NAME, 'S_txt1'):
                a = self.browser.find_elements(By.CLASS_NAME, 'S_txt1')
                try:
                    a[9].click()
                except:
                    self.SleepFor(2)
                    continue

                while 1:
                    try:
                        # Click the login button.
                        # The QR code on the screen shall be scanned
                        self.browser.find_elements(By.CLASS_NAME, "tab_bar")[0].find_elements(By.TAG_NAME, "a")[1].click()

                        self.SleepFor(2)
                        QRCodeXpath = "/html/body/div[4]/div[2]/div[3]/div[2]/div[1]/img"
                        item = self.browser.find_elements(By.XPATH, QRCodeXpath)
                        QRCodeUrl = item[0].get_attribute("src")
                        self.QRCodeBrowser = webbrowser.open_new(QRCodeUrl)
                        break
                    except:
                        self.SleepFor(2)
                        continue
                while 1:
                    if self.browser.find_elements(By.CLASS_NAME, 'woo-badge-box'):
                        print("Page loaded successfully! Waiting for navigation...")
                        break
                    else:
                        self.SleepFor(1)
                break
            else:  # Query frequency(sec)
                self.SleepFor(1)

    def StartSession(self) -> None:
        """
        Start one session
        :return: None
        """
        self.browser.delete_all_cookies()
        self.browser.get("https://weibo.com/login.php")
        self.WaitUntilLoaded()

        for url in self.targetUrlList:
            self.CreateDir(url)
            self.browser.get(url)
            print("Navigating into detail pages...")
            self.SaveUrl(url)
            try:
                if self.crawMode == 1:
                    self.StartCrawlSingleItem()
                elif self.crawMode == 2:
                    self.StartCrawlMultiItems()
            except:
                continue

        print("\033[0;31;40m" + "Program finished. " + "Hit any key to exit." + "\033[0m")
        input()
        self.browser.close()

    def CreateDir(self, url) -> None:
        if self.crawMode == 1:
            try:
                self.currentDirName = url[url.rfind("/") + 1 : url.rfind("#")]
            except:
                pass

        elif self.crawMode == 2:
            try:
                self.currentDirName = urllib.parse.unquote(url[26:-47])
            except:
                pass
        
        try:
            os.mkdir("crawled/" + self.currentDirName)
        except:
            pass
        finally:
            self.currentFolderLocation = "crawled/" + self.currentDirName + "/"

    def SaveUrl(self, url) -> None:
        with open(self.currentFolderLocation + "/网址.txt", "w", encoding="utf-8") as urlFileObject:
            urlFileObject.write(url)

    def StartCrawlSingleItem(self) -> None:
        self.browser.get(self.targetUrlList[0])
        self.DumpOnDetailedPage(self.currentDirName)

    def StartCrawlMultiItems(self) -> None:
        """
        Start looping: navigate to detail page,
        and get every detail of comments
        :return: None
        """
        current_page = 1
        for page in range(1, 2):
            # Check if it's the right page.
            if current_page != page:
                for t in range(page - current_page):
                    next_page = self.browser.find_elements(By.CLASS_NAME, "m-page")[0].find_elements(
                        By.CLASS_NAME, "next")
                    self.browser.execute_script("window.scrollTo(0,document.body.scrollHeight);", next_page)
                    next_page[0].click()
                    current_page += 1
                    self.SleepFor(2)

            for i in range(1, 11):
                self.SleepFor(2)
                print("Current on page {}, item {}, loading...".format(page, i))
                XpathMore = "/html/body/div[1]/div[2]/div/div[2]/div[1]/div[3]/div[{}]/div/div[2]/ul/li[2]/a".format(i)
                XpathLink = "/html/body/div[1]/div[2]/div/div[2]/div[1]/div[3]/div[{}]/div/div[3]/div/div[3]/a".format(i)

                a = self.browser.find_elements(By.XPATH, XpathMore)
                try:
                    a[0].click()
                except:
                    print("There is no more page! skipping...")
                    continue
                self.SleepFor(2)

                # Navigate to comment detail page if there is a button:
                b = self.browser.find_elements(By.XPATH, XpathLink)
                if len(b):
                    print("Redirecting to detail page...")
                    self.browser.get(b[0].get_attribute("href"))

                    print("Dumping on detailed page...")
                    self.DumpOnDetailedPage("page" + str(page) + "-item" + str(i))
                else:
                    print("Dumping on current page...")
                    self.DumpOnCurrentPage(i - 1, "page" + str(page) + "-item" + str(i))

            # Next page
            next_page = self.browser.find_elements(By.CLASS_NAME, "m-page")[0].find_elements(
                By.CLASS_NAME, "next")
            self.browser.execute_script("window.scrollTo(0,document.body.scrollHeight);", next_page)
            next_page[0].click()
            current_page += 1
            self.SleepFor(2)

    def DumpOnCurrentPage(self, i: int, file_name: str) -> None:
        """
        Dump function for fewer comments drawn on
        current page only.
        :param i: current tag count
        :param file_name: current page : current comment
        :return: return if there is no comment at all
        """
        # Open a file to get ready for dumping
        CurrentFileObj = open(self.currentFolderLocation + file_name + ".txt", 'w', encoding="utf-8")

        self.SleepFor(2)

        wbc = self.browser.find_elements(By.CLASS_NAME, "txt")[i].get_attribute("innerText").replace("\n", "").replace(
            " ", "")
        wbc = self.SerializeEmojy(wbc)
        CurrentFileObj.write("wbc " + wbc + "\n\n")

        try:
            comments_list = self.browser.find_elements(By.CLASS_NAME, "card-wrap")[i].find_elements(
                By.CLASS_NAME, "list")[0].find_elements(By.CLASS_NAME, "card-review")
        except:
            CurrentFileObj.write("There was no comment.")
            CurrentFileObj.close()
            return

        if not len(comments_list):
            CurrentFileObj.write("There was no comment.")
            CurrentFileObj.close()
            return
        else:
            for n in range(len(comments_list)):
                base_node = comments_list[n].find_elements(By.CLASS_NAME, "content")[0]
                # raw_wbid be like: //weibo.com/u/xxx?refer...
                # What we need is only the xxx between u/ and ?refer.
                raw_wbid = base_node.find_elements(By.CLASS_NAME, "txt")[0].find_elements(
                    By.TAG_NAME, "a")[0].get_attribute("href")
                wbid = re.findall('/u/[0-9]*\?', raw_wbid)[0][3:-1]
                wbname = base_node.find_elements(By.CLASS_NAME, "txt")[0].find_elements(
                    By.TAG_NAME, "a")[0].get_attribute("innerText")
                content_raw = base_node.find_elements(By.CLASS_NAME, "txt")[0].get_attribute("innerHTML")[1:].strip()
                content_raw = re.sub('<a.*</a>', "", content_raw)
                content = self.SerializeEmojy(content_raw).replace("\n", "").replace(" ", "")[1:]
                time = base_node.find_elements(By.CLASS_NAME, "fun")[0].find_elements(
                    By.CLASS_NAME, "from")[0].get_attribute("innerText")
                likes_raw = base_node.find_elements(By.CLASS_NAME, "fun")[0].find_elements(
                    By.TAG_NAME, "li")[-1].find_elements(By.TAG_NAME, "span")[0].get_attribute("innerText")
                likes = likes_raw if len(likes_raw) else '0'
                # print("m-o likes:", likes, wbid, wbname, time, content)
                line = " ".join(["m-o likes:", likes, wbid, wbname, time, content + "\n"])
                CurrentFileObj.write(line)

            # Close file object
            CurrentFileObj.close()

    def DumpOnDetailedPage(self, file_name: str) -> None:
        """
        Start dumping every detailed comment
        :param file_name: current page : current comment
        :return return if the comments are unavailable
        """
        self.SleepFor(2)

        # Open a file to get ready for dumping
        CurrentFileObj = open(self.currentFolderLocation + file_name + ".txt", 'w', encoding="utf-8")

        wbc = self.browser.find_elements(By.CLASS_NAME, "detail_wbtext_4CRf9")[0].get_attribute(
            "innerText").replace("\n", "").replace(" ", "")
        wbc = self.SerializeEmojy(wbc)
        CurrentFileObj.write("wbc " + wbc + "\n\n")

        wbid_ = self.browser.find_elements(By.CLASS_NAME, "ALink_default_2ibt1")[0].get_attribute(
            "href").rsplit("/", 1)[-1]
        if wbid_ == "1812339720":
            CurrentFileObj.write("Blacklist user: LUSON妈-.")
            CurrentFileObj.close()
            self.browser.back()
            return

        unavailable = "/html/body/div/div[1]/div[2]/div[2]/main/div[1]/div/div[2]/div[2]/div[3]/div[2]"
        if len(self.browser.find_elements(By.XPATH, unavailable)):
            print("The comments on this page are unavailable, skipping...")
            CurrentFileObj.write("Comments are unavailable.")
            CurrentFileObj.close()
            self.browser.back()
            return

        # Click the order by likes button: NOW IT'S NOT NEEDED
        # self.SleepFor(2)
        # likes = "/html/body/div/div[1]/div[2]/div[2]/main/div/div/div[2]/div[2]/div[3]/div/div[1]/div/div[1]"

        # The program is using a more smart scroll function for now than
        # the method below:
        # self.browser.find_elements(By.XPATH, likes)[0].click()
        # self.SleepFor(2)
        # ele = self.browser.find_elements(By.CLASS_NAME, "Bottom_text_1kFLe")
        # self.browser.execute_script("window.scrollTo(0,document.body.scrollHeight);", ele)

        # There might be something tricky here:
        # Weibo.com is using a recycle scroller list to limit the
        # comments drawn on the screen.
        # Uncertain amount(btw. 0 & 20) of comments will be drawn
        # in random order.
        # The program shall be able to check if the comments has been
        # already dumped once.

        # One solution of the problem mentioned upper is:
        # Scroll window by 200px every step, and then
        # get the rendered comments list.
        # Loop every comment in the list, and check if
        # the main reply has been dumped.
        # By how can we identify if a comment has been
        # already dumped? weibo id value & time.
        # Here I believe a deque with length of 20 shall
        # be enough for duplicate removal.

        # After running a test, I've found that deque has two
        # drawbacks: one is that it's duplicate check is not O(1);
        # another is that a length of 20 shall not be enough.
        # The builtin data structure set meets the requests we
        # wanted. O(1) with any length of data inside. Only
        # more space will be demanded instead of using a deque.
        self.SleepFor(2)
        # DumpedList = collections.deque(maxlen=20)
        DumpedList = set()
        ComeToEnd = False
        LastFetched = False

        # Rank by likes button is only needed to be clicked once
        Clicked = False
        while not (ComeToEnd and LastFetched):

            self.SleepFor(0.3)

            RenderedComments = self.browser.find_elements(By.CLASS_NAME, "wbpro-list")

            # Only if come to the end of the page and
            # loop again shall the program end the loop.
            if ComeToEnd:
                LastFetched = True

            for i in range(len(RenderedComments)):
                # Step 1: extract the poster's id & time
                # Current div tag
                try:
                    raw = RenderedComments[i]
                except:
                    self.SleepFor(2)
                    try:
                        raw = RenderedComments[i]
                    except:
                        print("Element not being attached error, skipping...")
                        continue
                # Raw wbid shall be like "https://weibo.com/u/0000000001",
                # but what we need is only the numbers: slice(20:).
                try:
                    wbid = raw.find_elements(By.TAG_NAME, "a")[1].get_attribute("href")[20:]
                except:
                    print("Element not being attached error, skipping...")
                    continue
                # Raw time shall be like " 9-7       13:29 <!---->",
                # but what we need is only the numbers: [:-7].replace("\n", " ").
                # THIS IS NOT NEEDED by using innerText rather than innerHTML.
                time = raw.find_elements(By.CLASS_NAME, "info")[0].find_elements(By.TAG_NAME, "div")[0].get_attribute(
                    "innerText")
                # Skip if existence
                key = wbid + time
                if key in DumpedList:
                    print("Main comment already dumped, skipping...")
                    continue
                # DumpedList.append(key)
                DumpedList.add(key)
                # print(DumpedList)

                # Using for duplicate sleeping removal.
                slept = False

                # Step 2: check if there is a more button
                # IF: the number of elements of <a> tag is 6,
                # then certainly there is a show_more button.
                more_button = raw.find_elements(By.CLASS_NAME, "text")
                if len(more_button) and len(more_button[-1].find_elements(By.CLASS_NAME, "woo-font")):
                    try:
                        more_button[-1].find_elements(By.CLASS_NAME, "woo-font")[0].click()
                    except:
                        print("Wrong button would be clicked, skipping...")
                        continue
                    print("Open new(next) frame for more info...")
                    # Till now, a frame shall be drawn on the screen to show
                    # one specific user's comments & replies.
                    # There shall be len(vue-recycle-scroller__item-view)
                    # different users' comments in total.
                    # Comments are automatically ranked chronologically.
                    # Order by likes button shall be clicked.
                    # By now the program is expected to differentiate the main
                    # comment and the replies, and dump them in a specific order.

                    # Order by likes
                    if not Clicked:
                        try:
                            self.SleepFor(1)
                            self.browser.find_elements(By.CLASS_NAME, "ReplyModal_scroll3_2kADQ")[0].find_elements(
                                By.CLASS_NAME, "item")[0].click()
                            Clicked = True
                        except:
                            Clicked = True

                    # There might be something tricky as mentioned above:
                    # Weibo.com is using a recycle scroller list here to
                    # limit the comments drawn on the screen, too.
                    # And with another frame came up, window scroll function
                    # will not be able to work.
                    # One solution is that the program click this frame to
                    # get focus, and then send DOWN KEYs to refresh new
                    # comments.

                    # Recently a new solution popped in my mind:
                    # JS can call a element's scroll event.
                    # So the program can easily call the frame's
                    # scrollBy event.

                    # Duplicate removal is needed here, too.
                    # Here I believe a deque with length of 20 shall be
                    # enough.

                    # After running a test, I've found that deque has two
                    # drawbacks: one is that it's duplicate check is not O(1);
                    # another is that a length of 20 shall not be enough.
                    # The builtin data structure set meets the requests we
                    # wanted. O(1) with any length of data inside. Only
                    # more space will be demanded instead of using a deque.

                    # Inside the frame, variables are named lower case
                    # with _ to be seperated.
                    self.SleepFor(2)
                    # dumped_list = collections.deque(maxlen=20)
                    dumped_list = set()
                    come_to_end = False
                    last_fetch = False
                    while not (come_to_end and last_fetch):
                        base_node = self.browser.find_elements(By.CLASS_NAME, "ReplyModal_scroll3_2kADQ")[0].find_elements(
                            By.CLASS_NAME, "item1")[0]
                        rendered_comments = base_node.find_elements(By.CLASS_NAME, "vue-recycle-scroller__item-view")

                        if come_to_end:
                            last_fetch = True

                        # Dump main comment first
                        base_wrapper = base_node.find_elements(By.CLASS_NAME, "item1in")[0].find_elements(
                            By.CLASS_NAME, "text")[0]
                        main_comment_id = base_wrapper.find_elements(By.TAG_NAME, "a")[0].get_attribute("href")[20:]
                        main_comment_name = base_wrapper.find_elements(By.TAG_NAME, "a")[0].get_attribute("innerText")
                        main_comment_time = base_node.find_elements(By.CLASS_NAME, "item1in")[0].find_elements(
                            By.CLASS_NAME, "info")[0].find_elements(By.TAG_NAME, "div")[0].get_attribute(
                            "innerText")
                        main_comment_content = base_wrapper.find_elements(By.TAG_NAME, "span")[-1].get_attribute(
                            "innerHTML")
                        main_comment_content = self.SerializeEmojy(main_comment_content)
                        likes_exis = base_node.find_elements(By.CLASS_NAME, "item1in")[0].find_elements(
                            By.CLASS_NAME, "info")[0].find_elements(By.CLASS_NAME, "woo-like-count")
                        main_comment_likes = likes_exis[0].get_attribute("innerText") if len(likes_exis) else "0"

                        temp_key = main_comment_id + main_comment_time
                        if temp_key not in dumped_list:
                            # print("m likes:", main_comment_likes, main_comment_id, main_comment_name,
                            #       main_comment_time, main_comment_content)
                            line = " ".join(["m likes:", main_comment_likes, main_comment_id, main_comment_name,
                                main_comment_time, main_comment_content + "\n"])
                            CurrentFileObj.write(line)
                            # dumped_list.append(temp_key)
                            dumped_list.add(temp_key)

                        # Dump the replies
                        warned = False
                        for i_in in range(len(rendered_comments)):
                            # self.SleepFor(0.1)
                            raw_in = rendered_comments[i_in]
                            # Still, res are expected to be sliced.
                            wbid_in = raw_in.find_elements(By.TAG_NAME, "a")[0].get_attribute("href")[20:]
                            time_in = raw_in.find_elements(By.CLASS_NAME, "info")[0].find_elements(
                                By.TAG_NAME, "div")[0].get_attribute("innerText")
                            # Skip if existence
                            key_in = wbid_in + time_in
                            if key_in in dumped_list:
                                if not warned:
                                    print("Reply already dumped, skipping...")
                                    warned = True
                                continue
                            # dumped_list.append(key_in)
                            dumped_list.add(key_in)

                            # For now, the dumping work should be started:
                            reply = raw_in.find_elements(By.CLASS_NAME, "text")[0].find_elements(
                                By.TAG_NAME, "span")[-1].get_attribute("innerHTML")
                            reply = self.SerializeEmojy(reply)
                            name_in = raw_in.find_elements(By.TAG_NAME, "a")[0].get_attribute("innerText")
                            likes_exis_in = raw_in.find_elements(By.CLASS_NAME, "info")[0].find_elements(
                                By.CLASS_NAME, "woo-like-count")
                            likes = likes_exis_in[0].get_attribute("innerText") if len(likes_exis_in) else '0'
                            # print("r likes:", likes, wbid_in, name_in, time_in, reply)
                            line = " ".join(["r likes:", likes, wbid_in, name_in, time_in, reply + "\n"])
                            CurrentFileObj.write(line)

                        y_in = self.browser.find_elements(By.CLASS_NAME, "ReplyModal_scroll3_2kADQ")[0].get_attribute(
                            'scrollTop')
                        self.browser.execute_script(
                            "document.getElementsByClassName('ReplyModal_scroll3_2kADQ')[0].scrollBy(0, 500)")
                        if y_in == self.browser.find_elements(By.CLASS_NAME, "ReplyModal_scroll3_2kADQ")[0].get_attribute(
                                'scrollTop'):
                            come_to_end = True
                        self.SleepFor(1)

                    # At the end of this scope, don't forget to close this frame.
                    self.browser.find_elements(By.CLASS_NAME, "wbpro-layer")[0].find_elements(By.TAG_NAME, "i")[0].click()
                # ELSE: dump the main comment only
                else:
                    if not slept:
                        self.SleepFor(0.8)
                        slept = True
                    main_comment_content = raw.find_elements(By.CLASS_NAME, "text")[0].find_elements(
                        By.TAG_NAME, "span")[-1].get_attribute("innerHTML")
                    main_comment_content = self.SerializeEmojy(main_comment_content)
                    main_comment_name = raw.find_elements(By.TAG_NAME, "a")[1].get_attribute("innerText")
                    likes_exis = raw.find_elements(By.CLASS_NAME, "item1in")[0].find_elements(
                            By.CLASS_NAME, "info")[0].find_elements(By.CLASS_NAME, "woo-like-count")
                    main_comment_likes = likes_exis[0].get_attribute("innerText") if len(likes_exis) else '0'
                    # print("m-o likes:", main_comment_likes, wbid, main_comment_name,
                    #       time, main_comment_content)
                    line = " ".join(["m-o likes:", main_comment_likes, wbid, main_comment_name, 
                                        time, main_comment_content + "\n"])
                    CurrentFileObj.write(line)

            # Scroll for new elements being pushed in the rendered list.
            # Before that, the y position of scroller should be stored.
            # If y position doesn't change after scrolling, ComeToEnd is True.
            y = self.browser.find_elements(By.TAG_NAME, "html")[0].get_attribute("scrollTop")
            self.browser.execute_script("window.scrollBy(0,500);")
            if y == self.browser.find_elements(By.TAG_NAME, "html")[0].get_attribute("scrollTop"):
                ComeToEnd = True
            self.SleepFor(1.5)

        # Close file object
        CurrentFileObj.close()

        # Don't forget to navigate back!
        print("Current page is finished, navigating back...")
        self.browser.back()


if __name__ == '__main__':
    try:
        CB = CreeperExplode()
    except KeyboardInterrupt:
        print("Program stopped by force")
