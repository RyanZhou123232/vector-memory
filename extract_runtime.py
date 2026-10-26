"""Extract cabinets from the verified Microsoft package for local diagnostics."""

from pathlib import Path
import struct
import subprocess
import shutil
import xml.etree.ElementTree as ET

root = Path(__file__).resolve().parent / ".runtime"
payload = (root / "vc_redist.x64.exe").read_bytes()
offset = 0
index = 0
while True:
    offset = payload.find(b"MSCF", offset)
    if offset < 0:
        break
    reserved, size = struct.unpack_from("<II", payload, offset + 4)
    if reserved == 0 and 36 <= size <= len(payload) - offset:
        cabinet = root / f"container_{index}.cab"
        cabinet.write_bytes(payload[offset:offset + size])
        output = root / f"container_{index}"
        output.mkdir(exist_ok=True)
        result = subprocess.run(["expand.exe", "-F:*", str(cabinet), str(output)],
                                capture_output=True, text=True)
        if result.returncode:
            raise RuntimeError(result.stderr or result.stdout)
        index += 1
    offset += 4

manifest = ET.parse(root / "container_0" / "0")
namespace = {"b": "http://schemas.microsoft.com/wix/2008/Burn"}
for item in manifest.findall("b:Payload", namespace):
    if item.attrib.get("FilePath", "").lower().endswith("vcruntimeminimum_amd64\\cab1.cab"):
        cabinet = root / "container_1" / item.attrib["SourcePath"]
        output = root / "dlls"
        output.mkdir(exist_ok=True)
        subprocess.run(["expand.exe", "-F:*", str(cabinet), str(output)], check=True,
                       capture_output=True)
        for dll in output.glob("*.dll_amd64"):
            target = output / dll.name.removesuffix("_amd64")
            if not target.exists() or target.read_bytes() != dll.read_bytes():
                try:
                    shutil.copyfile(dll, target)
                except PermissionError as exc:
                    raise RuntimeError("Close the memory app before updating local runtime DLLs.") from exc
        print("Extracted the x64 C++ runtime locally; no Windows files changed.")
        break
else:
    raise RuntimeError("The package format changed; x64 runtime cabinet not found.")
