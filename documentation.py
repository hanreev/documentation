# -*- coding: utf-8 -*-

import math
import os
import re
import sys
from glob import glob

from bs4 import BeautifulSoup
from PyQt5.QtCore import QSettings
from PyQt5.QtGui import QDoubleValidator
from PyQt5.QtWidgets import QApplication, QFileDialog, QMessageBox, QWidget
from xhtml2pdf import pisa

from logger import create_logger
from ui_documentation import Ui_Form

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
log_filename = os.path.join(BASE_DIR, 'documentation.log')
settings_filename = os.path.join(BASE_DIR, 'documentation.ini')
template = os.path.join(BASE_DIR, 'template.html')
logo = os.path.join(BASE_DIR, 'logo.png')

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
        <td>KM</td>
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

        self.setWindowTitle('AutoDoc')
        paper_sizes = ['Legal', 'Letter']
        for i in range(7):
            paper_sizes.append('A' + str(i))
            paper_sizes.append('B' + str(i))
        for paper_size in sorted(paper_sizes):
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

        self.setup_signals()
        self.load_settings()
        self.show()

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
        with open(output, 'wb') as fp:
            pisa_status = pisa.CreatePDF(content, dest=fp)

        return pisa_status.err

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

        no_distribusi = '12345'
        page_count = math.ceil(len(pictures) / 6)
        no_leger = '15 {} -- K {:0>3} 1'.format(no_ruas, page_count)

        with open(template) as fp:
            template_content = fp.read()
            paper_size = self.cb_paperSize.currentText().lower()
            if paper_size == 'custom':
                page_size = '{}cm {}cm'.format(
                    self.le_paperWidth.text(), self.le_paperWidth.text())
            else:
                page_size = '{} {}'.format(
                    paper_size, self.cb_paperOrientation.currentText().lower())
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

        soup.find(id='logo')['src'] = 'file:///' + logo.replace('\\', '/')
        soup.find(id='title').string = self.le_title.text()
        soup.find(id='supervisor').string = '( {} )'.format(
            self.le_supervisor.text())
        tr_no_distribusi = soup.find('tr', id='no-distribusi')
        tr_no_leger = soup.find('tr', id='no-leger')

        for n in no_distribusi:
            td = soup.new_tag('td')
            td['class'] = 'box'
            td.string = n
            tr_no_distribusi.append(td)

        for n in no_leger:
            td = soup.new_tag('td')
            if n == ' ':
                td['class'] = 'separator'
            else:
                td['class'] = 'box'
                td.string = n
            tr_no_leger.append(td)

        pictures = []
        for filetype in ['*.jpg', '*.jpeg', '*.png']:
            pictures.extend(
                glob(os.path.join(src_dir, '**', 'STA ' + filetype), recursive=True))

        self.write_log('# Pictures found: ' + str(len(pictures)))

        table_soup = None
        for i, pic_path in enumerate(pictures):
            cell_idx = i % 6
            if cell_idx == 0:
                if table_soup is not None:
                    soup.body.append(table_soup)
                table_soup = BeautifulSoup(table_template, 'lxml')
            pic_soup = BeautifulSoup(picture_template, 'lxml')
            pic_soup.find('img')['src'] = 'file:///' + \
                pic_path.replace('\\', '/')
            pic_soup.find('td', class_='no-ruas').string = no_ruas
            pic_soup.find('td', class_='nama-ruas').string = nm_ruas
            m_sta = re.match(r'STA ([\d+]+) .+', os.path.basename(pic_path))
            sta = m_sta.group(1) if m_sta else ''
            pic_soup.find('td', class_='sta').string = sta
            table_soup.find('td', class_='cell-' +
                            str(cell_idx)).append(pic_soup)
        if table_soup is not None:
            soup.body.append(table_soup)

        self.convert_to_pdf(str(soup), output=os.path.join(
            output_dir, '{}.pdf'.format(os.path.basename(src_dir))))

    def load_settings(self):
        geometry = self.settings.value('Ui/Geometry')
        if geometry:
            self.restoreGeometry(geometry)
        self.le_source.setText(self.settings.value('Input/Source'))
        self.le_output.setText(self.settings.value('Input/Output'))
        self.le_title.setText(self.settings.value('Input/Title'))
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
