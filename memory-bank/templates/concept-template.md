---
page_type: concept
entities:
  - type: string
    required: true
    description: 概念实体类型
  - name: string
    required: true
    description: 概念名称
frontmatter_schema:
  entities:
    - type: object
      properties:
        - type: string
          required: true
        - name: string
          required: true
---

# {{entities[0].name}}

## Overview

{{entities[0].details}}

## Key Points

- Point 1
- Point 2
- Point 3

## Example

```
Example content or code snippet here
```

## Related Concepts

{{render_related(entities[0].related)}}

## References

{{render_references(entities[0].references)}}
