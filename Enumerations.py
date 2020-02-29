import enum


class message_type(enum.Enum):
    treeIsChopped = 1
    makeCharcoal = 2
    cancelUpgrade = 3
    isUpgradedDiscoverer = 4
    move = 5
    treeAppeared = 6
    stopUpgrading = 7
