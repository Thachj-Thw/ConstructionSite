import zipfile
import re
import os


class ConstructionSiteReport():
    '''
    Class tạo báo cáo công trình cty DH
    '''
    source = os.path.dirname(os.path.normpath(__file__))
    base_path = os.path.join(os.path.dirname(os.path.normpath(__file__)), "base.docx")

    def __init__(self, filename: str) -> None:
        self.filename = filename if os.path.splitext(filename)[1] == ".docx" else filename + ".docx"
        self.pages = ""
        zipbase = zipfile.ZipFile(self.base_path, "r")
        search_page = re.search(r"(?<=<w:body>).+?(?=<w:sectPr)", zipbase.read("word/document.xml").decode("utf-8"))
        zipbase.close()
        if not search_page:
            raise Exception("Something wrong with base.docx")
        self.page_base = search_page.group()
        self.paraId = 1
        self.docPrid = 1
        

    def add_page(self, date: str, project_name: str, project_id: str, start_morning: str, end_morning: str, start_afternoon: str, end_afternoon: str, job_morning: str, job_afternoon: str) -> None:
        if len(job_morning) < 4:
            job_morning += [" "] * (4 - len(job_morning))
        if len(job_afternoon) < 4:
            job_afternoon += [" "] * (4 - len(job_afternoon))
        page = self.page_base % (date, project_name, project_id, start_morning, end_morning, start_afternoon, end_afternoon, job_morning[0], job_afternoon[0], job_morning[1], job_afternoon[1], job_morning[2], job_afternoon[2], job_morning[3], job_afternoon[3])
        for para_id in re.findall(r"paraId=\".+?\"", page):
            page = re.sub(para_id, "paraId=\"" + str(hex(self.paraId))[2:].rjust(8, "0").upper() + "\"", page)
            self.paraId += 1
        page = re.sub(r'<w:bookmarkStart w:id="0" w:name="_GoBack"/><w:bookmarkEnd w:id="0"/>', '', page)
        for docPr in re.findall(r'<wp:docPr id="\d+" name="\w+ \d+"/>', page):
            docPr_id = re.search(r'<wp:docPr id="\d+"', docPr).group()
            new_id = docPr_id
            new_docPr = docPr
            while re.search(new_id, self.pages):
                self.docPrid += 1
                new_id = re.sub(r"\d+", str(self.docPrid), docPr_id)
                new_docPr = re.sub(r'\d+', str(self.docPrid), docPr)
            page = re.sub(docPr, new_docPr, page)
        self.pages += page

    def save(self, folder: str = "") -> None:
        zipbase = zipfile.ZipFile(self.base_path)
        output = zipfile.ZipFile(os.path.join(os.path.normpath(folder), self.filename), "w")
        for zipinfo in zipbase.infolist():
            buffer = zipbase.read(zipinfo.filename)
            if zipinfo.filename == 'word/document.xml':
                data = buffer.decode('utf-8')
                buffer = re.sub(r"(?<=<w:body>).+?(?=<w:sectPr)", self.pages, data).encode('utf-8')
            output.writestr(zipinfo, buffer)
        zipbase.close()
        output.close()

    def unzip(self, docxfile: str, folder: str = "") -> None:
        if __name__ != "__main__":
            return
        zipdocx = zipfile.ZipFile(docxfile, "r")
        for zipinfo in zipdocx.infolist():
            save_file = os.path.join(folder, zipinfo.filename)
            save_dir = os.path.dirname(save_file)
            if save_dir and not os.path.isdir(save_dir):
                os.makedirs(save_dir)
            buffer = zipdocx.read(zipinfo.filename)
            tail = os.path.splitext(zipinfo.filename)[1]
            if tail == ".png" or tail == ".jpg":
                with open(save_file, "wb") as f:
                    f.write(buffer)
            else:
                with open(save_file, "w", encoding="utf-8") as f:
                    f.write(buffer.decode('utf-8'))
        zipdocx.close()

    def test(self, documentfile: str, save_as: str):
        if __name__ != "__main__":
            return
        output = zipfile.ZipFile(save_as, "w")
        zipbase = zipfile.ZipFile(self.base_path, "r")
        for zipinfo in zipbase.infolist():
            if zipinfo.filename != 'word/document.xml':
                output.writestr(zipinfo, zipbase.read(zipinfo.filename))
        zipbase.close()
        with open(documentfile, "r", encoding="utf-8") as f:
            buffer = f.read().encode("utf-8")
        output.writestr('word/document.xml', buffer)
        output.close()


if __name__ == "__main__":
    r = ConstructionSiteReport("")
    r.unzip(r.base_path, "docx")
    # r.test(r"document.xml", "test.docx")
