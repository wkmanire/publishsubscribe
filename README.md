# Publish Subscribe

## Overview and Features
A pubsub implementation with features to facilitate game development.

**Time Boxing**: Event dispatching is always done synchronously and is a blocking operation.  A time budget can be specified to help prevent the game from dropping frames.

**Message Prioritization**: Automatic sorting of events so that they are dispatched in a predictable order

**Subscriber Prioritization**: Specify the order in which subscribers are notified.  This can be especially helpful when paired with time boxing.  Less time sensitive subscribers can be deprioritized in the case that that time budget is exceeded during dispatch.

**Subscriber Groups**: The ability to name groups of subscribers and activate/disactivate them as a group without unsubscribing them.  This coincides with the concept of swapping scenes in a game loop.

**Event Queuing**: Events do not have to be immediately dispatched at the time of publishing.  Instead, dispatch can be deferred and executed on demand.

**Thread Safety**: A global mutex is used to prevent race conditions when publishing, subscribing, or dispatching events.

## Example
This example shows the basic pattern for using the publishsubscribe module.

```python
from enum import Enum, auto
from dataclasses import dataclass

import publishsubscribe as pubsub


class GameEvents(Enum):
    EntityCollision = auto()
    AchievementUnlocked = auto()
    MusicEnded = auto()


class Priorities(Enum):
    Low = auto()
    Medium = auto()
    High = auto()


def on_entity_collision(data):
    entity_1, entity_2 = data.entities
    print(f"{entity1} collided with {entity2}!")


def on_achievement_unlocked(data):
    print(
        f"Congratulations, you unlocked the {data} achievement!"
    )


def on_music_ended(data):
    print("Who killed the music?")
    restart_music(data)


# Here we are telling the system to process entity collisions before
# anything else.
#
# When the music ends, process that before dealing with achievements.
#
# Achievement handling gets the lowest priority.
pubsub.subscribe(GameEvents.EntityCollision, on_entity_collision,
                 Priorities.High)
pubsub.subscribe(GameEvents.MusicEnded, on_music_ended, Priorities.Medium)
pubsub.subscribe(GameEvents.AchievementUnlocked, on_achievement_unlocked,
                 Priorities.Low)


@dataclass
class EntityCollision:
    entity_1: object
    entity_2: object


# Let's say during a frame that the following events were published
# 1. The player collided with a wall
# 2. A bullet collided with a bullet
# 3. The music ended
# 4. The player unlocked the "bonk!" achievement
#
# NOTE!: Remember that publish does not cause the event to be
# immediately handled by subscribers. That will only happen when we
# call dispatch.

# Player vs Wall collision is higher priority than Bullet vs Bullet
# collision so within the EntityCollision events, handle player
# collision first.
pubsub.publish(GameEvents.EntityCollision, priority=Priorities.High, data=EntityCollision(player, wall))
pubsub.publish(GameEvents.EntityCollision, priority=Priorities.Low, data=EntityCollision(bullet, bullet))

# The music ended. We likely would never have two of these in the same
# frame, so we'll leave priority as the default value. Since all we
# need for the event data is the name of the song that was playing,
# we'll just pass a string for data instead of creating an event
# specific data class.
pubsub.publish(GameEvents.EntityCollision, data="main-theme.ogg")


# For running into the wall, the player unlocks the "bonk!" achievement
pubsub.publish(GameEvents.AchievementUnlocked, data="bonk!")

# We have now collected and prioritized four different events into the
# queue. We can choose to dispatch them at the end of the current
# frame, or we can hold onto them and dispatch them later, at the
# beginning of the next frame. You'll need to consider this when
# implementing your game loop. It is possible to dispatch only certain
# kinds of events, so you find that it is best to call dispatch
# multiple times in the same frame for different reasons.

# Let's set a budget of 4 milliseconds for event handling. This means
# we'll dispatch at least one event. If time permits, we'll dispatch
# additional events. It's possible that more than 4 milliseconds will
# elapse, but once the time budget has been met or exceeded, no
# additional events will be dispatched until dispatch is called again.
# We want to dispatch for all event types, so no event_type filter is
# provided.
pubsub.dispatch(budget_ms=4)

# publishsubscribe is capable of more functionality in terms of named
# subscriber groups. Be sure to scan the module to learn everything
# that this module can do. (it's less than 200 lines of code so it
# makes more sense to just read the module itself than to read a
# separate documentation)

```
