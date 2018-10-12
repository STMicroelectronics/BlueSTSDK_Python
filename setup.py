import setuptools

with open("README.md", "r") as fh:
        long_description = fh.read()

        setuptools.setup(
            name="blue_st_sdk_package",
            version="0.0.1",
            author="Davide Aliprandi",
            author_email="davide.aliprandi@st.com",
            description="Bluetooth abstraction API package",
            long_description=long_description,
            long_description_content_type="text/markdown",
            url="https://github.com/STMicroelectronics-CentralLabs/BlueSTSDK_Python",
            packages=setuptools.find_packages(),
            classifiers=[
                        "Programming Language :: Python :: 2.7",
                        "License :: Open Source",
                        "Operating System :: OS Independent",
                        ],
        )
