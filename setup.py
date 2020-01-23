from setuptools import setup

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(name="TDebugger",
      version="0.2.3",
      packages=["TDebugger", "TDebugger.TestAlgos"],
      entry_points={"console_scripts": [
          "TDebugger = TDebugger.TDebugger:main"]},
      author="Jayesh Nirve",
      author_email="nitinnirve@gmail.com",
      description="A advanced python debugger with live tracing that outputs video logs of a program's execution.",
      long_description=long_description,
      long_description_content_type="text/markdown",
      url="https://github.com/CCExtractor/TDebugger",
      license="GPL-2.0",
      include_package_data=True,
      install_requires=['Pillow', 'opencv-python', 'numpy', 'pyyaml'],
      classifiers=[
          "Programming Language :: Python :: 3",
          "Programming Language :: Python :: 3.7",
      ],
      )
