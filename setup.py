
from setuptools import setup, find_packages

setup(
    name='hip_exo_ws',
    version='0.1',
    packages=find_packages(),  # Automatically finds all packages
    install_requires=[
        'numpy',
        'pyqtgraph',
        'pandas',
        'tqdm',
        'NeuroLocoMiddleware'
        # Add other dependencies here
    ],
    include_package_data=True,
    author='Huan Min',
    description='Admittance control with TMotor and real-time plotting',
)
