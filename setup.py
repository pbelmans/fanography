from setuptools import setup

setup(
    name="Fanography",
    packages=["fanography"],
    include_package_data=True,
    install_requires=[
      "flask",
      "yaml",
    ],
)
