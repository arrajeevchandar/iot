"""Exercise the exact MCU inference wrapper/kernels on the host CPU (not a hardware test)."""
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import subprocess

ROOT=Path(__file__).resolve().parents[1]
LIB=ROOT/".pio/libdeps/esp32dev/Chirale_TensorFLowLite/src"
if not LIB.exists():
    LIB=ROOT.parent/"esp32-build/Chirale/src"
if not LIB.exists():
    raise SystemExit("Install firmware dependencies first.")
OUT=ROOT/"runtime/tflm-native"
OUT.mkdir(parents=True,exist_ok=True)
micro=LIB/"tensorflow/lite/micro"
sources=[]
for folder in ["tensorflow/lite/core/api","tensorflow/lite/core/c","tensorflow/lite/kernels/internal","tensorflow/lite/kernels/internal/reference","tensorflow/lite/schema"]:
    sources.extend((LIB/folder).glob("*.cpp"))
sources.append(LIB/"tensorflow/lite/kernels/kernel_util.cpp")
sources.extend(p for p in micro.glob("*.cpp") if not p.name.startswith(("all_ops", "test", "mock", "fake", "system_setup")))
for folder in ["arena_allocator","memory_planner","tflite_bridge"]:
    sources.extend((micro/folder).glob("*.cpp"))
for name in ["kernel_util.cpp","fully_connected_common.cpp","softmax_common.cpp","micro_tensor_utils.cpp","cmsis_nn/fully_connected.cpp","cmsis_nn/softmax.cpp"]:
    sources.append(micro/"kernels"/name)
sources.extend((LIB/"third_party/cmsis_nn/Source").rglob("*.c"))
sources.extend([ROOT/"firmware/src/tinyml_manager.cpp",ROOT/"tests/tflm_native.cpp"])
def compile_one(source):
    obj=OUT/(str(source.relative_to(LIB) if source.is_relative_to(LIB) else source.relative_to(ROOT)).replace("/","_")+".o")
    if not source.is_relative_to(LIB) or not obj.exists() or obj.stat().st_mtime<max(source.stat().st_mtime,Path(__file__).stat().st_mtime):
        cpp=source.suffix==".cpp"
        command=["g++" if cpp else "gcc", "-O1", "-ffunction-sections", "-fdata-sections", "-DARDUINO", "-DCLASSROOM_NATIVE_TEST", "-DTF_LITE_USE_CTIME", "-I"+str(LIB), "-I"+str(ROOT/"firmware/include")]
        if cpp: command.append("-std=c++17")
        subprocess.run(command+["-c",str(source),"-o",str(obj)],check=True)
    return str(obj)
with ThreadPoolExecutor(max_workers=4) as pool:
    objects=list(pool.map(compile_one,sources))
binary=OUT/"test-tflm"
subprocess.run(["g++","-Wl,--gc-sections",*objects,"-o",str(binary)],check=True)
subprocess.run([str(binary)],check=True)
