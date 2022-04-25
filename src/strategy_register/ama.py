from typing import Tuple, Optional

from ._strategy_register import StrategyAbstract, PositionStatus
from matplotlib import pyplot as plt


SHOW_PLOT = False


class StrategyAMA(StrategyAbstract):
    constants = dict()

    @staticmethod
    def validate_params(params: dict):
        for p, val in params.items():
            if not (isinstance(val, int) and val > 0):
                raise ValueError(f'Parameter `{p}` must be integer and greather than 0.')

        if not params['fast'] < params['n'] < params['slow']:
            raise ValueError('`fast` must be < than `n`, and `n` must be < `slow`.')

    def calculate_ama(self, prices, fast, slow, n, t, last_ma):
        if last_ma is None:
            offset = fast + slow // 2
            last_ma = sum(prices[t - offset:t]) / (offset - 1)

        fastest = self.constants['fastest']
        slowest = self.constants['slowest']

        direction = abs(prices[t] - prices[t - n - 1])
        volatility = sum([abs(prices[t - i] - prices[t - i - 1]) for i in range(n)])
        er = direction / volatility
        smooth = er * (fastest - slowest) + slowest

        if er < .3:
            # Если тренд слабый, то возводим коэффициент сглаживания в квадрат.
            smooth = smooth ** 2

        return smooth * prices[t] + (1 - smooth) * last_ma

    def calculate(self, prices: list, params: dict, show_plot=False) -> Tuple[Optional[float], Optional[float]]:
        mas = []
        self.validate_params(params)
        # Задаём константы для алгоритма расчёта AMA в специальном словаре класса.
        self.constants['fastest'] = 2 / (params['fast'] + 1)
        self.constants['slowest'] = 2 / (params['slow'] + 1)
        margin = max(params.values())

        # Производим валидацию длины рассматриваемого периода.
        if len(prices) < margin or len(prices) < 2:
            # Если период слишком мал, то возвращаем null.
            return None, None

        result = 1.
        # Держим значение Enum, который будет служить флагом, куплен ли инструмент.
        position_status = PositionStatus.none

        # Флаг для первой покупки.
        first_buy = True
        last_price = None
        last_moving_average = None
        for t in range(margin - 1, len(prices)):
            # Считаем AMA.
            moving_average = self.calculate_ama(
                prices, params['fast'], params['slow'], params['n'], t, last_moving_average
            )

            # Условия покупки.
            if prices[t] > moving_average >= prices[t - 1] or \
                    first_buy and last_moving_average and moving_average > last_moving_average:
                # MA протыкает график сверху. Покупаем.
                if first_buy and last_moving_average:
                    # Если инструмент ещё не покупался и МА возрастает.
                    first_buy = False
                    last_price = (prices[t - 1] + prices[t]) / 2
                    position_status = PositionStatus.long
                    if show_plot:
                        print('buy by', moving_average)

                if position_status == PositionStatus.none:
                    # Запоминаем цену покупки, которая пригодится при расчёте во время продажи.
                    last_price = moving_average
                    if show_plot:
                        print('buy by', moving_average)
                # Запоминаем, что мы совершили покупку на повышение (позиция long).
                position_status = PositionStatus.long

            # Условия продажи.
            if prices[t] < moving_average <= prices[t - 1]:
                # MA протыкает график снизу. Продаём.
                if position_status == PositionStatus.long:
                    # Засчитаем продажу, если мы покупали.
                    # К значению доходности прибавляем отношение цены продажи к цене покупки.
                    result += moving_average / last_price - 1.
                    if show_plot:
                        print('sell by', moving_average)
                position_status = PositionStatus.none

            # Запоминаем значение MA для следующей итерации.
            last_moving_average = moving_average
            mas.append(moving_average)
            if show_plot:
                print(prices[t])
                print(moving_average)

        if show_plot:
            x = range(len(prices[margin - 1:]))
            plt.plot(x, prices[margin - 1:], x, mas)
            plt.show()
        return result, prices[-1] / prices[0]
