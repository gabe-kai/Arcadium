---
title: Manual Test Page
slug: manual-test-page
section: Testing
status: published
order: 0
---
# Manual Test Page

## Formatting

### Basic Text Formatting

The **bold**, _italic_, and `inline code` formats all appear to work.

An [external link](https://www.google.com) and an [internal link](/pages/bea4e8a4-e141-47e6-9974-c9c1da165c29) both appear to work.

### List Formatting

Bullet List:

-   bullet 1
    
-   bullet 2
    
-   bullet 3
    
    -   sub bullet 1
        
        -   sub sub bullet 2
            
            -   sub sub sub bullet 3

Numbered List:

1.  number 1
    
2.  number 2
    
3.  number 3
    
    1.  sub number 1
        
        1.  sub sub number 2
            
            1.  sub sub sub number 3

### Image Formatting

![](http://localhost:5000/api/uploads/images/93416a64-7b18-4a3b-9e9b-81280ca0a18a.png)

### Code Blocks

```
"""Entry point for running sync utility as a module"""
from app.sync.cli import main

if __name__ == '__main__':
    main()
```

### Tables

<table class="arc-editor-table" style="min-width: 75px;"><colgroup><col style="min-width: 25px;"><col style="min-width: 25px;"><col style="min-width: 25px;"></colgroup><tbody><tr><th colspan="1" rowspan="1"><p></p></th><th colspan="1" rowspan="1"><p>Col 1</p></th><th colspan="1" rowspan="1"><p>Col 2</p></th></tr><tr><td colspan="1" rowspan="1"><p>Row 1</p></td><td colspan="1" rowspan="1"><p></p></td><td colspan="1" rowspan="1"><p></p></td></tr><tr><td colspan="1" rowspan="1"><p>Row 2</p></td><td colspan="1" rowspan="1"><p></p></td><td colspan="1" rowspan="1"><p></p></td></tr></tbody></table>