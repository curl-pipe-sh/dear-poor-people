# poor-tools

A collection of quick-and-dirty shell hacks pretending to be real tools.
Made for situations where you can't install the proper thing (no internet, no package manager, no compiler, no patience).

They're small, ugly, and barely work — but sometimes that's enough.

## Installing the bundle

Run `./poor-installer --dest /some/bin` to copy every tool into your own bin
directory. Useful flags:

- `--emulate` strips the `poor` prefix (so `poorcurl` becomes `curl`).
- `--clear` wipes the destination before installing.
- `--ignore NAME` or `--ignore 'pattern*'` skips specific tools.
- `--uninstall` removes the files we would install (respects the same flags).

You can also install a subset via globs: `./poor-installer --dest ~/.local/bin 'curl*'`.

## License

GPL-3.0, deal with it.
