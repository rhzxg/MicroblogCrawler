from core.Utility import *
import xlwings as Excel
import warnings
import os

# Excel Serializer
class ExcelSerializer:
    def __init__(self) -> None:
        warnings.filterwarnings("ignore")
        try:
            self.excelApp = Excel.App(False, False)
        except:
            Utility.PrintLog("Excel is not installed properly on this computer! Program exiting...", Constant.Color.red)
            Utility.ExitProgram()

        self.excelApp.display_alerts = False    
        self.excelApp.screen_updating = False

        self.excelBook = self.excelApp.books.add()
        self.excelSheet = self.excelBook.sheets["sheet1"]

        self.excelSheet.range("A:F").api.NumberFormat ="@"
        self.excelSheet.range("A1:G1").api.Merge()
        self.excelSheet.range(1, 1).row_height = 30
        self.excelSheet.range("A:B").column_width = 10
        self.excelSheet.range("C:C").column_width = 12
        self.excelSheet.range("D:D").column_width = 15
        self.excelSheet.range("E:E").column_width = 10
        self.excelSheet.range("F:F").column_width = 15
        self.excelSheet.range("G:G").column_width = 10
        self.excelSheet.range("H:H").column_width = 120
        self.excelSheet.range(1, 1).api.HorizontalAlignment = -4131

        headers = ["Type", "Like Count", "User ID", "User Name", "Gender", "Post Time", "IP Address", "Content"]
        self.excelSheet.range("A2").value = headers
        self.excelSheet.range('A2').api.Select()

        self.currentRow = 3

    def WriteMainContent(self, content: str, hyperLink: str) -> None:
        # fill row
        excelCellA = self.excelSheet.range("A1")
        excelCellA.value = content
        excelCellA.api.WrapText = True

        # hyper link
        excelCellG = self.excelSheet.range("H1")
        excelCellG.api.Hyperlinks.Add(Anchor=excelCellG.api, Address=hyperLink, TextToDisplay="Click to visit original Microblog.")
        

    def WriteLine(self, values: list) -> None:
        cellADesc = "A" + str(self.currentRow)
        excelCellA = self.excelSheet.range(cellADesc)
        
        # fill row
        excelCellA.value = values
        
        # hyper link
        cellCDesc = "C" + str(self.currentRow)
        excelCellC = self.excelSheet.range(cellCDesc)
        hyperLink = "https://weibo.com/u/" + values[2]
        excelCellC.api.Hyperlinks.Add(Anchor=excelCellC.api, Address=hyperLink, TextToDisplay=excelCellC.value)

        self.currentRow += 1

    def Save(self, folderName: str, fileName: str) -> None:
        if not fileName.endswith(".xlsx"):
            fileName += ".xlsx"
        fullPath = os.path.join(folderName , fileName)
        self.excelBook.save(fullPath)

    def Close(self) -> None:
        self.excelBook.close()
