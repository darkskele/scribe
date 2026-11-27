# queue decisions

```{decision} Every queue is bounded, a power of two in capacity
:id: cds-queue-d1

A full push returns false and the caller decides.
```

```{decision} Cursors and ready flags sit on their own cache line
:id: cds-queue-d2
```

```{decision} Storage moves to the heap only by a template flag
:id: cds-queue-d3

For capacities too large for the stack.
```

```{decision} SlotRing is addressed by absolute position
:id: cds-queue-d4

So producers finish out of order and the consumer still reads in order.
```
