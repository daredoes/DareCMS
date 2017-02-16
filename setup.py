from setuptools import setup

exec(open('darecms/_version.py').read())
if __name__ == '__main__':
    setup(
        name='darecms',
        packages=['darecms'],
        version=__version__,
        author='Daniel Evans',
        author_email='me@danielarevans.com',
        description='The Sideboard CMS',
        url='https://github.com/migetman9/darecms',
        install_requires=open('requirements.txt').readlines()
    )
