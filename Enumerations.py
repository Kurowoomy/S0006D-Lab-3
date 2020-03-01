import enum


class message_type(enum.Enum):
    treeIsChopped = 1
    makeCharcoal = 2
    cancelUpgrade = 3
    isUpgradedDiscoverer = 4
    move = 5
    treeAppeared = 6
    stopUpgrading = 7
    isUpgradedBuilder = 8
    buildingIsDone = 9



class location_type(enum.Enum):
    tree = 1
    kiln = 2
