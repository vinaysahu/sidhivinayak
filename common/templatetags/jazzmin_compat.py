from django import template
from django.contrib.admin.views.main import PAGE_VAR
from django.utils.safestring import mark_safe

register = template.Library()


@register.simple_tag
def jazzmin_paginator_number(change_list, i):
    """
    Fixed version of jazzmin's jazzmin_paginator_number that uses mark_safe
    instead of format_html() with no args, which was broken in Django 6.0.
    """
    html_str = ""
    start = i == 1
    end = i == change_list.paginator.num_pages
    spacer = i in (".", "\u2026")
    current_page = i == change_list.page_num

    if start:
        link = change_list.get_query_string({PAGE_VAR: change_list.page_num - 1}) if change_list.page_num > 1 else "#"
        html_str += """
        <li class="page-item previous {disabled}">
            <a class="page-link" href="{link}" data-dt-idx="0" tabindex="0">\u00ab</a>
        </li>
        """.format(link=link, disabled="disabled" if link == "#" else "")

    if current_page:
        html_str += """
        <li class="page-item active">
            <a class="page-link" href="javascript:void(0);" data-dt-idx="3" tabindex="0">{num}</a>
        </li>
        """.format(num=i)
    elif spacer:
        html_str += """
        <li class="page-item">
            <a class="page-link" href="javascript:void(0);" data-dt-idx="3" tabindex="0">\u2026 </a>
        </li>
        """
    else:
        query_string = change_list.get_query_string({PAGE_VAR: i})
        end_class = "end" if end else ""
        html_str += """
            <li class="page-item">
            <a href="{query_string}" class="page-link {end}" data-dt-idx="3" tabindex="0">{num}</a>
            </li>
        """.format(num=i, query_string=query_string, end=end_class)

    if end:
        link = change_list.get_query_string({PAGE_VAR: change_list.page_num + 1}) if change_list.page_num < i else "#"
        html_str += """
        <li class="page-item next {disabled}">
            <a class="page-link" href="{link}" data-dt-idx="7" tabindex="0">\u00bb</a>
        </li>
        """.format(link=link, disabled="disabled" if link == "#" else "")

    return mark_safe(html_str)
