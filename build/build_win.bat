WHERE ndk-build
@ IF %ERRORLEVEL% NEQ 0 (
    ECHO ERROR: ndk-build not found, please install android NDK first.
    EXIT /B 2
)

@ IF NOT EXIST ".\venv\Scripts\activate" (
    ECHO ERROR: Please run build from tracecat root path.
    EXIT /B
)

cd demon

call ndk-build clean

call ndk-build

cd ..

@ IF NOT EXIST ".\demon\obj\local\arm64-v8a\tracecatd" (
    ECHO ERROR: tracecatd build failed, please check the errors.
    EXIT /B
)

call .\venv\Scripts\activate

rd /s /q .\build\build\

rd /s /q .\build\dist\

pyinstaller .\build\spec\tracecat_win_dir.spec --workpath=".\\build\build\\" --distpath=".\\build\dist\\"

pyinstaller .\scripts\run_all.py --specpath=".\\build\\build\\" --workpath=".\\build\\build\\" --distpath=".\\build\\dist\\"

xcopy /s /y .\build\dist\run_all .\build\dist\tracecat

tar -acvf .\build\dist\tracecat.zip -C .\build\dist\ tracecat

call deactivate