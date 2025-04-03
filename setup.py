from setuptools import setup

setup(
    name="Fanography",
    packages=["fanography"],
    include_package_data=True,
    install_requires=[
        "flask",
        "pyyaml",
    ],
    data_files=[
        ("", "data.yml"),
        ("", "sections.yml"),
        ("", "delpezzo-surfaces.yml"),
        ("", "delpezzo-varieties.yml"),
    ],
)
