<p align="center">
  <img src="https://github.com/pommee/Pocker/blob/main/resources/pocker-name.png?raw=true" />
  <table>
    <tr>
        <td>
            <img width="100%" src="https://github.com/pommee/Pocker/blob/main/resources/home-preview.png?raw=true">
        </td>
        <td>
            <img width="100%" src="https://github.com/pommee/Pocker/blob/main/resources/search-logs.png?raw=true">
        </td>
    </tr>
    <tr>
        <td>
            <img width="100%" src="https://github.com/pommee/Pocker/blob/main/resources/shell-preview.png?raw=true">
        </td>
        <td>
            <img width="100%" src="https://github.com/pommee/Pocker/blob/main/resources/help-screen-preview.png?raw=true">
        </td>
    </tr>
  </table>
</p>

# 👋🏼 Introduction

Pocker is a TUI tool to help with docker related tasks. For example,

- View containers/images.
- Manage status of containers.
- See logs, attributes, environment variables and container statistics.
- Filter logs based on keywords.
- Start shell inside a container.

The tool is heavily based on [docker-py](https://docker-py.readthedocs.io/en/stable/index.html) and [textual](https://github.com/textualize/textual/).  
A big thanks goes over to the creator and contributors of textual as it makes for a very sleek and easy interface.

[!["Buy Me A Coffee"](https://www.buymeacoffee.com/assets/img/custom_images/orange_img.png)](https://buymeacoffee.com/pommee)

## 🤏🏼 Prerequisite

> [!NOTE]
> [Pipx](https://pipx.pypa.io/stable/installation/) must be installed.  
> Python version 3.10.9 or newer.

## 📦 Installation

Pocker is hosted at PyPi ([see here](https://pypi.org/project/pocker-tui/)).


```shell
pipx install pocker-tui           # Latest version
pipx install pocker-tui==version  # Specific version
```

### Install from GitHub repository

PyPi will mostly contain newest version, but it is also possible to run install from this repository.

```bash
pipx install git+https://github.com/pommee/Pocker
```

## 🚦 Usage

```shell
pocker          # Start pocker
pocker update   # Fetch and install latest version
```

Keybinds can be seen in the footer when started or by pressing `?` to display help modal.

## 🔧 Configuration

Upon the first startup, a configuration file will be generated and stored at `$HOME/.config/pocker/config.yaml`.

| Key                 | Default | Info                                                                                                                                  |
| ------------------- | ------- | ------------------------------------------------------------------------------------------------------------------------------------- |
| log_tail            | 2000    | At **startup**, Pocker will fetch `log_tail` amount of container logs.<br> Not recommended to exceed ~3000 as startup will slow down. |
| max_log_lines       | 2000    | The displayed container logs are shown sequentially, with the oldest log being removed as a new one appears.                          |
| show_all_containers | false   | Show running and exited containers.                                                                                                   |
| start_fullscreen    | false   | Display container logs in fullscreen mode at startup.                                                                                 |
| start_scroll        | true    | Automatically scrolls when new logs are fetched.                                                                                      |
| start_wrap          | false   | When enabled, logs will wrap to fit the content window.                                                                               |

### Keymap [default]

| Key   | Action        | Description                                                                      |
| ----- | ------------- | -------------------------------------------------------------------------------- |
| `q`   | Quit          | Exits the application.                                                           |
| `l`   | Logs          | Opens the logs view to display log entries.                                      |
| `/`   | Search        | Search logs.                                                                     |
| `TAB` | Cycle widgets | Used to cycle widgets. Newly focused widget will have it's borders alter colors. |
| `a`   | Attributes    | Displays the attributes panel, showing various item attributes.                  |
| `e`   | Environment   | Opens the environment settings view.                                             |
| `d`   | Statistics    | Shows statistical information related to the container.                          |
| `v`   | Shell         | Creates a shell for the current container.                                       |
| `f`   | Fullscreen    | Toggles fullscreen mode for the logs view.                                       |
| `w`   | Wrap Logs     | Toggles log wrapping in the logs view.                                           |
| `s`   | Toggle Scroll | Toggles scrolling mode for the current view.                                     |

This table helps you understand the functionalities assigned to each key, making navigation and operation more efficient.

### Errors

Errors will be displayed whenever encountered.

![keybind-error](https://github.com/pommee/Pocker/blob/main/resources/keybind-error.png?raw=true)

> Example of faulty keybind for `Shell`; in this case the key does not exist in the config.
