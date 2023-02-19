# Tracecat

A general kernel trace analysis framework

## Download

`git clone https://github.com/kernel-cyrus/tracecat.git`

## Start to Run

#### Run on Linux or MacOS

Setup environment:

```
    1. Install python3
    sudo apt-get python3

    2. Install virtualenv
    pip3 install virtualenv

    3. Init virtual environment
    python3 -m venv ./venv

    4. Enter virtual environment
    source ./venv/bin/activate

    5. Install required packages
    pip3 install -r ./venv/requirements.txt

    6. Quit virtual environment
    ./venv/bin/deactivate
```

Then you can simply run by:

```
    1. Enter virtual environment
    source ./venv/bin/activate

    2. Run tracecat
    python3 tracecat.py

    3. Quit virtual environment
    ./venv/bin/deactivate
```

#### Run on Windows

Setup environment:

```
    1. Download and Install python3
    https://www.python.org/downloads/

    2. Install virtualenv
    pip install virtualenv

    3. Init virtual environment
    python -m venv .\venv

    4. Enter virtual environment
    .\venv\Scripts\activate

    5. Install required packages
    pip3 install -r .\venv\requirements.txt

    6. Quit virtual environment
    .\venv\Scripts\deactivate
```

Then you can simply run by:

```
    1. Enter virtual environment
    .\venv\Scripts\activate

    2. Run tracecat
    python tracecat.py

    3. Quit virtual environment
    .\venv\Scripts\deactivate
```

## Build Binary Distribution

You can also build tracecat into executables, so that it can simply run without any installations.

Build Windows release

```
.\build\build_win.bat           (run on Windows)
```

Build Linux release

```
source ./build/build_linux.sh   (run on Linux)
```

Build Mac release

```
source ./build/build_mac.sh     (run on MacOS)
```

Then you can get distribution package from:

```    
./build/dist/tracecat.zip
```

## User Guide

See <a href="docs/user_guide.md" target="_blank">docs/user_guide</a>

## Contact

Author: Cyrus Huang

Github: <https://github.com/kernel-cyrus/tracecat>
