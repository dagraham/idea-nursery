# Notes


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

