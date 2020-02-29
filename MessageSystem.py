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
        currentTime = time.perf_counter()
        if len(MessageDispatcher.priorityQ) > 0:
            while MessageDispatcher.priorityQ[0][1].dispatchTime <= currentTime:
                MessageDispatcher.priorityQ[0][1].reciever.handleMessage(MessageDispatcher.priorityQ[0][1])
                heapq.heappop(MessageDispatcher.priorityQ)[1]
                if len(MessageDispatcher.priorityQ) <= 0:
                    break

        # for telegram in MessageDispatcher.priorityQ:
        #     if telegram[1].dispatchTime <= time.perf_counter():  # TODO: fortsätt fixa dispatchdelayedMessage/buggar
        #         telegram[1].reciever.handleMessage(telegram[1])
        #         heapq.heappop(MessageDispatcher.priorityQ)[1]