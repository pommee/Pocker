
![image](./resources/image.png)

# Pocker

I found Docker Desktop to be bloated, heavy, slow, resource-hogging and contains features that I rarely ever use.  
Not to say that it's bad; just not for me.

# Introduction

Pocker is a lightweight CLI tool to help with docker related tasks. For example,

* View containers/images.
* See logs and attributes.
* Manage status of containers.

The tool is heavily based on [docker-py](https://docker-py.readthedocs.io/en/stable/index.html) and [textual](https://github.com/textualize/textual/).  
A big thanks goes over to the creator and contributors of textual as it makes for a very sleek and easy interface.

## Prerequisite

> [!NOTE] 
> Pipx must be installed.

```shell
pip install pipx
```

## Installation

### Install from remote repository

This will install latest version available from main.
```shell
pipx install git+https://github.com/pommee/Pocker@main
```

### Install from local repository
```bash
git clone https://github.com/pommee/Pocker.git
cd Pocker
pipx install . 
```

## Usage

Start by running

```shell
pocker
```

Keybinds can be seen in the footer when started or by pressing `?`.