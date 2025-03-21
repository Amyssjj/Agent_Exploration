from setuptools import setup, find_packages

setup(
    name="langfun-apps",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "langfun>=0.1.0",
        "pyglove>=0.4.0",
        "openai>=1.0.0",
        "notion-client>=1.0.0",
        "anthropic>=0.3.0",
        "pandas>=1.5.0",
        "numpy>=1.23.0",
        "jupyter>=1.0.0",
        "ipython>=8.0.0",
        "python-dotenv>=1.0.0",
    ],
    python_requires=">=3.9",
    description="Applications built with langfun framework",
    author="Your Name",
    author_email="your.email@example.com",
    url="https://github.com/yourusername/langfun-apps",
)