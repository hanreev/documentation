# -*- coding: utf-8 -*-

import os
import re
import sys
from glob import glob

from bs4 import BeautifulSoup
from PyQt5.QtCore import QSettings
from PyQt5.QtGui import QDoubleValidator
from PyQt5.QtWidgets import QApplication, QFileDialog, QMessageBox, QWidget
from xhtml2pdf import pisa
from reportlab.lib import pagesizes

from logger import create_logger
from ui_documentation import Ui_Form

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
log_filename = os.path.join(BASE_DIR, 'documentation.log')
settings_filename = os.path.join(BASE_DIR, 'documentation.ini')
logo = os.path.join(BASE_DIR, 'logo.png')

template = '''<!DOCTYPE html>
<html>
  <head>
    <meta charset="UTF-8" />
    <title>Document</title>

    <style>
      @page {
        size: [PAGE_SIZE];

        @frame content_frame {
          top: [MARGIN_TOP];
          left: [MARGIN_LEFT];
          right: [MARGIN_RIGHT];
        }

        @frame footer_frame {
          -pdf-frame-content: footer_content;
          top: 26.5cm;
          left: [MARGIN_LEFT];
          right: [MARGIN_RIGHT];
        }
      }

      body {
        font-family: Helvetica sans-serif;
      }

      h1 {
        font-size: 18pt;
        margin: 0;
      }

      h2 {
        font-size: 14pt;
        margin: 0;
      }

      h3 {
        font-size: 11pt;
        font-weight: 500;
        margin: 0;
      }

      table {
        width: 100%;
        border-collapse: collapse;
      }

      td.box {
        width: 18pt;
        height: 16pt;
        border: 1pt solid black;
        text-align: center;
        padding-top: 2pt;
      }

      td.separator {
        width: 6pt;
      }

      .valign-top {
        vertical-align: top;
      }

      .valign-bottom {
        vertical-align: bottom;
      }

      .table-box td {
        font-weight: bold;
        font-size: 10pt;
        height: 16pt;
      }

      .header {
        margin-bottom: 0.5cm;
      }

      .table-content {
        page-break-after: always;
      }

      .table-content img {
        width: 100%;
      }

      .img-container {
        text-align: center;
      }
    </style>
  </head>

  <body>
    <div id="footer_content" style="text-align: center; font-size: 10pt; font-weight: bold">
      <p style="margin-bottom: 30pt">PENANGGUNG JAWAB LAPANGAN</p>
      <p id="supervisor" style="text-decoration: underline; margin-bottom: 0"></p>
      <p style="margin-top: 0">Team Leader</p>
    </div>
  </body>
</html>
'''

header_template = '''<div class="header">
    <table>
    <tr>
        <td width="30%" class="valign-top">
        <table>
            <tr>
            <td width="1.6cm" class="valign-top">
                <img class="logo" width="1.6cm" />
            </td>
            <td>
                <h2>PEMERINTAH KOTA JAMBI</h2>
                <h3>DINAS PEKERJAAN UMUM DAN PENATAAN RUANG</h3>
                <p style="font-size: 8pt; margin: 0">
                ALAMAT: JL. H. ZAINIR HAVIZ NO. 04, KEC. KOTABARU JAMBI TELP. 40553
                </p>
            </td>
            </tr>
        </table>
        </td>
        <td align="center">
        <h1 class="title"></h1>
        </td>
        <td width="30%">
        <table class="table-box">
            <tr>
            <td>
                <table>
                <tr class="no-distribusi">
                    <td>NOMOR DISTRIBUSI KE</td>
                </tr>
                </table>
            </td>
            </tr>
            <tr>
            <td style="vertical-align: bottom">NOMOR LEMBAR KARTU LEGER JALAN:</td>
            </tr>
            <tr>
            <td>
                <table>
                <tr class="no-leger">
                    <td></td>
                </tr>
                </table>
            </td>
            </tr>
        </table>
        </td>
    </tr>
    </table>
</div>
'''

table_template = '''
<table class="table-content">
    <tr>
        <td class="cell-0"></td>
        <td width="1cm"></td>
        <td class="cell-1"></td>
        <td width="1cm"></td>
        <td class="cell-2"></td>
    </tr>
    <tr>
        <td height="1cm"></td>
    </tr>
    <tr>
        <td class="cell-3"></td>
        <td width="1cm"></td>
        <td class="cell-4"></td>
        <td width="1cm"></td>
        <td class="cell-5"></td>
    </tr>
</table>
'''

