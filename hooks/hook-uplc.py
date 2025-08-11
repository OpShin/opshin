from PyInstaller.utils.hooks import collect_data_files

# Instruct pyinstaller to collect data files from uplc package.
datas = collect_data_files("uplc")
