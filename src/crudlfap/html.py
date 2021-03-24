from django.conf import settings
from django.urls import reverse
from django.utils.translation import ugettext as _
from ryzom_django_mdc.html import *  # noqa


class A(A):
    attrs = dict(
        up_target='#main, .mdc-top-app-bar__title, #drawer .mdc-list',
        # up_transition='cross-fade',
    )


class PageMenu(Div):
    attrs = dict(cls='mdc-elevation--z2', style='margin-bottom: 10px')

    def to_html(self, *content, **context):
        if 'page-menu' not in context:
            return super().to_html(*content, **context)

        content = list(content)
        menu = context['page-menu']

        for v in menu:
            if v.urlname == context['view'].urlname:
                continue

            button = A(
                MDCTextButton(
                    v.label.capitalize(),
                    icon=getattr(v, 'icon', None),
                    tag='span',
                    style={
                        'margin': '10px',
                        'color': getattr(v, 'color', 'inherit'),
                    },
                ),
                href=v.url,
                style='text-decoration: none',
            )
            if getattr(v, 'controller', None) == 'modal':
                button.attrs.up_modal = '.main-inner'
                del button.attrs['up-target']

            content.append(button)

        return super().to_html(
            *content,
            '<div class="mdc-elevation-overlay"></div>',
            '<div class="mdc-button__ripple"></div>',
            **context,
        )


class Main(Main):
    pass


class Body(Body):
    style = 'margin: 0'

    def __init__(self, *content, **attrs):
        self.drawer = mdcDrawer(id='drawer')
        self.bar = mdcTopAppBar()
        self.main = Main(
            Div(
                *content,
                cls='main-inner',
            ),
            cls='main mdc-drawer-app-content',
            id='main',
        )
        self.debug = settings.DEBUG
        super().__init__(
            self.bar,
            Div(
                self.drawer,
                self.main,
                cls='mdc-top-app-bar--fixed-adjust',
            ),
        )

    def py2js(self):
        up.compiler('[data-mdc-auto-init]', lambda: mdc.autoInit())
        if self.debug:
            up.log.enable()


class App(Html):
    body_class = Body
    scripts = [
        'https://unpkg.com/unpoly@0.62.1/dist/unpoly.js',
    ]
    stylesheets = [
        'https://unpkg.com/unpoly@0.62.1/dist/unpoly.min.css',
    ]


class NarrowCard(Div):
    style = {
        'max-width': '25em',
        'margin': 'auto',
        'padding': '1em',
        'margin-top': '2em',
        'button': {
            'width': '100%',
        },
        '.MDCField label': {
            'width': '100%',
        }
    }


@template('crudlfap/form.html', App, NarrowCard)
@template('crudlfap/update.html', App, NarrowCard)
@template('crudlfap/create.html', App, NarrowCard)
@template('registration/login.html', App, NarrowCard)
class FormTemplate(Form):
    attrs = dict(
        up_target=A.attrs['up-target'],
        method='post',
    )

    def to_html(self, view, form, **context):
        back = ''
        if next_ := view.request.GET.get('next', ''):
            back = A(
                MDCButton(
                    _('Back'),
                    tag='span',
                ),
                href=next_,
            )
        return super().to_html(
            H3(view.title),
            form,
            CSRFInput(view.request),
            back,
            MDCButton(getattr(view, 'title_submit', _('Submit'))),
        )


@template('crudlfap/home.html', App)
class Home(Div):
    def to_html(self, **context):
        return super().to_html(H1('Welcome to Ryzom-CRUDLFA+'), **context)


@template('registration/logged_out.html', App, NarrowCard)
class LoggedOut(Div):
    def to_html(self, **context):
        from .site import site
        return super().to_html(
            H1(_('Log out')),
            P(_('Thanks for spending some quality time with the Web site today.')),  # noqa
            A(
                _('Log in again'),
                href=site.views['login'].url,
            ),
            **context,
        )


@template('crudlfap/detail.html', App, NarrowCard)
class ObjectDetail(Div):
    def to_html(self, **context):
        table = MDCDataTable()
        table.thead.attrs.style.display = 'none'
        table.table.attrs.style.width = '100%'
        table.attrs.data_mdc_auto_init = False

        for field in context['view'].display_fields:
            table.tbody.addchild(MDCDataTableTr(
                MDCDataTableTh(field['field'].verbose_name.capitalize()),
                MDCDataTableTd(field['value']),
            ))

        return super().to_html(table, **context)

    def context(self, *content, **context):
        context['page-menu'] = context['view'].router.get_menu(
            'object',
            context['view'].request,
            object=context['view'].object,
        )
        return super().context(*content, **context)


