from setuptools import setup


setup(
    name="compiler-lc3",
    version="0.1.0",
    description="A small C-subset to LC-3 compiler",
    packages=["compiler_lc3"],
    entry_points={
        "console_scripts": [
            "compiler-lc3=compiler_lc3.__main__:main",
        ]
    },
)
