---
kind: area
---

# queue

Bounded lock-free queues, one per shape of producers and consumers. Each moves elements between threads with no lock and no allocation after construction.

## Diagram

```
SpscQueue    one producer ──▶ one consumer
MpscQueue    many producers ──▶ one consumer
SpmcQueue    one producer ──▶ every consumer sees every element
WorkQueue    one producer ──▶ each element to one consumer
SlotRing     producers fill positions in any order ──▶ one consumer reads in order
```

## Description

- `SpscQueue`. One producer, one consumer.
- `MpscQueue`. Any number of producers race to claim a position, one consumer.
- `SpmcQueue`. One producer, a compile-time set of consumers, each reading every element at its own pace.
- `WorkQueue`. One producer, each element taken by exactly one consumer, in push order.
- `SlotRing`. Addressed by absolute position. Producers finish out of order, the consumer reads in order.

Every queue is bounded, a power of two in capacity. A full push returns false and the caller decides.

## Milestones

````{milestone} A queue for every producer and consumer shape
:id: cds-queue-m1
:status: done

```{reqs}
r1  done  A full push returns false and leaves the queue unchanged
r2  done  Elements leave in the order they entered, per producer
```
````

````{milestone} No system call on any path
:id: cds-queue-m2
:status: underway

A lost CAS spins on a pause instruction, never `std::this_thread::yield`.

```{claims}
c1  open  ^cds-c1  Push and pop make no system call on any path
```
````

````{milestone} Element storage touched at construction
:id: cds-queue-m3
:status: open

So no first push takes a page fault.

```{claims}
c2  open  No page fault after construction
```
````

````{milestone} Memory ordering and races checked
:id: cds-queue-m4
:status: open

```{claims}
c3  open  Every queue's orderings are sufficient under the C++ memory model
c4  open  No data race on any queue
```
````

````{milestone} Push and pop noexcept whenever constructing the element is
:id: cds-queue-m6
:status: open

```{reqs}
r3  open  push and pop are noexcept exactly when the element's construction is
```
````
