import os
import PyInstaller.__main__

def version_to_tuple(version):
    return tuple(map(int, (version.split("."))))

# PyInstaller 6.0.0부턴 --contents_directory 추가 필요(--ondir은 default로 설정되는 인자)
def pyInstallerVersionCheck():
    import PyInstaller
    PyInsVer = version_to_tuple(PyInstaller.__version__)
    PyInsVerStr = '--contents-directory=.' if PyInsVer >= version_to_tuple("6.0.0") else '--onedir'
    return PyInsVerStr

PyInstaller.__main__.run([
    'arknights_client_pytesseract_ocr.py',

    f'--add-data=.env{os.pathsep}.',
    f'--add-data=resource/ip.txt{os.pathsep}resource/',
    f'--add-data=resource/arknights_client.ui{os.pathsep}resource/',
    f'--add-data=resource/operation.PNG{os.pathsep}resource/',

    '--noconfirm',
    pyInstallerVersionCheck(),

    '--icon=resource/arknight_sanity_detector.ico',
    # '--onefile',
    '--noconsole',
])