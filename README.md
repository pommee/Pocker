<p align="center">
  <img src="./resources/pocker-name.png" />
</p>

---

![image](./resources/image.png)

# Pocker

I found Docker Desktop to be bloated, heavy, slow, resource-hogging and contains features that I rarely ever use.  
Not to say that it's bad; just not for me.

# 👋🏼 Introduction

Pocker is a lightweight CLI tool to help with docker related tasks. For example,

- View containers/images.
- See logs and attributes.
- Manage status of containers.

The tool is heavily based on [docker-py](https://docker-py.readthedocs.io/en/stable/index.html) and [textual](https://github.com/textualize/textual/).  
A big thanks goes over to the creator and contributors of textual as it makes for a very sleek and easy interface.

[!["Buy Me A Coffee"](https://www.buymeacoffee.com/assets/img/custom_images/orange_img.png)](https://buymeacoffee.com/pommee)

## 🤏🏼 Prerequisite

> [!NOTE]
> Pipx must be installed.

```shell
pip install pipx
```

## 📦 Installation

### Install latest version from remote repository

```shell
pipx install git+https://github.com/pommee/Pocker@main
```

### Install from local repository

```bash
git clone https://github.com/pommee/Pocker.git
cd Pocker
pipx install .
```

## 🚦 Usage

```shell
pocker          # Start pocker
pocker update   # Fetch and install latest version
```

Keybinds can be seen in the footer when started or by pressing `?` to display help modal.

## 🔧 Configuration

Configuration can be done in [config.yaml](https://github.com/pommee/Pocker/blob/main/config.yaml).

| Key              | Default | Info                                                                                                                                  |
| ---------------- | ------- | ------------------------------------------------------------------------------------------------------------------------------------- |
| log_tail         | 2000    | At **startup**, Pocker will fetch `log_tail` amount of container logs.<br> Not recommended to exceed ~3000 as startup will slow down. |
| start_fullscreen | False   | Display container logs in fullscreen mode at startup.                                                                                 |
| start_scroll     | True    | Automatic scroll when new logs are fetched.                                                                                           |
| start_wrap       | False   | Wrap logs to fit content window.                                                                                                      |
