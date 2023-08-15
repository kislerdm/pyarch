# pyarch

The tool to generate dynamic [class diagrams](https://mermaid.js.org/syntax/classDiagram.html) of python packages to
facilitate their development and maintenance.

**Motivation**:

- Reduction of the cognitive load when learning the structure of a new package.
- Identification of architecture bottlenecks using static analysis of inter-modular dependencies.

## Demo

- [sklearn](https://www.dkisler.com/pyarch/sklearn)
- [SuperDuperDB](https://www.dkisler.com/pyarch/superduperdb)
- [Sanic](https://www.dkisler.com/pyarch/sanic)
- [FastAPI](https://www.dkisler.com/pyarch/fastapi)

## How to install

**Prerequisites**:

- python >= 3.8

**Steps**

1. Download the latest release of the python script
2. Move it to the bin directory `/usr/local/bin`
3. Run the script to validate the version:

```commandline
pyarch --version
```

_Note_ that sudo permissions will be required. Alternatively, the script can be executed without the `step 2`:

```commandline
python3 pyarch --version
```

**Demo**

_Note_ [curl](https://curl.se/) is required.

```commandline
sudo curl -SLo /usr/local/bin/pyarch https://github.com/kislerdm/pyarch/releases/download/v0.0.1/pyarch &&\
pyarch --version
```

Output:

```commandline
version: 0.0.1
```

## How to use

**Prerequisites**:

- pylint
- pyarch

Follow the steps to generate the webpage with dynamic architecture diagrams of [sklearn](https://scikit-learn.org/):

1. Create a clean directory

```commandline
mkdir sklearn-diagram && cd sklearn-diagram 
```

2. Clone sklearn from GitHub to the local repository:

```commandline
git clone git@github.com:scikit-learn/scikit-learn.git code
```

3. Generate the package architecture diagrams as UML
   using [pyreverse](https://pylint.readthedocs.io/en/latest/pyreverse.html)

```commandline
pyreverse -Akmy -o puml -d . --ignore=test,tests code/sklearn
```

4. Generate the webpage with the dynamic diagrams:

```commandline
pyarch -i . -o . -v --title="sklearn architecture" --header="sklearn architecture"
```

The directory is expected to have the following structure:

```commandline
.
├── code
├── classes.puml
├── packages.puml
└── index.html
```

Open `index.html` using a web-browser:

<img src="sklearn-demo.png" alt="sklearn-demo" width="100%" style="border:2px solid #000">

## Distribution and contribution

The project is distributed under the MIT license - feel free to use it as you will.

Please open github issue, and/or PR with a change proposal to collaborate.
