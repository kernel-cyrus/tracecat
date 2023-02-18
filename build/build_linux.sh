#!/bin/bash

if ! command -v ndk-build &> /dev/null
then
    echo "ERROR: ndk-build not found, please install android NDK first."
    return
fi

if ! [ -f "./venv/bin/activate" ]; then
    echo "ERROR: Please run build from tracecat root path."
    return
fi

(cd demon; ndk-build clean; ndk-build)

if ! [ -f "./demon/obj/local/arm64-v8a/tracecatd" ]; then
    echo "ERROR: tracecatd build failed, please check the errors."
    return
fi

source ./venv/bin/activate

rm -rf ./build/build

rm -rf ./build/dist

pyinstaller ./build/spec/tracecat_mac_dir.spec --workpath="./build/build/" --distpath="./build/dist/"

pyinstaller ./scripts/run_all.py --specpath="./build/build/" --workpath="./build/build/" --distpath="./build/dist/"

cp -rf ./build/dist/run_all/* ./build/dist/tracecat/

tar -zcvf ./build/dist/tracecat.tar.gz -C ./build/dist/ tracecat/

deactivate