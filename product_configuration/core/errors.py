from configuration.models import OptionsProfile


class OptionDoesNotExist(Exception):
    def __init__(self, option_slug):
        self.option = OptionsProfile.objects.get(slug=option_slug)
        super().__init__(f'Ненайдена стоимоть опции {self.option.name}')

    def __str__(self):
        return f'В БД отсутствует стоимость опции: {self.option.name}'


# class OptionsCannotUsedTogether(Exception):
class OptionConstraintWorked(Exception):
    def __init__(self, text):
        self.text = text
        super().__init__(self.text)

    def __str__(self):
        return self.text
    # def __init__(self, options):
    #     self.options = [option.name for option in options]
    #     super().__init__('Невозможно совместное использование опций: \n' + '\n'.join(self.options))
    #
    # def __str__(self):
    #     return 'Невозможно совместное использование опций: \n' + '\n'.join(self.options)


# class OptionsMaxValueUse(Exception):
#     def __init__(self, options, max_value):
#         self.options = [option.name for option in options]
#         self.max_value = max_value
#         super().__init__(f'Превышен максимальный совместный объем ({self.max_value}) подключения опций:\n' + '\n'.join(self.options))
#
#     def __str__(self):
#         return f'Превышен максимальный совместный объем ({self.max_value}) подключения опций: \n' + '\n'.join(self.options)
