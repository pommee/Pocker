## [1.18.4](https://github.com/pommee/Pocker/compare/v1.18.3...v1.18.4) (2025-03-16)


### Bug Fixes

* use pywinpty for windows ([72343c4](https://github.com/pommee/Pocker/commit/72343c4fb7946edb04626ff8ada6b10c06534785))

## [1.18.3](https://github.com/pommee/Pocker/compare/v1.18.2...v1.18.3) (2025-03-16)


### Bug Fixes

* better error message if docker daemon is not running or unavailable ([edd905b](https://github.com/pommee/Pocker/commit/edd905b654b246bf606c6e7c9b37896c938a07d4))

## [1.18.2](https://github.com/pommee/Pocker/compare/v1.18.1...v1.18.2) (2025-03-14)


### Bug Fixes

* move termios to local import to hopefully solve windows build ([460b3ee](https://github.com/pommee/Pocker/commit/460b3eedc50c6a5a27088962e28a3ff42fabb357))

## [1.18.1](https://github.com/pommee/Pocker/compare/v1.18.0...v1.18.1) (2025-03-11)


### Bug Fixes

* move fcntl import ([0577ab4](https://github.com/pommee/Pocker/commit/0577ab46f36429a90a8f630024df5d23f6f8af89))

# [1.18.0](https://github.com/pommee/Pocker/compare/v1.17.5...v1.18.0) (2025-02-08)


### Bug Fixes

* added 'up' and 'down' keys to container shell ([07f4bd5](https://github.com/pommee/Pocker/commit/07f4bd5e3aee1f0ec9baeb948888043fa511f753))
* height of one for listitem after textual upgrade ([a22ab22](https://github.com/pommee/Pocker/commit/a22ab229a7e575190a215216458e28506c0399eb))
* prevent double jump when cycling containers ([f668f8a](https://github.com/pommee/Pocker/commit/f668f8a8c20a2a8397f90118a2c13596df206387))
* prevent error when fetching status ([ff380f6](https://github.com/pommee/Pocker/commit/ff380f60897a117716cc839b4504fc3286cbde67))


### Features

* trigger new release ([ba60774](https://github.com/pommee/Pocker/commit/ba6077492546ff3e05f9400758c1753df9322a0b))

## [1.17.5](https://github.com/pommee/Pocker/compare/v1.17.4...v1.17.5) (2025-01-31)


### Bug Fixes

* parallel container and image fetch ([b30ceec](https://github.com/pommee/Pocker/commit/b30ceec24bb4c3976a579c3274c3e7ec1169fef8))

## [1.17.4](https://github.com/pommee/Pocker/compare/v1.17.3...v1.17.4) (2025-01-31)


### Bug Fixes

* ensure buttons are hidden when containers are not maximized ([9494ef0](https://github.com/pommee/Pocker/commit/9494ef0f6d756f4a74037efccfaa6cbcc2c85da7))

## [1.17.3](https://github.com/pommee/Pocker/compare/v1.17.2...v1.17.3) (2024-11-29)


### Bug Fixes

* revert dependency upgrades ([f0921de](https://github.com/pommee/Pocker/commit/f0921de0467abec66d247d6a4bf718fe28f999db))

## [1.17.2](https://github.com/pommee/Pocker/compare/v1.17.1...v1.17.2) (2024-11-29)


### Bug Fixes

* improve container shell ([b641585](https://github.com/pommee/Pocker/commit/b6415853894d9758023011c16999b271072d2e0d))
* respect log_tail config when started ([523708b](https://github.com/pommee/Pocker/commit/523708b8d57e9b612f47a00de71cc463c87b3f1c))

## [1.17.1](https://github.com/pommee/Pocker/compare/v1.17.0...v1.17.1) (2024-09-02)


### Bug Fixes

* fix bug where instance of screens crashes the application ([5333633](https://github.com/pommee/Pocker/commit/53336330e78d957e6011aa15bb13dd492e601a68))

# [1.17.0](https://github.com/pommee/Pocker/compare/v1.16.0...v1.17.0) (2024-08-30)


### Features

* fix exception when clicking statistics with mouse. textual dep updated ([9dec04c](https://github.com/pommee/Pocker/commit/9dec04c71384243c6aae5e007ad634b5c1d3a4b9))

# [1.16.0](https://github.com/pommee/Pocker/compare/v1.15.0...v1.16.0) (2024-08-27)


### Features

* separate plots for cpu and memory ([c4f6879](https://github.com/pommee/Pocker/commit/c4f6879180c6b7de1192dddc278ef2d6ca2da548))

# [1.15.0](https://github.com/pommee/Pocker/compare/v1.14.3...v1.15.0) (2024-08-26)


### Features

* added plot for cpu and memory in statistics pane ([8e21518](https://github.com/pommee/Pocker/commit/8e2151896cc03e47f929f3b13ae5a2e6ab2c7d92))

## [1.14.3](https://github.com/pommee/Pocker/compare/v1.14.2...v1.14.3) (2024-08-22)


### Bug Fixes

* prevent duplicated logs when using keybinds ([016deb6](https://github.com/pommee/Pocker/commit/016deb661cce3cfa3c287a36b5c50824162a7122))
* update command now installs via pipx ([b9a272d](https://github.com/pommee/Pocker/commit/b9a272da8e4d64ec7ae4129a5803e890acb68a2c))

## [1.14.2](https://github.com/pommee/Pocker/compare/v1.14.1...v1.14.2) (2024-08-22)


### Bug Fixes

* prevent duplicated logs ([dc213aa](https://github.com/pommee/Pocker/commit/dc213aa980495f3a6dfa3755c1d74b5ef6c193b2))

## [1.14.1](https://github.com/pommee/Pocker/compare/v1.14.0...v1.14.1) (2024-08-20)


### Bug Fixes

* correct styling when minimizing containers and images ([aabaa83](https://github.com/pommee/Pocker/commit/aabaa83318238a7ee3a452f6f323814a1c57061f))

# [1.14.0](https://github.com/pommee/Pocker/compare/v1.13.1...v1.14.0) (2024-08-20)


### Features

* controls for containers when 'containerns-and-images' are in expanded view ([cf41cef](https://github.com/pommee/Pocker/commit/cf41cef11f5ecbf8573558c5bbcc67fe70262db7))

## [1.13.1](https://github.com/pommee/Pocker/compare/v1.13.0...v1.13.1) (2024-08-19)


### Bug Fixes

* fix not able to open settings and help panes ([13ea0e7](https://github.com/pommee/Pocker/commit/13ea0e728b6b1ef7a6fa4ca4a56af6cd07e4aa55))

# [1.13.0](https://github.com/pommee/Pocker/compare/v1.12.5...v1.13.0) (2024-08-19)


### Features

* fullscreen containers and images view ([c878344](https://github.com/pommee/Pocker/commit/c878344f473563f9c20a209ef33a266595fe6889))

## [1.12.5](https://github.com/pommee/Pocker/compare/v1.12.4...v1.12.5) (2024-08-19)


### Bug Fixes

* update active tab content when container switched ([46277b9](https://github.com/pommee/Pocker/commit/46277b9c91da62bc986671b39659bbffa7360309))

## [1.12.4](https://github.com/pommee/Pocker/compare/v1.12.3...v1.12.4) (2024-08-19)


### Bug Fixes

* search now works in all tabs, except for shell ([7c58e61](https://github.com/pommee/Pocker/commit/7c58e613b9d40f7e1693fd3fba65bc21eef8b3ff))

## [1.12.3](https://github.com/pommee/Pocker/compare/v1.12.2...v1.12.3) (2024-08-16)


### Bug Fixes

* read and apply config on startup. stream logs instead of polling ([b55b724](https://github.com/pommee/Pocker/commit/b55b724d2efa4d1879953c2a1bc25aff409b27bb))

## [1.12.2](https://github.com/pommee/Pocker/compare/v1.12.1...v1.12.2) (2024-08-16)


### Bug Fixes

* make 'search log' not skip lines ([768b7c4](https://github.com/pommee/Pocker/commit/768b7c4bf63559b52f98d9df6b668b338ccbc79a))

## [1.12.1](https://github.com/pommee/Pocker/compare/v1.12.0...v1.12.1) (2024-08-16)


### Bug Fixes

* new error modal when no containers are available ([a8e30d9](https://github.com/pommee/Pocker/commit/a8e30d95e01afcc448d2e88573167bd522e548c5))

# [1.12.0](https://github.com/pommee/Pocker/compare/v1.11.6...v1.12.0) (2024-08-16)


### Features

* added windows support ([9df0129](https://github.com/pommee/Pocker/commit/9df012948959f65c199b486622235226738689f7))

## [1.11.6](https://github.com/pommee/Pocker/compare/v1.11.5...v1.11.6) (2024-08-13)


### Bug Fixes

* remove margin for more widget space ([2760214](https://github.com/pommee/Pocker/commit/2760214dd050555063817833667a7c0f3a87f06c))

## [1.11.5](https://github.com/pommee/Pocker/compare/v1.11.4...v1.11.5) (2024-08-13)


### Bug Fixes

* fix container statistics work when switching containers ([8315b77](https://github.com/pommee/Pocker/commit/8315b77c0d452a9eff2c4aa2808c3e5d76b917b1))

## [1.11.4](https://github.com/pommee/Pocker/compare/v1.11.3...v1.11.4) (2024-08-13)


### Bug Fixes

* restore 'q' ([11b5a04](https://github.com/pommee/Pocker/commit/11b5a04eec69840e7c0a2c024f5c4a642456c070))

## [1.11.3](https://github.com/pommee/Pocker/compare/v1.11.2...v1.11.3) (2024-08-12)


### Bug Fixes

* add newly started container to manager list ([c705981](https://github.com/pommee/Pocker/commit/c7059812a437f119bc9a033e1a5f5df65b2061ce))

## [1.11.2](https://github.com/pommee/Pocker/compare/v1.11.1...v1.11.2) (2024-08-12)


### Bug Fixes

* daemon thread to respect ctrl+c ([681be21](https://github.com/pommee/Pocker/commit/681be21809eeb94c399031c206755b63ea06a3a5))

## [1.11.1](https://github.com/pommee/Pocker/compare/v1.11.0...v1.11.1) (2024-08-12)


### Bug Fixes

* make container state more reliable and reflect in ui ([99c655c](https://github.com/pommee/Pocker/commit/99c655cf198d859f5f4e52672b82ce2e3ad97f98))

# [1.11.0](https://github.com/pommee/Pocker/compare/v1.10.0...v1.11.0) (2024-08-08)


### Features

* cycle widget color feedback ([c024ef4](https://github.com/pommee/Pocker/commit/c024ef45e02db9886f5135478edda94d65c75cb5))

# [1.10.0](https://github.com/pommee/Pocker/compare/v1.9.0...v1.10.0) (2024-08-08)


### Features

* cycle containers using arrows ([156a9ec](https://github.com/pommee/Pocker/commit/156a9ec6f2e55a90788939b99a19cb48deea70cc))

# [1.9.0](https://github.com/pommee/Pocker/compare/v1.8.1...v1.9.0) (2024-07-19)


### Features

* added settings page ([6ae211c](https://github.com/pommee/Pocker/commit/6ae211c206f8537093f855681efd3fdb00ffddab))

## [1.8.1](https://github.com/pommee/Pocker/compare/v1.8.0...v1.8.1) (2024-07-17)


### Bug Fixes

* respect case-sensitive when searching logs ([a88c854](https://github.com/pommee/Pocker/commit/a88c854a293e1e404263d8733898150794a2e61a))

# [1.8.0](https://github.com/pommee/Pocker/compare/v1.7.1...v1.8.0) (2024-07-17)


### Features

* add highlighting for keyword when searching ([a619be0](https://github.com/pommee/Pocker/commit/a619be035615be2b858fbad297ac7c7cd4a1ccb5))

## [1.7.1](https://github.com/pommee/Pocker/compare/v1.7.0...v1.7.1) (2024-07-14)


### Bug Fixes

* remove duplicated logs and double reinitialization ([2e29927](https://github.com/pommee/Pocker/commit/2e2992711774da172c644be970e333a0c1f8bdc8))

# [1.7.0](https://github.com/pommee/Pocker/compare/v1.6.5...v1.7.0) (2024-07-11)


### Features

* added case-sensitive switch when searching logs ([af1c862](https://github.com/pommee/Pocker/commit/af1c86213bcb774351500b3a9c98aa5f850162e9))

## [1.6.5](https://github.com/pommee/Pocker/compare/v1.6.4...v1.6.5) (2024-07-11)


### Bug Fixes

* fix bug when clicking other container in list ([f53d534](https://github.com/pommee/Pocker/commit/f53d534ef44c01e93c19bd2c5f2d1103da8e5bfc))

## [1.6.4](https://github.com/pommee/Pocker/compare/v1.6.3...v1.6.4) (2024-07-10)


### Bug Fixes

* show error if no containers are found at startup ([2c5f924](https://github.com/pommee/Pocker/commit/2c5f924a071c3dc4dfc9bb7e42a6d1faa38e60e3))

## [1.6.3](https://github.com/pommee/Pocker/compare/v1.6.2...v1.6.3) (2024-07-10)


### Bug Fixes

* added 'show_all_containers' ([638044c](https://github.com/pommee/Pocker/commit/638044cac6fabbbdea57b766367cab89ac37fb42))

## [1.6.2](https://github.com/pommee/Pocker/compare/v1.6.1...v1.6.2) (2024-07-10)


### Bug Fixes

* improve 'search logs' performance ([3dc8cdf](https://github.com/pommee/Pocker/commit/3dc8cdfda31a4e3565715fc9d4f31b7ac2aa521c))

## [1.6.1](https://github.com/pommee/Pocker/compare/v1.6.0...v1.6.1) (2024-06-23)


### Bug Fixes

* ensure config directory exists when creating config file ([7951248](https://github.com/pommee/Pocker/commit/7951248fb328f6dddd28df0c255fb7d26293d2f5))

# [1.6.0](https://github.com/pommee/Pocker/compare/v1.5.1...v1.6.0) (2024-06-23)


### Features

* added shell for container ([13ed545](https://github.com/pommee/Pocker/commit/13ed545f63e35d4fbcaa0847acfbed22d8bceca7))

## [1.5.1](https://github.com/pommee/Pocker/compare/v1.5.0...v1.5.1) (2024-06-23)


### Bug Fixes

* bug where clicking env tab did not display ([9590eea](https://github.com/pommee/Pocker/commit/9590eea1263312a4ef5b2c6f3d4ef16473ad0774))

# [1.5.0](https://github.com/pommee/Pocker/compare/v1.4.0...v1.5.0) (2024-06-23)


### Features

* added custom keybinds to config ([e7f640f](https://github.com/pommee/Pocker/commit/e7f640f78625cee724181c3e0f18c0ecaedfd177))

# [1.4.0](https://github.com/pommee/Pocker/compare/v1.3.6...v1.4.0) (2024-06-22)


### Features

* added view tabs ([1d0b029](https://github.com/pommee/Pocker/commit/1d0b029af937714f4695f4c8a83c2be461ad67e6))

## [1.3.6](https://github.com/pommee/Pocker/compare/v1.3.5...v1.3.6) (2024-06-19)


### Bug Fixes

* performance improvements ([82583a1](https://github.com/pommee/Pocker/commit/82583a1a8be955fff7584a3689f5fa51a2894860))

## [1.3.5](https://github.com/pommee/Pocker/compare/v1.3.4...v1.3.5) (2024-06-18)


### Bug Fixes

* fix pocker update ([3e5c706](https://github.com/pommee/Pocker/commit/3e5c7063fccb958028697e76d16c7133a6fdc032))

## [1.3.4](https://github.com/pommee/Pocker/compare/v1.3.3...v1.3.4) (2024-06-18)


### Bug Fixes

* correct version number ([f531fab](https://github.com/pommee/Pocker/commit/f531fab451ad61f85a920cd682abd2cb53706392))

## [1.3.3](https://github.com/pommee/Pocker/compare/v1.3.2...v1.3.3) (2024-06-18)


### Bug Fixes

* faster startup time ([4ed0007](https://github.com/pommee/Pocker/commit/4ed000721e4d7bd3f282077b606259d9e1517e2f))

## [1.3.2](https://github.com/pommee/Pocker/compare/v1.3.1...v1.3.2) (2024-06-12)


### Bug Fixes

* correctly fetch changelog and better view in help screen ([012c949](https://github.com/pommee/Pocker/commit/012c9491f7e38039dabec92be9cee09e847218d7))
* escape help screen correct ([c330707](https://github.com/pommee/Pocker/commit/c3307079914ee7de2caa3cffe1476409d7368769))
* scroll to latest on startup ([67bc2a9](https://github.com/pommee/Pocker/commit/67bc2a9e20e5fb1a68ac6edff6182332f687d6a5))

## [1.3.1](https://github.com/pommee/Pocker/compare/v1.3.0...v1.3.1) (2024-06-12)


### Bug Fixes

* config and last fetch time placed in home config dot files ([dc2f1f0](https://github.com/pommee/Pocker/commit/dc2f1f02dffef1854ef94603d58ae590fd1fbd94))

# [1.3.0](https://github.com/pommee/Pocker/compare/v1.2.0...v1.3.0) (2024-06-06)


### Bug Fixes

* increase git fetch time, prevent rate limit ([088773d](https://github.com/pommee/Pocker/commit/088773d213c90d2d47446ac45571a320fe291a47))


### Features

* added update command ([279f17f](https://github.com/pommee/Pocker/commit/279f17f5f36c72afadb9d305ff8d85000d3d7f14))

# [1.2.0](https://github.com/pommee/Pocker/compare/v1.1.0...v1.2.0) (2024-06-06)


### Features

* notification when update available ([a83734e](https://github.com/pommee/Pocker/commit/a83734e0b8da4be833ea1cb683e7209d84dcbe3a))

# [1.1.0](https://github.com/pommee/Pocker/compare/v1.0.0...v1.1.0) (2024-06-05)


### Features

* improve startup time, added user config ([a7a8f58](https://github.com/pommee/Pocker/commit/a7a8f584bf0a91e539c46989dcff75184c970a83))

# 1.0.0 (2024-06-05)


### Bug Fixes

* running containers are placed at top ([05dee71](https://github.com/pommee/Pocker/commit/05dee718dbc5b9d821e9c313e49c4bc6ba2e9600))


### Features

* initial version ([2a0e428](https://github.com/pommee/Pocker/commit/2a0e428369c9c09f7fb0cca80309dea9467252ac))
