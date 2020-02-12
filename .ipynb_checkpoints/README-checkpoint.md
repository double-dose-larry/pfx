This package provides an iterface to pulling down Pitch F/X data and converting it to a usable dataframe

usage

```python
from pfx import PitchFX
#init
pfx = PitchFX()

# see what games are available for a date or date range
pfx.get_gameday_gids(start="4/1/2019", end="4/7/2019")

# pull down data into a pandas dataframe
df = pfx.get_gid_df('gid_2019_06_19_tbamlb_nyamlb_1') # takes a few seconds per game

# or if you want multiple games
import pandas as pd
df = pd.concat([ pfx.get_gid_df(gid) for gid in pfx.get_gameday_gids("4/1/2019")]) # may take a few minutes

# use data as necessary
df.shape
```