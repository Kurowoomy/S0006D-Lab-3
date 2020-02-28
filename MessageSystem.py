import time
import heapq


class Telegram:
    def __init__(self, sender, reciever, msg, dispatchTime, extraInfo):
        self.sender = sender
        self.reciever = reciever
        self.msg = msg
        self.dispatchTime = dispatchTime
        self.extraInfo = extraInfo


class MessageDispatcher:
    priorityQ = []  # queue for delayed messages

    def dispatchMessage(self, reciever, sender, msg, delay, extraInfo):
        dispatchTime = time.perf_counter() + delay
        telegram = Telegram(sender, reciever, msg, dispatchTime, extraInfo)
        if delay <= 0:
            reciever.handleMessage(telegram)
        else:
            heapq.heappush(MessageDispatcher.priorityQ, (dispatchTime, telegram))

    def dispatchDelayedMessages(self):  # TODO: fixa så dispatchDelayedMessages används
        pass
        # for telegram in MessageDispatcher.priorityQ:
        #     if telegram.dispatchTime <= time.perf_counter():  # TODO: fortsätt fixa dispatchdelayedMessage/buggar
        #         telegram[1].reciever.handleMessage(telegram)
        #         heapq.heappop(MessageDispatcher.priorityQ)[1]

        # amount = len(MessageDispatcher.priorityQ) - 1
        #
        # while amount >= 0:  # checks if it's time to let entities handle telegram message
        #     if MessageDispatcher.priorityQ[amount].dispatchTime <= time.clock():
        #         MessageDispatcher.priorityQ[amount].recieverEntity.handleMessage(MessageDispatcher.priorityQ[amount])
        #         MessageDispatcher.priorityQ.remove(MessageDispatcher.priorityQ[amount])
        #     amount -= 1
