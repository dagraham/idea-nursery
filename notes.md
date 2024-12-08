# Notes


age      0   1   2   3   4   5   6   7   8   9   10  11  12  13  14  15
inkling  _   _   _   1   2   3   4   5   6   7   8   9   10  11  12  13
notion   _   _   _   x   x   x   x   1   2   3   4   5   6   7   8   9
idea     _   _   _   _   _   _   _   x   x   x   x   x   1   2   3   4   5   6

start at 3 for inkling => 4 for notion and 5 for age
inkling_late = age - 3 = age - X
notion_late = age - 3 - 4 = age - X - X - 1 = age - 2X - 1 
idea_late = age - 3 - 4 - 5 = age - 12 = age - 2X - 1 - X - 2 = age - 3X - 3 

ages = x, y, z (3, 4, 5)

inkling_late = age - x 
notion_late = age - x - y
idea_late = age - x - y - z
warning = w 

inkling_late = 0 => inkling_age_color == inkling color (on time) then progesses to red over the next w periods
notion_late = 0 => notion_age_color == notion color (on time) then progesses to red over the next w periods




def show (list of status names)

    list of names -> list of numbers 

    binary rep = [1 for x in [0,1,2,3] if x in list_of_numbers else 0]

def hide (list of status_names)

    list of names -> list of numbers 

    binary rep = [x for x in [0,1,2,3] if x in list_of_numbers]
    
```python
def hide(lst:list[int])->int:
    """Converts list of status positions to a list of binaries where a 1's mean hide and 0's show."""
    ret = []
    for x in [0,1,2,3]:
        if x in lst:
            ret.append(1)
        else:
            ret.append(0)
    return ret

def show(lst:list[int])->int:
    """Converts list of status positions to a list of binaries where a 1's mean hide and 0's show."""
    ret = []
    for x in [0,1,2,3]:
        if x in lst:
            ret.append(0)
        else:
            ret.append(1)
    return ret

def hide_pos_from_binary(lst_of_binaries:list[int])->list[int]:
    count = 0
    res = []
    for x in lst_of_binaries:
        if x == 1:
            res.append(count)
        count += 1
    return res


```
def show(rep:List[int]) 


- [ ] list of integers argument
```python
@click.command()
@click.option('--numbers', type=int, multiple=True, help="List of integers")
def process_numbers(numbers):
    click.echo(f"Received numbers: {list(numbers)}")
```

- [ ] set-stage command
```python
@click.command()
@click.argument(
    "stage",
    type=click.Choice([r for r in stage_names]),  # Constrain "stage" to valid choices
)
@click.argument("pos", type=int)  # Second required argument
def set_stage(stage: str, pos: int):
```

- [ ] set-status command
```python
@click.command()
@click.argument(
    "status",
    type=click.Choice([s for s in status_names]),
    help="Status of the idea",
)
@click.argument("pos", type=int)  # Second required argument
def set_status(status: str, pos: int):
```

- 0 to 1 or 2 and 1 or 2 to 0 replace pause and activate
- 1 to 2 replace advance
  - require stage 3 (idea/plant)?
  - create (and then keep updated) markdown version?
- allow 2 to 1?

- maybe promote & demote with --status and/or --stage switches






Todo

- [ ] maybe one status command allows 1->0 and 0->1 pause and activate and 1->2 and 2->1 advance and withdraw

- [ ] Work out idle colors
- [ ] Work out age colors

- [ ] Edit does name (first line) and content (remaining lines)
- [ ] add rename, stage and release/promote? and then remove update as command - status handled by pause+activate and promote


## thinking about timestamp colors 

```
Start           age          idle  
thought[0]   0 color[0]    0  color[0]
             
```
If there is an expectation for duration for each stage, then the sum would be the expectation for how long to keeper and then library when tagged and linked.

When transitions to next stages occur on time, age color should remain the same as the stage color. When age is greater than the sum of expections to get to the next stage, then age should get an alert color that depends on how much greater. Thinking of stage colors as a progression from blue to yellow, late should be a progression from the stage color to red.

How long for each stage?


How to preserve times when moving to paused?

Add pause (active -> paused) and activate (paused -> active) commands
pause: added = now - added, reviewed = now - reviewed
activate: added = when shifting back to active, 

pause:      added1 = now1 - added0; reviewed1 = now1 - reviewd0

activate:   added2 = now2 - added1 = now2 - now1 + added0



```python
oneday = 24 * 60 * 60
age_period = 7 * oneday
idle_period = 2 * oneday

num_colors = len(time_colors) 

oneday = 24 * 60 * 60
days_allowed = [2, 3, 3, 2] # eg
late_colors = [ , , , ]

# if on time, give stage color 
def get_color(seconds, num_days):
    for i in range(num_colors):
        if seconds <= (i+1)*num_days*oneday
            return colors[i]


    



```

