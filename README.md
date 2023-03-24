Documentation
=====

Automated photo documentation


## Requirements ###

* [Python 3.9](https://docs.python.org/3.9/)
* [PyQt5](https://www.riverbankcomputing.com/static/Docs/PyQt5/index.html)
* [Beautiful Soup 4](https://www.crummy.com/software/BeautifulSoup/)
* [xhtml2pdf](https://github.com/xhtml2pdf/xhtml2pdf)
* [PyInstaller](http://www.pyinstaller.org/) (Only for making executable file. For windows users, use latest development version)


### Running ###

* Run these commands from terminal or cmd
  ```bash
  cd path_to_project

  python documentation.py
  ```


### Making Executable ###

* Run these commands from terminal or cmd
  ```bash
  cd path_to_project

  pyinstaller -w -i folder.ico documentation.py
  ```
* Executable created but there is an error
* Adjust `documentation.spec` as follow
  ```python
  a = Analysis(['documentation.py'],
              ...
              datas=[('logo.png', '.'),
                      ('folder.png', '.'),
                      ('files/arabic_reshaper', 'arabic_reshaper')],
              hiddenimports=['reportlab.graphics.barcode.code128',
                              'reportlab.graphics.barcode.code39',
                              'reportlab.graphics.barcode.code93',
                              'reportlab.graphics.barcode.ecc200datamatrix',
                              'reportlab.graphics.barcode.usps',
                              'reportlab.graphics.barcode.usps4s'],
              ...
              )
  ```
* Run this command to generate executable
  ```bash
  pyinstaller documentation.spec
  ```


## Contact ##

* [hanreev@gmail.com](mailto:hanreev@gmail.com)


## Changelog ##

