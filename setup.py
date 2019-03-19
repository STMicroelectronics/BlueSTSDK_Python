import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="blue_st_sdk",
    version="1.0.0",
    author="Davide Aliprandi",
    author_email="davide.aliprandi@gmail.com",
    description="Bluetooth abstraction API package",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/STMicroelectronics-CentralLabs/BlueSTSDK_Python",
    packages=setuptools.find_packages(),
    classifiers=[
        "License :: Other/Proprietary License",
        "Operating System :: POSIX :: Linux",
        "Programming Language :: Python :: 2.7",
        "Topic :: Software Development :: Embedded Systems"
    ],
)
