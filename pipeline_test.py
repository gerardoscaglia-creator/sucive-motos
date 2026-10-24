import unittest,tempfile,os,json,types,sys
from unittest.mock import patch
import capture
from pathlib import Path

class PipelineTests(unittest.TestCase):
    def test_period_comes_from_report_not_update_date_or_clock(self):
        for period,updated,expected in [('01/12/2026','01/01/2027','2026-12'),('01/01/2027','03/02/2027','2027-01')]:
            page=types.SimpleNamespace(extract_text=lambda:f'Fecha de actualización {updated}\nPeríodo {period}\n')
            with patch.dict(sys.modules,{'pypdf':types.SimpleNamespace(PdfReader=lambda _:types.SimpleNamespace(pages=[page]))}):
                self.assertEqual(capture.parse_pdf('unused')[0],expected)

    def test_delayed_repeated_pdf_preserves_history_and_is_idempotent(self):
        with tempfile.TemporaryDirectory() as root:
            data=os.path.join(root,'data');pdfs=os.path.join(root,'pdfs');os.mkdir(data)
            old=os.path.join(data,'2026-12.json');original=b'{"periodo":"2026-12","data":{}}';Path(old).write_bytes(original)
            def download(_,dest):
                with open(dest,'wb') as f:f.write(b'fixed official report fixture')
            with patch.multiple(capture,DATA_DIR=data,PDF_DIR=pdfs,DB=os.path.join(root,'test.db')),patch.object(capture,'download',download),patch.object(capture,'parse_pdf',return_value=('2027-01',{'Soriano':{'YUMBO':0}},{})),patch.object(capture,'validate',return_value=[]):
                capture.main(); first=Path(data,'2027-01.json').read_bytes();capture.main()
                self.assertEqual(first,Path(data,'2027-01.json').read_bytes())
                self.assertEqual(original,Path(old).read_bytes())
                self.assertFalse(os.path.exists(os.path.join(data,'2027-02.json')))

    def test_invalid_unpublished_report_never_creates_snapshot(self):
        with tempfile.TemporaryDirectory() as root:
            with patch.multiple(capture,DATA_DIR=os.path.join(root,'data'),PDF_DIR=os.path.join(root,'pdfs')),patch.object(capture,'download'),patch.object(capture,'parse_pdf',return_value=(None,{},{})):
                with self.assertRaises(SystemExit):capture.main()
                self.assertEqual(os.listdir(capture.DATA_DIR),[])

if __name__=='__main__':unittest.main()
