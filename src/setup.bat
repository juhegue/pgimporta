rem Crea instalador

python setup.py py2exe


python setup_crea.py

copy imagenes\pgimporta.bmp install\.
copy imagenes\pgimporta.ico install\.
"C:\Program Files (x86)\NSIS\makensis" /V4 install\pgimporta.nsi"

pause