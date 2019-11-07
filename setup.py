import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="lib_sc2", # Replace with your own username
    version="0.0.1",
    author="Renyu Liu",
    author_email="liury728@gmail.com",
    description="A library to enhance original sc2 package",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/derpypony/python_sc2_lib",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: Windows 10",
    ],
    python_requires='>=3.7',
)
