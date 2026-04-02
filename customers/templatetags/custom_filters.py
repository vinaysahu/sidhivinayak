from django import template
from common.utils.format_currency import format_indian_currency
from num2words import num2words

register = template.Library()

@register.filter
def indian_currency(value):
    return format_indian_currency(value)

@register.filter
def amount_in_words(value):
    return num2words(value, lang='en_IN').title()