class ListAction(Div):
    def onclick(element):
        link = element.attributes.href.value + '?'
        for checkbox in document.querySelectorAll('[data-pk]:checked'):
            link += '&pk=' + checkbox.attributes['data-pk'].value
        up.modal.visit(link, {target: '.main-inner'})


class ListActions(Component):
    tag = 'list-actions'

    class HTMLElement:
        def connectedCallback(self):
            this.previousElementSibling.addEventListener(
                'change', this.change.bind(this))

        def change(self, event):
            if event.target.checked:
                this.style.display = 'block'
            elif not this.previousElementSibling.querySelector(':checked'):
                this.style.display = 'none'


@template('crudlfap/list.html', App)
class ObjectList(Div):
    def context(self, *content, **context):
        context['page-menu'] = context['view'].router.get_menu(
            'model',
            context['view'].request,
        )
        return super().context(*content, **context)

    def to_html(self, **context):
        if context['view'].listactions:
            table_checkbox = MDCCheckboxInput()
            table_checkbox.attrs.addcls = 'mdc-data-table__header-row-checkbox'

            thead = MDCDataTableThead(tr=MDCDataTableHeaderTr(
                MDCDataTableTh(
                    table_checkbox,
                    addcls='mdc-data-table__header-cell--checkbox',
                )
            ))
        else:
            thead = MDCDataTableThead(tr=MDCDataTableHeaderTr())

        for column in context['view'].table.columns:
            thead.tr.addchild(self.th_component(column, **context))

        # align "actions" title to the right with the buttons
        thead.tr.content[-1].attrs.style['text-align'] = 'right'

        table = MDCDataTable(thead=thead, style={
            'min-width': '100%',
            'border-width': 0,
        })

        for row in context['view'].table.paginated_rows:
            table.tbody.addchild(
                self.row_component(row, **context)
            )

        if context['view'].listactions:
            table.addchild(self.listactions_component(**context))

        table.addchild(self.pagination_component(**context))

        return super().to_html(
            self.drawer_component(**context) or '',
            PageMenu(),
            Div(
                self.search_component(**context) or '',
                table,
                cls='mdc-drawer__content'
            ),
            **context,
        )

    def listactions_component(self, **context):
        return ListActions(
            *[
                ListAction(
                    MDCButton(
                        view.label,
                        icon=view.icon,
                        style='color: ' + getattr(view, 'color', 'inherit'),
                    ),
                    title=view.title,
                    href=view.url,
                    up_modal='.main-inner',
                    up_target=False,
                ) for view in context['view'].listactions
            ],
        )

    def search_component(self, **context):
        search_form = self.search_form_component(**context)

        filterset = getattr(context['view'], 'filterset', None)
        if not filterset:
            return search_form

        toggle = MDCDrawerToggle(
            Button(
                'filter_list',
                cls='material-icons mdc-icon-button',
                style='--mdc-ripple-fg-size:28px; --mdc-ripple-top:10px;',
            ),
            data_drawer_id='page-drawer',
        )

        filters_chips = Div(
            toggle=toggle,
            search=search_form or '',
            chips=Div(
                cls='mdc-chip-set',
                role='grid',
                style='display: inline-block',
            )
        )

        def remove_filter_url(name):
            get = context['view'].request.GET.copy()
            if name in get:
                del get[name]
            return context['view'].request.path_info + '?' + get.urlencode()

        for bf in filterset.form.visible_fields():
            value = context['view'].request.GET.get(bf.name, '')
            if not value:
                continue
            chip = MDCChip(
                Span(
                    role='button',
                    tabindex='0',
                    cls='mdc-chip__primary-action',
                    text=Span(
                        bf.label,
                        ': ',
                        str(bf.form.cleaned_data[bf.name]),
                        cls='mdc-chip__text',
                    ),
                ),
                icon=I(
                    'cancel',
                    cls=(
                        'material-icons',
                        'mdc-chip__icon',
                        'mdc-chip__icon--trailing',
                    ),
                    tabindex='-1',
                    role='button',
                ),
                tag='a',
                href=remove_filter_url(bf.name),
                up_target='main',
            )
            filters_chips.chips.addchild(chip)
        return filters_chips

    def drawer_component(self, **context):
        filterset = getattr(context['view'], 'filterset', None)
        if not filterset:
            return
        form = Form(
            method='get',
            action=context['view'].request.path_info,
            up_autosubmit=True,
            up_delay='200ms',
            up_target='.mdc-drawer__content',
        )
        for key in ('sort', 'q'):
            if key in context['view'].request.GET:
                form.addchild(Input(
                    name=key,
                    value=context['view'].request.GET[key],
                    type='hidden'
                ))
        for bf in filterset.form.visible_fields():
            filterfield = MDCFilterField(
                label=bf.label,
                widget=bf.to_component()
            )
            value = context['view'].request.GET.get(bf.name, '')
            if not value:
                filterfield.widget.style.display = 'none'
            form.addchild(filterfield)
        drawer = Aside(
            MDCDrawerToggle(
                MDCButton(_('Close'), icon='close'),
                data_drawer_id='page-drawer',
                style='text-align: right',
            ),
            Div(
                form,
                cls='mdc-drawer-app-content',
            ),
            id='page-drawer',
            cls='mdc-drawer mdc-drawer--dismissible',
            style='padding: 1em',
        )
        return drawer

    def search_form_component(self, **context):
        search_form = getattr(context['view'], 'search_form', None)

        if not search_form:
            return

        search_form = InlineForm(
            search_form,
            method='get',
            action=context['view'].request.path_info,
            up_autosubmit=True,
            up_delay='200ms',
            up_target='.mdc-data-table, .mdc-chip-set',
        )
        for k, v in context['view'].request.GET.items():
            if k == 'q':
                continue
            search_form.addchild(Input(
                name=k,
                value=v,
                type='hidden',
            ))
        return search_form

    def row_component(self, row, **context):
        if context['view'].listactions:
            checkboxinput = MDCCheckboxInput(
                data_pk=str(row.record.pk)
            )
            checkboxinput.attrs.addcls = 'mdc-data-table__row-checkbox'
            tr = MDCDataTableTr(
                MDCDataTableTd(
                    checkboxinput,
                    addcls='mdc-data-table__cell--checkbox',
                )
            )
        else:
            tr = MDCDataTableTr()

        for column, cell in row.items():
            # todo: localize values
            tr.addchild(MDCDataTableTd(cell))
            # todo: if is numeric
            # td.attrs.addcls = 'mdc-data-table__header-cell--numeric'
        return tr

    def th_component(self, column, **context):
        th = MDCDataTableTh(
            wrapper=Div(
                cls='mdc-data-table__header-cell-wrapper',
                label=Div(
                    cls='mdc-data-table__header-cell-label',
                    style='font-weight: 500',
                    text=Text(column.header),
                ),
            )
        )

        # sorting
        if column.orderable:
            th.attrs.addcls = 'mdc-data-table__header-cell--with-sort'
            if column.is_ordered:
                th.attrs.addcls = 'mdc-data-table__header-cell--sorted'
            get = context['view'].request.GET.copy()
            get['sort'] = column.order_by_alias.next
            href = ''.join([
                context['view'].request.path_info,
                '?',
                get.urlencode(),
            ])
            th.wrapper.content += [
                A(
                    cls=(
                        'mdc-icon-button',
                        'material-icons',
                        'mdc-data-table__sort-icon-button',
                    ),
                    aria_label='Sort by dessert',
                    aria_describedby='dessert-status-label',
                    up_target='table',
                    href=href,
                    text=Text(
                        'arrow_upward'
                        if column.order_by_alias.is_descending
                        else 'arrow_downward'
                    ),
                ),
                Div(
                    cls='mdc-data-table__sort-status-label',
                    aria_hidden='true',
                    id='dessert-status-label',
                ),
            ]
        return th

    def pagination_component(self, **context):
        def pageurl(n):
            get = context['view'].request.GET.copy()
            get['page'] = n
            return context['view'].request.path_info + '?' + get.urlencode()

        page = context['view'].table.page
        navigation = Div(
            Div(
                cls='mdc-data-table__pagination-total',
                text=Text(''.join([
                    str(page.start_index()),
                    '-',
                    str(page.paginator.per_page * page.number),
                    ' / ',
                    str(page.paginator.count),
                ]))
            ),
            A(
                cls=(
                    'mdc-icon-button',
                    'material-icons',
                    'mdc-data-table__pagination-button',
                ),
                disabled=page.number == 1,
                href=pageurl(1),
                icon=Div(cls='mdc-button__icon', text=Text('first_page')),
                up_target='.mdc-data-table',
            ),
            A(
                cls=(
                    'mdc-icon-button',
                    'material-icons',
                    'mdc-data-table__pagination-button',
                ),
                disabled=not page.has_previous(),
                icon=Div(cls='mdc-button__icon', text=Text('chevron_left')),
                href=pageurl(
                    page.number - 1
                    if page.has_previous()
                    else 1
                ),
                up_target='.mdc-data-table',
            ),
            A(
                cls=(
                    'mdc-icon-button',
                    'material-icons',
                    'mdc-data-table__pagination-button',
                ),
                disabled=not page.has_next(),
                icon=Div(cls='mdc-button__icon', text=Text('chevron_right')),
                href=pageurl(
                    page.number + 1
                    if page.has_next()
                    else page.paginator.num_pages
                ),
                up_target='.mdc-data-table',
            ),
            A(
                cls=(
                    'mdc-icon-button',
                    'material-icons',
                    'mdc-data-table__pagination-button',
                ),
                disabled=page.paginator.num_pages == page.number,
                icon=Div(cls='mdc-button__icon', text=Text('last_page')),
                href=pageurl(page.paginator.num_pages),
                up_target='.mdc-data-table',
            ),
            cls='mdc-data-table__pagination-navigation',
        )
        perpage = Div(
            Div(
                _('Rows per page'),
                cls='mdc-data-table__pagination-rows-per-page-label'
            ),
            select=MDCSelectPerPage(
                addcls=(
                    'mdc-select--outlined',
                    'mdc-select--no-label',
                    'mdc-data-table__pagination-rows-per-page-select',
                ),
                select=Select(*[
                    Option(
                        str(i),
                        value=i,
                        selected=page.paginator.per_page == i
                    )
                    for i in (3, 5, 7, 10, 25, 100)
                ])
            ),
            cls='mdc-data-table__pagination-rows-per-page',
        )
        return MDCDataTablePagination(
            perpage=perpage,
            navigation=navigation,
        )


