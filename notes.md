# Notes

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

