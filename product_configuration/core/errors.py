from configuration.models import OptionsProfile


class OptionDoesNotExist(Exception):
    def __init__(self, option_slug):
        self.option = OptionsProfile.objects.get(slug=option_slug)
        super().__init__(f'Ненайдена стоимоть опции {self.option.name}')

    def __str__(self):
        return f'В БД отсутствует стоимость опции: {self.option.name}'


class OptionConstraintWorked(Exception):
    def __init__(self, text):
        self.text = text
        super().__init__(self.text)

    def __str__(self):
        return self.text