picture_template = '''
<table>
    <tr>
        <td colspan="5" class="img-container">
            <img>
        </td>
    </tr>
    <tr>
        <td height="24pt"></td>
    </tr>
    <tr>
        <td></td>
        <td>NOMOR RUAS</td>
        <td width="10pt">:</td>
        <td class="no-ruas"></td>
        <td></td>
    </tr>
    <tr>
        <td></td>
        <td>NAMA RUAS</td>
        <td width="10pt">:</td>
        <td class="nama-ruas"></td>
        <td></td>
    </tr>
    <tr>
        <td></td>
        <td>STA</td>
        <td width="10pt">:</td>
        <td class="sta"></td>
        <td></td>
    </tr>
</table>
'''


class Documentation(QWidget, Ui_Form):
    def __init__(self):
        super(Documentation, self).__init__()
        self.settings = QSettings(settings_filename, QSettings.IniFormat)
        self.setup_ui()

        self.logger = create_logger(log_filename)

    def setup_ui(self):
        self.setupUi(self)

        paper_sizes = []

        for attribute in dir(pagesizes):
            if attribute.startswith('_'):
                continue
            if attribute in ['mm', 'inch', 'portrait', 'landscape', 'elevenSeventeen', 'legal', 'letter']:
                continue
            paper_sizes.append(attribute)

        for paper_size in sorted(paper_sizes, key=lambda ps: re.sub(r'(\d+)', lambda m: '{:0>4}'.format(m.group(1)), ps)):
            self.cb_paperSize.addItem(paper_size)

        self.cb_paperSize.addItem('Custom')
        self.cb_paperOrientation.addItem('Portrait')
        self.cb_paperOrientation.addItem('Landscape')
        self.le_paperWidth.setValidator(QDoubleValidator(0, 10, 4, self))
        self.le_paperHeight.setValidator(QDoubleValidator(0, 10, 4, self))
        self.le_paperWidth.setEnabled(False)
        self.le_paperHeight.setEnabled(False)
        self.le_mTop.setValidator(QDoubleValidator(0, 10, 4, self))
        self.le_mBottom.setValidator(QDoubleValidator(0, 10, 4, self))
        self.le_mLeft.setValidator(QDoubleValidator(0, 10, 4, self))
        self.le_mRight.setValidator(QDoubleValidator(0, 10, 4, self))

        # TODO: Remove these lines to enable supervisor in footer
        self.le_supervisor.hide()
        self.label_7.hide()

        self.setup_signals()
        self.load_settings()
        self.show()

        # TODO: Adjust template for different paper sizes
        # Lock paper size and orientation
        self.cb_paperSize.setCurrentText('A3')
        self.cb_paperSize.setDisabled(True)
        self.cb_paperOrientation.setCurrentText('Landscape')
        self.cb_paperOrientation.setDisabled(True)

    def setup_signals(self):
        self.btn_source.clicked.connect(self.browse_source)
        self.btn_output.clicked.connect(self.browse_output)
        self.cb_paperSize.currentTextChanged.connect(self.change_paper_size)
        self.btn_clearLog.clicked.connect(self.clear_log)
        self.btn_start.clicked.connect(self.start)

    def browse_source(self):
        source = QFileDialog.getExistingDirectory(self, 'Source')
        self.le_source.setText(source)

    def browse_output(self):
        output = QFileDialog.getExistingDirectory(self, 'Output Directory')
        self.le_output.setText(output)

    def clear_log(self):
        self.te_log.clear()

    def start(self):
        self.freeze_ui(True)
        src_dir = self.le_source.text()
        if not (bool(src_dir) and os.path.exists(src_dir)):
            QMessageBox.critical(self, 'Error', 'Invalid source directory')
            self.freeze_ui(False)
            return

        output = self.le_output.text()
        if not (bool(output) and os.path.exists(output)):
            QMessageBox.critical(self, 'Error', 'Invalid output directory')
            self.freeze_ui(False)
            return

        self.write_log('Processing source directory "{}"'.format(src_dir))

        for basename in os.listdir(src_dir):
            full_path = os.path.join(src_dir, basename)
            if not os.path.isdir(full_path):
                continue
            self.write_log('# Current directory: ' + basename)
            self.insert_picture(full_path, output)
            self.write_log('==========\n')

        self.freeze_ui(False)

    def convert_to_pdf(self, content, output):
        self.write_log('# Writing PDF: ' + output)
        try:
            with open(output, 'wb') as fp:
                pisa_status = pisa.CreatePDF(content, dest=fp)

            self.write_log('Done!')
            return pisa_status.err
        except Exception as e:
            QMessageBox.critical(self, 'Error', str(e))
            return 1

    def get_header(self, no_ruas, page_number):
        no_distribusi = self.le_no_dist.text().strip()
        no_leger = self.le_no_lembar.text()

        def replace_no_leger(match):
            return match.group(1) + str(no_ruas) + match.group(3) + '{:0>3}'.format(page_number) + match.group(5)
        no_leger = re.sub(r'^(\d{2} )(\d{3})( .{2} \w )(\d{3})( \d)$', replace_no_leger, no_leger)

        header_soup = BeautifulSoup(header_template, 'lxml')
        header_soup.find(class_='logo')['src'] = 'file:///' + logo.replace('\\', '/')
        header_soup.find(class_='title').string = self.le_title.text()
        tr_no_distribusi = header_soup.find('tr', class_='no-distribusi')
        tr_no_leger = header_soup.find('tr', class_='no-leger')

        for n in no_distribusi:
            td = header_soup.new_tag('td')
            if n == ' ':
                td['class'] = 'separator'
            else:
                td['class'] = 'box'
                td.string = n
            tr_no_distribusi.append(td)

        for n in no_leger:
            td = header_soup.new_tag('td')
            if n == ' ':
                td['class'] = 'separator'
            else:
                td['class'] = 'box'
                td.string = n
            tr_no_leger.append(td)
        return header_soup

    def insert_picture(self, src_dir, output_dir):
        basename = os.path.basename(src_dir)
        parts = re.split(r' ?- ?', basename)
        if len(parts) != 2:
            print('Invalid directory', basename)
            return
        no_ruas, nm_ruas = parts

        pictures = []
        for filetype in ['*.jpg', '*.jpeg', '*.png']:
            pictures.extend(
                glob(os.path.join(src_dir, '**', 'STA ' + filetype), recursive=True))

        pictures = sorted(pictures, key=lambda f: os.path.basename(f))
        paper_size = self.cb_paperSize.currentText().lower()
        if paper_size == 'custom':
            page_size = '{}cm {}cm'.format(
                self.le_paperWidth.text(), self.le_paperWidth.text())
        else:
            page_size = '{} {}'.format(
                paper_size, self.cb_paperOrientation.currentText().lower())
        template_content = template
        template_content = template_content.replace(
            '[PAGE_SIZE]', page_size)
        template_content = template_content.replace(
            '[MARGIN_TOP]', self.le_mTop.text() + 'cm')
        template_content = template_content.replace(
            '[MARGIN_BOTTOM]', self.le_mBottom.text() + 'cm')
        template_content = template_content.replace(
            '[MARGIN_LEFT]', self.le_mLeft.text() + 'cm')
        template_content = template_content.replace(
            '[MARGIN_RIGHT]', self.le_mRight.text() + 'cm')
        soup = BeautifulSoup(template_content, 'lxml')

        soup.find(id='supervisor').string = '( {} )'.format(
            self.le_supervisor.text())

        self.write_log('# Pictures found: ' + str(len(pictures)))

        header_soup = None
        table_soup = None
        page_number = 1
        for i, pic_path in enumerate(pictures):
            cell_idx = i % 6
            if cell_idx == 0:
                if header_soup is not None:
                    soup.body.append(header_soup)
                if table_soup is not None:
                    soup.body.append(table_soup)
                header_soup = self.get_header(no_ruas, page_number)
                table_soup = BeautifulSoup(table_template, 'lxml')
                page_number += 1
            pic_soup = BeautifulSoup(picture_template, 'lxml')
            pic_soup.find('img')['src'] = 'file:///' + \
                pic_path.replace('\\', '/')
            pic_soup.find('td', class_='no-ruas').string = no_ruas
            pic_soup.find('td', class_='nama-ruas').string = nm_ruas
            sta = ''
            sta_suffix = ''
            m_sta = re.match(r'STA ([\d+]+) *(KIRI|KANAN)*.*', os.path.basename(pic_path))
            if m_sta:
                sta = m_sta.group(1) or ''
                sta_suffix = m_sta.group(2) or ''
            pic_dir = os.path.basename(os.path.dirname(pic_path)).upper()
            if pic_dir == 'KIRI' or pic_dir == 'KANAN':
                sta_suffix = pic_dir
            pic_soup.find('td', class_='sta').string = ' '.join([sta, sta_suffix])
            table_soup.find('td', class_='cell-' +
                            str(cell_idx)).append(pic_soup)
        if header_soup is not None:
            soup.body.append(header_soup)
        if table_soup is not None:
            soup.body.append(table_soup)

        # TODO: Remove this lines to show footer
        soup.find(id='footer_content').clear()

        output = os.path.join(output_dir, '{}.pdf'.format(os.path.basename(src_dir)))
        self.convert_to_pdf(str(soup), output=output.replace('\\', '/'))

    def load_settings(self):
        geometry = self.settings.value('Ui/Geometry')
        if geometry:
            self.restoreGeometry(geometry)
        self.le_source.setText(self.settings.value('Input/Source'))
        self.le_output.setText(self.settings.value('Input/Output'))
        self.le_title.setText(self.settings.value('Input/Title'))
        self.le_no_dist.setText(self.settings.value('Input/DistributionNumber', '12345'))
        self.le_no_lembar.setText(self.settings.value('Input/PageNumber', '15 000 -- K 000 1'))
        self.le_supervisor.setText(self.settings.value('Input/Supervisor'))
        self.cb_paperSize.setCurrentText(
            self.settings.value('Page/Size', 'A3'))
        self.cb_paperOrientation.setCurrentText(
            self.settings.value('Page/Orientation', 'Landscape'))
        self.le_paperWidth.setText(self.settings.value('Page/Width'))
        self.le_paperHeight.setText(self.settings.value('Page/Height'))
        self.le_mTop.setText(self.settings.value('Margin/Top'))
        self.le_mBottom.setText(self.settings.value('Margin/Bottom'))
        self.le_mLeft.setText(self.settings.value('Margin/Left'))
        self.le_mRight.setText(self.settings.value('Margin/Right'))

    def save_settings(self):
        self.settings.setValue('Ui/Geometry', self.saveGeometry())
        self.settings.setValue('Input/Source', self.le_source.text())
        self.settings.setValue('Input/Output', self.le_output.text())
        self.settings.setValue('Input/Title', self.le_title.text())
        self.settings.setValue('Input/DistributionNumber', self.le_no_dist.text())
        self.settings.setValue('Input/PageNumber', self.le_no_lembar.text())
        self.settings.setValue('Input/Supervisor', self.le_supervisor.text())
        self.settings.setValue('Page/Size', self.cb_paperSize.currentText())
        self.settings.setValue(
            'Page/Orientation', self.cb_paperOrientation.currentText())
        self.settings.setValue('Page/Width', self.le_paperWidth.text())
        self.settings.setValue('Page/Height', self.le_paperHeight.text())
        self.settings.setValue('Margin/Top', self.le_mTop.text())
        self.settings.setValue('Margin/Bottom', self.le_mBottom.text())
        self.settings.setValue('Margin/Left', self.le_mLeft.text())
        self.settings.setValue('Margin/Right', self.le_mRight.text())

    def freeze_ui(self, freeze: bool):
        self.le_source.setDisabled(freeze)
        self.btn_source.setDisabled(freeze)
        self.le_output.setDisabled(freeze)
        self.btn_output.setDisabled(freeze)
        self.le_title.setDisabled(freeze)
        self.le_supervisor.setDisabled(freeze)
        self.gb_paperSize.setDisabled(freeze)
        self.gb_margins.setDisabled(freeze)
        self.btn_start.setDisabled(freeze)
        QApplication.processEvents()

    def change_paper_size(self, paper_size):
        is_custom = paper_size.lower() == 'custom'
        self.le_paperWidth.setEnabled(is_custom)
        self.le_paperHeight.setEnabled(is_custom)
        if is_custom:
            self.le_paperWidth.setText(self.settings.value('Page/Width'))
            self.le_paperHeight.setText(self.settings.value('Page/Height'))
        else:
            self.settings.setValue('Page/Width', self.le_paperWidth.text())
            self.settings.setValue('Page/Height', self.le_paperHeight.text())
            self.le_paperWidth.clear()
            self.le_paperHeight.clear()

    def write_log(self, log):
        self.te_log.appendPlainText(log)
        self.te_log.ensureCursorVisible()
        QApplication.processEvents()
        self.logger.info(log)

    def closeEvent(self, event):
        reply = QMessageBox.question(self, 'Keluar', 'Keluar aplikasi?')

        if reply == QMessageBox.Yes:
            self.save_settings()
            event.accept()
        else:
            event.ignore()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    doc = Documentation()
    sys.exit(app.exec_())
