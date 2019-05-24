import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="blue_st_sdk",
    version="1.2.1",
    author="Davide Aliprandi",
    author_email="davide.aliprandi@gmail.com",
    description="Bluetooth Low Energy abstraction library package.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/STMicroelectronics/BlueSTSDK_Python",
    packages=setuptools.find_packages(),
    license='BSD 3-clause',
    classifiers=[
        "License :: OSI Approved :: BSD License",
        "Operating System :: POSIX :: Linux",
        "Programming Language :: Python :: 2.7",
        "Topic :: Software Development :: Embedded Systems"
    ],
)
