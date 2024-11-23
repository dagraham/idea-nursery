# Notes

## thinking about views and saving state

-

```
id in the first column and position in the last. Note that position
is +1 what it should be to correspond to the actual row number.
ideas from view: [
    (1, 'My First Idea', 0, 0, 1732294455, 1732294455, 2), 
    (2, 'My Second Idea', 1, 1, 1732294455, 1732294455, 3), 
    (3, 'My Third Idea', 2, 1, 1732294455, 1732294455, 4), 
    (4, 'My Fourth Idea', 3, 2, 1732294455, 1732294455, 5)
]
after deleting 'position 3' which should have been row 3 but actually deletes id 2 
ideas from view: [
    (1, 'My First Idea', 0, 0, 1732294455, 1732294455, 2), 
    (3, 'My Third Idea', 2, 1, 1732294455, 1732294455, 3), 
    (4, 'My Fourth Idea', 3, 2, 1732294455, 1732294455, 4)
]


```