class mdcTopAppBar(Header):
    def __init__(self, title='', buttons=None):
        self.title = title
        self.buttons = buttons or []
        super().__init__(
            Div(cls='mdc-top-app-bar__row'),
            cls='mdc-top-app-bar app-bar',
            id='app-bar',
            data_mdc_auto_init='MDCTopAppBar',
        )

    def to_html(self, view, **context):
        self.content[0].content = [Component(
            Section(
                Button(
                    'menu',
                    cls='material-icons mdc-top-app-bar__navigation-icon mdc-icon-button',  # noqa
                ),
                Span(
                    view.title,
                    cls='mdc-top-app-bar__title',
                ),
                cls='mdc-top-app-bar__section mdc-top-app-bar__section--align-start',  # noqa
            ),
            cls='mdc-top-app-bar__section mdc-top-app-bar__section--align-start',  # noqa
            tag='section',
        )]
        return super().to_html(**context)

    def nav():
        window.drawer.open = not window.drawer.open

    def py2js(self):
        window.addEventListener('DOMContentLoaded', self.setup)

    def setup():
        window.drawer = mdc.drawer.MDCDrawer.attachTo(
            document.getElementById('drawer'))
        topAppBar = mdc.topAppBar.MDCTopAppBar.attachTo(
            document.getElementById('app-bar'))
        topAppBar.setScrollTarget(document.getElementById('main'))
        topAppBar.listen('MDCTopAppBar:nav', self.nav)


