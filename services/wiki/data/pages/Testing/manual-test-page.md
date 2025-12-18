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

![](http://localhost:5000/api/uploads/images/d7ad1b64-387a-4f1a-bc42-e74578c90354.png)

### Code Blocks

```
"""Entry point for running sync utility as a module"""
from app.sync.cli import main

if __name__ == '__main__':
    main()
```

### Tables