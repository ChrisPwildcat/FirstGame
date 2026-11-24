from setuptools import setup, find_packages


setup(
    name='cp-game',
    version='0.1.0',
    description='Game experiments: a text adventure and Lineage, an evolution-driven civ prototype',
    author='Chris Powell',
    author_email='ccp5959@gmail.com',
    keywords='game cpgame engine pygame evolution domestication',
    packages=find_packages('src'),
    package_dir={"": "src"},
    python_requires='>=3.9',
    install_requires=['pygame-ce>=2.4'],
    entry_points={
        'console_scripts': [
            'cpgame = cp_game.main:main',
            'lineage = lineage.game:main',
        ]
    },
)
