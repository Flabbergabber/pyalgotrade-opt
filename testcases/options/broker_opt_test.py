import datetime

import testcases.common

from pyalgotrade import broker
from pyalgotrade.broker import optbroker

class DefaultTraits(optbroker.InstrumentTraits):
    def roundQuantity(self, quantity):
        return int(quantity)


class OrderTestCase(testcases.common.TestCase):
    def __buildAcceptedLimitOrder(self, action, limitPrice, quantity):
        ret = optbroker.OptionLimitOrder(action, "orcl", limitPrice, quantity, optbroker.OptionOrder.Right.CALL, 20, "2016-01-01", DefaultTraits())
        self.assertEquals(ret.getSubmitDateTime(), None)
        ret.switchState(optbroker.Order.State.SUBMITTED)
        ret.setSubmitted(1, datetime.datetime.now())
        self.assertNotEquals(ret.getSubmitDateTime(), None)
        ret.switchState(optbroker.Order.State.ACCEPTED)
        return ret

    def testCompleteFill(self):
        order = self.__buildAcceptedLimitOrder(optbroker.Order.Action.BUY, 1, 1)
        self.assertEqual(order.getRemaining(), 1)
        self.assertEqual(order.getFilled(), 0)
        self.assertEqual(order.getAvgFillPrice(), None)
        self.assertEqual(order.getExecutionInfo(), None)

        order.addExecutionInfo(broker.OrderExecutionInfo(0.9, 1, 0, datetime.datetime.now()))
        self.assertTrue(order.isFilled())
        self.assertEqual(order.getRemaining(), 0)
        self.assertEqual(order.getFilled(), 1)
        self.assertEqual(order.getAvgFillPrice(), 0.9)

    def testCompleteFillInvalidSize(self):
        order = self.__buildAcceptedLimitOrder(optbroker.Order.Action.BUY, 1, 1)
        with self.assertRaises(Exception):
            order.addExecutionInfo(broker.OrderExecutionInfo(1, 1.001, 0, datetime.datetime.now()))
        self.assertTrue(order.isAccepted())
        self.assertEqual(order.getRemaining(), 1)
        self.assertEqual(order.getFilled(), 0)
        self.assertEqual(order.getAvgFillPrice(), None)
        self.assertEqual(order.getExecutionInfo(), None)

    def testPartialFill(self):
        order = self.__buildAcceptedLimitOrder(optbroker.Order.Action.BUY, 2, 11)
        self.assertEqual(order.getRemaining(), 11)
        self.assertEqual(order.getFilled(), 0)
        self.assertEqual(order.getAvgFillPrice(), None)
        self.assertEqual(order.getExecutionInfo(), None)

        order.addExecutionInfo(broker.OrderExecutionInfo(1, 8, 0, datetime.datetime.now()))
        self.assertTrue(order.isPartiallyFilled())
        self.assertEqual(order.getRemaining(), 3)
        self.assertEqual(order.getFilled(), 8)
        self.assertEqual(order.getAvgFillPrice(), 1)
        self.assertEqual(order.getExecutionInfo().getQuantity(), 8)
        self.assertEqual(order.getExecutionInfo().getPrice(), 1)

        order.addExecutionInfo(broker.OrderExecutionInfo(1.5, 1, 0, datetime.datetime.now()))
        self.assertTrue(order.isPartiallyFilled())
        self.assertEqual(order.getRemaining(), 2)
        self.assertEqual(order.getFilled(), 9)
        self.assertEqual(round(order.getAvgFillPrice(), 4), round(1.055555556, 4))
        self.assertEqual(order.getExecutionInfo().getQuantity(), 1)
        self.assertEqual(order.getExecutionInfo().getPrice(), 1.5)

        order.addExecutionInfo(broker.OrderExecutionInfo(1.123, 2, 0, datetime.datetime.now()))
        self.assertTrue(order.isFilled())
        self.assertEqual(order.getRemaining(), 0)
        self.assertEqual(order.getFilled(), 11)
        self.assertEqual(round(order.getAvgFillPrice(), 4), round(1.067818182, 4))
        self.assertEqual(order.getExecutionInfo().getQuantity(), 2)
        self.assertEqual(order.getExecutionInfo().getPrice(), 1.123)