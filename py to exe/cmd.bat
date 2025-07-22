pyinstaller --name="GendALF" --onefile --noconsole --icon="GendALF_Logo.ico" --add-data "../asset;asset" --add-data "../documentation.md;documentation.md" ../main.py
pyinstaller --name="update" --onefile --noconsole ../update.py
copy dist\GendALF.exe ..
copy dist\update.exe ..
rmdir /s /q build
rmdir /s /q dist
del GendALF.spec
del update.spec

pause