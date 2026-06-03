from __future__ import annotations

import platform
import shutil
import subprocess
import sys
import tarfile
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
DIST_DIR = ROOT / "dist"
BUILD_DIR = ROOT / "build" / "release"
PYI_DIST = BUILD_DIR / "pyinstaller-dist"
PYI_WORK = BUILD_DIR / "pyinstaller-work"
def run(cmd: list[str], *, cwd: Path) -> None:
    subprocess.run(cmd, cwd=cwd, check=True)


def release_name() -> str:
    system = platform.system().lower()
    machine = platform.machine().lower()
    return f"compiler-lc3-{system}-{machine}"


def exe_name() -> str:
    return "compiler-lc3.exe" if platform.system().lower() == "windows" else "compiler-lc3"


def clean() -> None:
    shutil.rmtree(BUILD_DIR, ignore_errors=True)
    BUILD_DIR.mkdir(parents=True, exist_ok=True)
    DIST_DIR.mkdir(parents=True, exist_ok=True)


def build_executable() -> Path:
    run(
        [
            sys.executable,
            "-m",
            "PyInstaller",
            "--noconfirm",
            "--clean",
            "--onedir",
            "--name",
            "compiler-lc3",
            "--distpath",
            str(PYI_DIST),
            "--workpath",
            str(PYI_WORK),
            "--specpath",
            str(BUILD_DIR),
            "scripts/pyinstaller_entry.py",
        ],
        cwd=ROOT,
    )
    return PYI_DIST / "compiler-lc3"


def assemble_release(exe_dir: Path) -> Path:
    target = DIST_DIR / release_name()
    shutil.rmtree(target, ignore_errors=True)
    (target / "bin").mkdir(parents=True)
    (target / "docs").mkdir(parents=True)
    (target / "examples").mkdir(parents=True)

    shutil.copytree(exe_dir / "_internal", target / "bin" / "_internal")
    shutil.copy2(exe_dir / exe_name(), target / "bin" / exe_name())
    shutil.copy2(ROOT / "README.md", target / "docs" / "lc3说明书.md")
    if (ROOT / "examples").exists():
        for item in (ROOT / "examples").iterdir():
            if item.is_file():
                shutil.copy2(item, target / "examples" / item.name)

    readme = target / "README.md"
    readme.write_text(
        "\n".join(
            [
                "# compiler-lc3 Portable Release",
                "",
                "这是 `compiler-lc3` 的免安装发行版。",
                "",
                "## 使用方式",
                "",
                "1. 解压压缩包。",
                "2. 将 `bin/` 目录加入环境变量 `PATH`。",
                f"3. 直接运行 `{exe_name()}`。",
                "",
                "示例：",
                "",
                "```bash",
                f"{exe_name()} input.c -o output.asm",
                f"{exe_name()} input.c -o output.asm -d",
                f"{exe_name()} input.c -o output.asm --beginner-style",
                "```",
                "",
                "## 目录说明",
                "",
                f"- `bin/{exe_name()}`：编译器可执行文件",
                "- `examples/`：示例输入程序",
                "- `docs/lc3说明书.md`：当前语言子集、输出模式、测试方式和不支持特性的说明",
                "",
                "## 说明",
                "",
                "- 该发行版已自带 Python 运行时，目标机无需额外安装 Python。",
                "- 本发行版用于把项目支持的 C 语言子集编译为 LC-3 汇编。",
                "- 当前支持 `int`、`char`、`bool`、基础指针、局部数组、短路逻辑、乘除模和常见控制流。",
                "- `-d` 会生成带注释的汇编，`--beginner-style` 会生成更接近初学者手写风格的汇编。",
                "",
                "## 输入与输出",
                "",
                "- 输入：C 子集源文件",
                "- 输出：LC-3 汇编文件（`.asm`）",
                "",
                "完整语言特性和限制见 `docs/lc3说明书.md`。",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    note = target / "docs" / "RELEASE.txt"
    note.write_text(
        "\n".join(
            [
                f"Release: {target.name}",
                "Usage:",
                "  1. Add the bin/ directory to PATH.",
                "  2. Run: compiler-lc3 input.c -o output.asm",
                "  3. Optional flags: -d, --beginner-style",
                "",
                "This portable release bundles the Python runtime for the compiler itself.",
                "LC-3 assembler/simulator binaries are not bundled in this release package.",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    return target


def make_archive(release_dir: Path) -> Path:
    if platform.system().lower() == "windows":
        archive = DIST_DIR / f"{release_dir.name}.zip"
        if archive.exists():
            archive.unlink()
        with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED) as zf:
            for path in release_dir.rglob("*"):
                zf.write(path, path.relative_to(release_dir.parent))
        return archive

    archive = DIST_DIR / f"{release_dir.name}.tar.gz"
    if archive.exists():
        archive.unlink()
    with tarfile.open(archive, "w:gz") as tar:
        tar.add(release_dir, arcname=release_dir.name)
    return archive


def verify_release(release_dir: Path) -> None:
    compiler = release_dir / "bin" / exe_name()
    out_asm = BUILD_DIR / "verify.asm"
    run([str(compiler), "tests/cases/puts_putchar.c", "-o", str(out_asm), "-d"], cwd=ROOT)


def main() -> None:
    clean()
    exe_dir = build_executable()
    release_dir = assemble_release(exe_dir)
    verify_release(release_dir)
    archive = make_archive(release_dir)
    print(release_dir)
    print(archive)


if __name__ == "__main__":
    main()