class mdcDrawer(Aside):
    def __init__(self, *content, **attrs):
        super().__init__(
            Div(
                *content,
                cls='mdc-drawer__content',
            ),
            cls='mdc-drawer mdc-drawer--dismissible mdc-top-app-bar--fixed-adjust',  # noqa
            data_mdc_auto_init='MDCDrawer',
            **attrs,
        )

    def to_html(self, *content, view, **context):
        request = view.request
        from .site import site

        content = []
        for view in site.get_menu('main', request):
            router = getattr(view, 'router', None)
            if router:
                icon = getattr(router, 'icon', None)
                title = getattr(view, 'model_verbose_name', view.title)
            else:
                icon = getattr(view, 'icon', None)
                title = getattr(view, 'title', '')

            content.append(
                A(
                    MDCListItem(title.capitalize(), icon=icon),
                    href=view.url,
                    style='text-decoration: none',
                )
            )

        if request.session.get('become_user', None):
            content.append(Li(
                A(
                    ' '.join([
                        str(_('Back to your account')),
                        request.session['become_user_realname'],
                    ]),
                    href=reverse('crudlfap:su'),
                )
            ))

        return super().to_html(MDCList(*content))


class mdcAppContent(Div):
    def __init__(self, *content):
        super().__init__(
            Component(
                *content,
                tag='main',
                cls='main-content',
                id='main-content',
            ),
            cls='mdc-drawer-app-content mdc-top-app-bar--fixed-adjust',
        )


class mdcSwitch(Component):
    def __init__(
        self, name, label=None, value=None, type=None, errors=None, help=None,
        required=False,
    ):
        super().__init__(
            Div(
                Div(cls='mdc-switch__track'),
                Div(
                    Div(cls='mdc-switch__thumb'),
                    Input(
                        type='checkbox',
                        id='id_' + name,
                        role='switch',
                        aria_checked='true' if bool(value) else '',
                        cls='mdc-switch__native-control',
                        checked=bool(value)
                    ),
                    cls='mdc-switch__thumb-underlay',
                ),
                cls='mdc-switch mdc-switch--checked',
                data_mdc_auto_init='MDCSwitch',
            ),
            Label(
                label or name.capitalize(),
                **{'for': 'id_' + name},
            )
        )