import setuptools

with open("README.md", "r") as fh:
        long_description = fh.read()

        setuptools.setup(
            name="blue_st_sdk",
            version="1.0.0",
            author="Davide Aliprandi",
            author_email="davide.aliprandi@st.com",
            description="Bluetooth abstraction API package",
            long_description=long_description,
            long_description_content_type="text/markdown",
            url="https://github.com/STMicroelectronics-CentralLabs/BlueSTSDK_Python",
            packages=setuptools.find_packages(),
            classifiers=[
                        "Programming Language :: Python :: 2.7",
                        "License :: \
                        COPYRIGHT(c) 2018 STMicroelectronics \
                        \
                        Redistribution and use in source and binary forms, with or without \
                        modification, are permitted provided that the following conditions are met: \
                          1. Redistributions of source code must retain the above copyright notice, \
                             this list of conditions and the following disclaimer. \
                          2. Redistributions in binary form must reproduce the above copyright \
                             notice, this list of conditions and the following disclaimer in the \
                             documentation and/or other materials provided with the distribution. \
                          3. Neither the name of STMicroelectronics nor the names of its \
                             contributors may be used to endorse or promote products derived from \
                             this software without specific prior written permission. \
                        \
                        THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS \"AS IS\" \
                        AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE \
                        IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE \
                        ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE \
                        LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR \
                        CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF \
                        SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS  \
                        INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN \
                        CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) \
                        ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE \
                        POSSIBILITY OF SUCH DAMAGE. \
                        ",
                        "Operating System :: Linux",
                        ],
        )
