from core.Utility import *
from core.MicroblogCrawler import *

if __name__ == "__main__":
    try:
        crawler = MicrobolgCrawler()
    except KeyboardInterrupt:
        Utility.PrintLog("Program stopped by force!", Constant.Color.red)