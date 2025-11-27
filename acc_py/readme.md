# src/acc_py structure

Basically the package is distributed in 4 subpackages.

### context
Config files -- It ensures that config.json and other configurations are loaded properly, without failing.

### db
Bridge between the database and the end user. It loads context for configs.

### plot
Plotting functions that load configurations from config.

### utilities
Random functions that do not rely on context. They're subdivided in parsers (meant to fail gracefully when it can't parse) and prompters (meant to do while loops to handle parser errors). Miscellanea is just a file for random stuff that is useful.


# Testing

- Check [unified.py](./test/unified.py) -- yes, you have to code a little bit
- Change `DB_PATH` and `DB_TEST_PATH` accordingly.