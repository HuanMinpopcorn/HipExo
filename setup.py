from setuptools import setup, find_packages

setup(
    name='hipexo',
    version='0.1.0',
    packages=find_packages(include=["TMotorCANControl", "TMotorCANControl.*",
                                     "NeuroLocoMiddleware", "NeuroLocoMiddleware.*"]),
    install_requires=[
    'numpy',
    ],

    entry_points={
        'console_scripts': [
            'hipexo=hipexo.main:main',
        ],
    },
    author='Your Name',
    description='High-level exoskeleton controller built on tmotor_control',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    classifiers=['Programming Language :: Python :: 3'],

)
