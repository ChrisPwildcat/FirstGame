from setuptools import setup, find_packages


setup(
    name='cp-game',
    version='0.0.1',
    description='Game for learning python',
    author='Chris Powell',
    author_email='ccp5959@gmail.com',
    keywords='game cpgame engine pygame',
    packages=find_packages('src'),
    package_dir={"": "src"},
    install_requires=[],
    entry_points={
        'console_scripts': ['cpgame = cp_game.main:main']
    },
)
