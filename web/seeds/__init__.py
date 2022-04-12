from web.controllers import articles
from django.db import transaction


def _create_article(full_name, content):
    article = articles.create_article(full_name)
    ver = articles.create_article_version(article, content)
    return ver


@transaction.atomic
def run():
    _create_article('nav:top', """
[[module ListPages range="." limit="1"]]
[[div class="top-bar"]]
* [# Объекты]
 * [[[scp-list | Объекты 001-999]]]
 * [[[scp-list-2 | Объекты 1000-1999]]]
 * [[[scp-list-3 | Объекты 2000-2999]]]
 * [[[scp-list-4 | Объекты 3000-3999]]]
 * [[[scp-list-5 | Объекты 4000-4999]]]
 * [[[scp-list-6 | Объекты 5000-5999]]]
 * [[[scp-list-7 | Объекты 6000-6999]]]
 * [[[scp-list-ru| Объекты Российского филиала]]]
 * [[[scp-list-fr|Объекты Французского филиала]]]
 * [[[scp-list-jp|Объекты Японского филиала]]]
 * [[[scp-list-es|Объекты Испанского филиала]]]
 * [[[scp-list-pl|Объекты Польского филиала]]]
 * [[[scp-list-ua|Объекты Украинского филиала]]]
 * [[[scp-list-others|Объекты других филиалов]]]
 * [[[scp-list-j | Шуточные объекты]]]
 * [[[explained-list | Обоснованные объекты]]]
 * [[[licensing-page | Авторство работ]]]
 * [[[archived-scps | Архив]]]
* [# Материалы]
 * [[[artwork:russian-art-hub |Арт-Хаб SCP-RU]]]
 * [[[site-7-media-hub |SCP-RU в медиапроектах]]]
 * [[[stories |Рассказы]]]
 * [[[contests |Архив конкурсов]]]
 * [[[news-archive |Архив новостей]]]
 * [[[history-of-the-universe-hub |История Фонда]]]
 * [[[logs-of-anomalies|Списки аномалий]]]
 * [[[canon-hub |Канон-хаб]]]
 * [[[interactives-list |Интерактивные материалы]]]
 * [[[the-leak |За кадром]]]
 * [[[site-7-midnight-radio |Site 7 Midnight Radio]]]
 * [[[other |Прочие материалы]]]
* [# Об Организации]
 * [[[about-the-scp-foundation |Общая информация]]]
 * [[[object-classes |Классы объектов]]]
 * [[[security-clearance-levels |Уровни допуска]]]
 * [[[foundation-counterparts |Филиалы Фонда SCP]]]
 * [[[secure-facilities-locations |Учреждения]]]
 * [[[task-forces |Опергруппы]]]
 * [[[mtf-equipment |Снаряжение МОГ и СБ]]]
 * [[[vehicle-list |Стандартная техника МОГ и СБ]]]
 * [[[standard-cell|Камеры содержания]]]
 * [[[authors-pages |Персонал]]]
 * [[[list-of-foundation-s-internal-departments |Внутренние службы ]]]
 * [[[groups-of-interest |Связанные организации]]]
 * [[[amnesiac-classification |Классификация амнезиаков]]]
 * [[[scp-objects-classification |Системы стандартизации]]]
 * [[[special-events-classification |Классификация особых событий]]]
* [# Руководства]
 * [[[sandbox:main|Правила Полигона]]]
 * [[[faq |FAQ]]]
 * [[[how-to-write-an-scp |Как написать SCP-объект]]]
 * [[[scp-template |Оформление и глоссарий]]]
 * [[[tag-guide | Руководство по тегам]]]
 * [[[the-big-list-of-overdone-scp-cliches|Список избитых штампов]]]
 * [[[essays|Очерки]]]
* [# Переход]
 * [[a href="http://scp-ru.wikidot.com/%%fullname%%"]]SCP-RU.WIKIDOT.COM[[/a]]
 * [http://scpsandbox.wikidot.com Старый Полигон]
 * [http://wanderers-library.wikidot.com Библиотека Странников]
 * [http://vk.com/scpfanpage Группа ВКонтакте]
 * [http://t.me/scpfoundation Телеграмм-канал SCP]
 * [http://twitter.com/scprussia Твиттер SCP]
 * [[[translations-planning|Планы на перевод]]]
 * [[[_admin |Управление сайтом]]]
* [# Новое]
 * [[[most-recently-created |Статьи]]]
 * [[[most-recently-edited |Правки]]]
 * [[[forum:recent-posts|Сообщения]]]
* [[[contacts|Контакты]]]
[[/div]]

[[div class="mobile-top-bar"]]

[[div class="open-menu"]]
[#side-bar ≡]
[[/div]]
* [# Объекты]
 * [[[scp-list | Объекты 001-999]]]
 * [[[scp-list-2 | Объекты 1000-1999]]]
 * [[[scp-list-3 | Объекты 2000-2999]]]
 * [[[scp-list-4 | Объекты 3000-3999]]]
 * [[[scp-list-5 | Объекты 4000-4999]]]
 * [[[scp-list-6 | Объекты 5000-5999]]]
 * [[[scp-list-7 | Объекты 6000-6999]]]
 * [[[scp-list-ru| Объекты Российского филиала]]]
 * [[[scp-list-fr|Объекты Французского филиала]]]
 * [[[scp-list-jp|Объекты Японского филиала]]]
 * [[[scp-list-es|Объекты Испанского филиала]]]
 * [[[scp-list-pl|Объекты Польского филиала]]]
 * [[[scp-list-ua|Объекты Украинского филиала]]]
 * [[[scp-list-others|Объекты других филиалов]]]
 * [[[scp-list-j | Шуточные объекты]]]
 * [[[explained-list | Обоснованные объекты]]]
 * [[[licensing-page | Авторство работ]]]
 * [[[archived-scps | Архив]]]
* [# Материалы]
 * [[[artwork:russian-art-hub |Арт-Хаб SCP-RU]]]
 * [[[site-7-media-hub |Медиахаб Зоны 7]]]
 * [[[stories |Рассказы]]]
 * [[[contests |Архив конкурсов]]]
 * [[[history-of-the-universe-hub |История Фонда]]]
 * [[[logs-of-anomalies|Списки аномалий]]]
 * [[[goi-hub |Материалы Связанных Организаций]]]
 * [[[canon-hub |Канон-хаб]]]
 * [[[interactives-list |Интерактивные материалы]]]
 * [[[the-leak |За кадром]]]
 * [[[site-7-midnight-radio |Site 7 Midnight Radio]]]
 * [[[news-archive |Архив новостей]]]
 * [[[other |Прочие материалы]]]
* [# Об Организации]
 * [[[about-the-scp-foundation |Общая информация]]]
 * [[[object-classes |Классы объектов]]]
 * [[[security-clearance-levels |Уровни допуска]]]
 * [[[foundation-counterparts |Филиалы Фонда SCP]]]
 * [[[secure-facilities-locations |Учреждения]]]
 * [[[task-forces |Опергруппы]]]
 * [[[mtf-equipment |Снаряжение МОГ и СБ]]]
 * [[[vehicle-list |Стандартная техника МОГ и СБ]]]
 * [[[standard-cell|Камеры содержания]]]
 * [[[authors-pages |Персонал]]]
 * [[[list-of-foundation-s-internal-departments |Внутренние службы ]]]
 * [[[groups-of-interest |Связанные организации]]]
 * [[[amnesiac-classification |Классификация амнезиаков]]]
 * [[[special-events-classification |Классификация особых событий]]]
 * [[[scp-objects-classification |Системы стандартизации]]]
* [# Руководства]
 * [[[sandbox:main|Правила Полигона]]]
 * [[[faq |FAQ]]]
 * [[[how-to-write-an-scp |Как написать SCP-объект]]]
 * [[[scp-template |Оформление и глоссарий]]]
 * [[[tag-guide | Руководство по тегам]]]
 * [[[the-big-list-of-overdone-scp-cliches|Список избитых штампов]]]
 * [[[essays|Очерки]]]
* [# Переход]
 * [[a href="http://scp-ru.wikidot.com/%%fullname%%"]]SCP-RU.WIKIDOT.COM[[/a]]
 * [http://scpsandbox.wikidot.com Старый Полигон]
 * [http://wanderers-library.wikidot.com Библиотека Странников]
 * [http://vk.com/scpfanpage Группа ВКонтакте]
 * [http://t.me/scpfoundation Телеграмм-канал SCP]
 * [http://twitter.com/scprussia Твиттер SCP]
 * [[[terminal|Терминал]]]
 * [[[translations-planning|Планы на перевод]]]
 * [[[chat|Чат]]]
 * [[[_admin |Управление сайтом]]]
* [[[contacts|Контакты]]]
[[/div]]
[[/module]]
    """)

    _create_article('nav:side', """
[[div id="u-become-member"]]
[[div class="menu-item"]]
[[image expand.png]][[[system:join|Стать участником]]]
[[/div]]
[[/div]]

[[div class="side-block"]]

[[div class="menu-item"]]
[[image letter.png]][[[news|Новости]]]
[[/div]]

[[div class="heading"]]
SCP-объекты
[[/div]]
[[div class="menu-item"]]
[[image series.png]][[[scp-series|Объекты I]]] [[span class="sub-text"]](001-999)[[/span]]
[[/div]]
[[div class="menu-item"]]
[[image series.png]][[[scp-series-2|Объекты II]]] [[span class="sub-text"]](1000-1999)[[/span]]
[[/div]]
[[div class="menu-item"]]
[[image series.png]][[[scp-series-3|Объекты III]]] [[span class="sub-text"]](2000-2999)[[/span]]
[[/div]]
[[div class="menu-item"]]
[[image series.png]][[[scp-series-4|Объекты IV]]] [[span class="sub-text"]](3000-3999)[[/span]]
[[/div]]
[[div class="menu-item"]]
[[image series.png]][[[scp-series-5|Объекты V]]] [[span class="sub-text"]](4000-4999)[[/span]]
[[/div]]
[[div class="menu-item"]]
[[image series.png]][[[scp-series-6|Объекты VI]]] [[span class="sub-text"]](5000-5999)[[/span]]
[[/div]]
[[div class="menu-item"]]
[[image series.png]][[[scp-series-7|Объекты VII]]] [[span class="sub-text"]](6000-6999)[[/span]]
[[/div]]

[[div class="menu-item"]]
[[image series.png]][[[scp-list-ru|Объекты RU]]] [[span class="sub-text"]](1001-1999)[[/span]]
[[/div]]

[[div class="heading"]]
Рассказы по объектам
[[/div]]

[[div class="menu-item small" style="grid-template-columns: 100% !important; max-height: max-content !important; height: auto !important; display: flex;"]]
[[image series.png]][[[scp-series-1-tales-edition|I]]] - [[[scp-series-2-tales-edition|II]]] - [[[scp-series-3-tales-edition|III]]] - [[[scp-series-4-tales-edition|IV]]] - [[[scp-series-5-tales-edition|V]]] - [[[scp-series-6-tales-edition|VI]]]
[[/div]]

[[div class="heading"]]
SCP-библиотека
[[/div]]
[[div class="menu-item"]]
[[image series.png]][[[stories|Список рассказов]]]
[[/div]]
[[div class="menu-item"]]
[[image series.png]][[[canon-hub|Канон-хаб]]]
[[/div]]
[[div class="menu-item"]]
[[image series.png]][[[groups-of-interest|Материалы СО]]]
[[/div]]
[[div class="menu-item"]]
[[image series.png]][[[logs-of-anomalies|Списки аномалий]]]
[[/div]]
[[div class="menu-item"]]
[[image series.png]][[[site-7-media-archive|Медиаархив]]]
[[/div]]
[[div class="menu-item"]]
[[image series.png]][[[artwork:russian-art-hub|Арт-Хаб SCP-RU]]]
[[/div]]


[[div class="heading"]]
Сайт
[[/div]]
[[div class="menu-item"]]
[[image help.png]][[[faq|FAQ]]]
[[/div]]
[[div class="menu-item"]]
[[image main.png]][[[random:random-page|Случайная статья]]]
[[/div]]
[[div class="menu-item"]]
[[image default.png]][[[top-rated-pages|Статьи по рейтингу]]]
[[/div]]
[[div class="menu-item"]]
[[image main.png]][[[most-recently-edited|Правки Основного]]]
[[/div]]
[[div class="menu-item sub-item"]]
[[image default.png]][[[most-recently-created|Новые статьи]]]
[[/div]]

[[div class="heading"]]
Сообщество
[[/div]]
[[div class="menu-item"]]
[[image forum.png]][[[forum:start|Форум]]]
[[/div]]
[[div class="menu-item sub-item"]]
[[image default.png]][[[forum:recent-posts|Новые сообщения]]]
[[/div]]

[[/div]]

[[div class="side-block"]]

[[div class="heading"]]
Полигон
[[/div]]
[[div class="menu-item"]]
[[image main.png]][[[sandbox:main|Правила]]]
[[/div]]
[[div class="menu-item sub-item"]]
[[image series.png]][[[scp-sandboxed-list|Список статей]]]
[[/div]]
[[div class="menu-item sub-item"]]
[[image series.png]][[[most-recently-sandboxed|Новые статьи]]]
[[/div]]
[[div class="menu-item sub-item"]]
[[image series.png]][[[translations-planning|Планы на перевод]]]
[[/div]]
[[div class="menu-item sub-item"]]
[[image series.png]][[[sandbox:not-translated|Объекты без перевода]]]
[[/div]]
[[div class="menu-item sub-item"]]
[[image series.png]][[[sandbox:drafts2| Черновики]]]
[[/div]]
[[module ListUsers users="."]]
[[div class="menu-item sub-item"]]
[[image http://scp-ru.wikidot.com/local--files/nav:side/default.png]][[[draft:%%name%%| Мой черновик]]]
[[/div]]
[[/module]]
[[div class="menu-item sub-item"]]
[[image series.png]][[[moderation-page-control|К просмотру АМС]]]
[[/div]]
[[div class="menu-item sub-item"]]
[[image series.png]][[[http://scp-ru.wikidot.com/system:page-tags/tag/к_вычитке|К вычитке]]]
[[/div]]
[[div class="menu-item sub-item"]]
[[image series.png]][[[sandbox:deleted2| Удалённые]]]
[[/div]]
-----
[[div class="menu-item sub-item"]]
[[image default.png]][[[new-page-ru|Создать статью]]]
[[/div]]

[[/div]]
-----
[[div class="side-block"]]
+++++ [[[system:page-tags | Теги]]] | [[[tags | Поиск]]]

[[collapsible show="+ Облако тегов" hide="- Облако тегов"]]
[[module TagCloud minFontSize="80%" maxFontSize="200%"  maxColor="8,8,64" minColor="100,100,128" target="system:page-tags" limit="30"]]
[[/collapsible]]

[[div style="font-size:70%;color:#888;margin-top:7px"]]
© SCP Foundation Russia
Возрастное ограничение: **18+**
Авторство: [[[licensing |объекты]]], [[[licensing-ru|ru-объекты]]], [[[the-archives|рассказы Библиотеки]]]
[[/div]]

[[/div]]

[[a href="##" class="close-menu"]]
[[image /component:theme/black.png style="z-index:-1; opacity: 0.3;"]]
[[/a]]

[[module ListUsers users="."]]
    [[image https://m.scpfoundation.net/wikidot/hit?wiki=scp-ru&uid=%%number%% style="position:absolute; left:-9999px;"]]
[[/module]]

[[div class="scpnet-interwiki-wrapper"]]
[[module ListPages range="." limit="1"]]
      [[iframe http://interwiki.scpdb.org/?wiki=scp-ru&lang=ru&page=%%category%%:%%name%% class="scpnet-interwiki-frame"]]
[[/module]]
[[/div]]
    """)

    if articles.get_article('main') is not None:
        return

    _create_article('main', """
[[div class="welcome-warning"]]
##600|Далее представлены материалы различной степени секретности.##\

##600|Ведётся наблюдение, нарушения режима секретности отслеживаются и караются.##\

##600|Других предупреждений не будет.##
[[/div]]

@@@@

[[div class="scp-other-branches" style="background:#f1f1f1"]]
  [[div class="scp-featured__title"]]
   [/artscp Официальная позиция SCP Russia по вопросу лицензионного кризиса] & [https://m.vk.com/@scpint-standwithscpru Позиция SCP INT]

   **[https://www.gofundme.com/f/scp-legal-funds Сбор средств на юридическую защиту Фонда]**
  [[/div]]
[[/div]]
@@@@

[[div class="scp-other-branches" style="background:#f1f1f1"]]
  [[div class="scp-featured__title"]]
   [/faq#toc1 Не могу войти в аккаунт. Что делать? (пункт 2.9 FAQ)]
  [[/div]]
[[/div]]
@@@@

[[div class="scp-other-branches" style="background:#f1f1f1"]]
  [[div class="scp-featured__title"]]
   [/what-makes-the-blood-run-cold Конкурс №19: Истоки жанра — От чего кровь стынет в жилах]
  [[/div]]
[[/div]]
@@@@



@@@@





[[div class="scp-featured"]]

[!-- FEATURED_DAILY_START --]
[[div class="scp-featured__block scp-featured__block_type_daily"]]
  [[div class="scp-featured__title"]]
    Объект дня
  [[/div]]
  [[div class="scp-featured__page-title"]]
    [/scp-1242-ru SCP-1242-RU - Рейстрэкские подражатели]
  [[/div]]
  [[div class="scp-featured__content"]]
  [[/div]]

  [[div class="scp-featured__previous"]]
    [[span class="scp-featured__previous-title"]]Предыдущие дни:[[/span]]
      - [/scp-3166 SCP-3166 - Гарфилд, ты даже не представляешь, насколько ты одинок]
- [/scp-6400 SCP-6400 - Там, снаружи]
- [/scp-6470 SCP-6470 - Вездесущий]
  [[/div]]
[[/div]]
[!-- FEATURED_DAILY_END --]

[!-- FEATURED_WEEKLY_START --]
[[div class="scp-featured__block"]]
  [[div class="scp-featured__title"]]
    Статья недели
  [[/div]]
  [[div class="scp-featured__page-title"]]
    [/SCP-1252-RU/ SCP-1252-RU - Начни заново ]
  [[/div]]
  [[div class="scp-featured__content"]]

SCP-1252 – это 5 каменных построек, предположительно имеющих изначально религиозное назначение. Архитектура указывает на принадлежность к народу Египта, а создание приходится на 230-220 г. до н.э, во время правления Птолемея Эвергета. Несмотря на этот факт, все объекты находятся на значительном расстоянии друг от друга, в местах, где в тот период времени существовали Египет, Понт, Вифиния, Македония и Афины, и обозначены как SCP-1252-Е, SCP-1252-П, SCP-1252-В, SCP-1252-М и SCP-1252-А.
 [[/div]]
[[/div]]
[!-- FEATURED_WEEKLY_END --]

[[/div]]

[[module CSS]]
.scp-list-translations p {
  margin: 0;
}
[[/module]]
[[div class="scp-other-branches" style="text-align: left; padding-bottom: 0"]]

[[div class="scp-featured__title" style="margin-bottom: 12px;"]]
Новые переводы
[[/div]]

[[div style="display: flex; flex-wrap: wrap; width: 100%; margin: 0 -8px"]]

[[div style="min-width: min(100vw, 400px); flex-basis: 50%; box-sizing: border-box; padding: 0 8px; margin-bottom: 18px" class="scp-list-translations"]]
[[module ListPages category="_default, wl" order="created_at desc" separate="false" offset="0" limit="5" tags="объект рассказ -ru -ru-tale"]]
%%title_linked%%
[[div style="font-size: 80%; font-weight: bold; font-style: italic; opacity: 0.6"]]
Добавлен %%created_at|%d.%m.%Y %%
[[/div]]
[[/module]]
[[/div]]
[[div style="min-width: min(100vw, 400px); flex-basis: 50%; box-sizing: border-box; padding: 0 8px; margin-bottom: 18px" class="scp-list-translations"]]
[[module ListPages category="_default, wl" order="created_at desc" separate="false" offset="5" limit="5" tags="объект рассказ -ru -ru-tale"]]
%%title_linked%%
[[div style="font-size: 80%; font-weight: bold; font-style: italic; opacity: 0.6"]]
Добавлен %%created_at|%d.%m.%Y %%
[[/div]]
[[/module]]
[[/div]]

[[/div]]

[[/div]]


[[div class="scp-featured"]]

[[div class="scp-featured__block scp-featured__block_type_gold"]]
  [[div class="scp-featured__title"]]
    Избранные объекты Российского Филиала
  [[/div]]
  [[div class="scp-featured__page-title"]]
- [[[scp-1031-ru|SCP-1031-RU]]] — Линия ускользания
- [[[scp-1117-ru|SCP-1117-RU]]] — Люди на холме
- [[[scp-1204-ru|SCP-1204-RU]]] — Бесконечная видеокассета
- [[[scp-1216-ru|SCP-1216-RU]]] — Врата рая
- [[[scp-1223-ru|SCP-1223-RU]]] — Эне-тоо
- [[[scp-1259-ru|SCP-1259-RU]]] — Комплекс «Орион»
- [[[scp-1263-ru|SCP-1263-RU]]] — <<Грибной Государь>>
- [[[scp-1311-ru|SCP-1311-RU]]] — В синем море, в белой пене
- [[[scp-1314-ru|SCP-1314-RU]]] — Не все слова исчезнут в пустоте
- [[[scp-1370-ru|SCP-1370-RU]]] — Господин Режиссёр
- [[[scp-1373-ru|SCP-1373-RU]]] — С.С.Д.
- [[[scp-1393-ru|SCP-1393-RU]]] — Тишь да гладь
- [[[scp-2195|SCP-2195-RU]]] — Сыны нации
  [[/div]]

  [[div class="scp-featured__title scp-featured__title_type_secondary"]]
    Избранные рассказы Российского Филиала
  [[/div]]

  [[div class="scp-featured__page-title"]]
- [[[trees-flowers-and-fruits | Деревья, цветы и плоды]]]
- [[[screams-that-no-one-can-hear | Крики, что никто не слышит]]]
- [[[class-d-recruiting | Набор персонала класса D]]]
- [[[live-air | Прямой эфир]]]
- [[[skeletons |Скелетики]]]
- [[[scp-003-h|SCP-003-H - Нормальность превыше всего]]]
  [[/div]]
[[/div]]

[[div class="scp-featured__block scp-featured__block_type_gold"]]
  [[div class="scp-featured__title"]]
    Избранные объекты SCP Foundation
  [[/div]]
  [[div class="scp-featured__page-title"]]
- [[[SCP-186]]] — Покончить с войнами
- [[[SCP-1193]]] — Погребённый гигант
- [[[SCP-1562]]] — Горка с туннелем
- [[[SCP-1732]]] — Септимий Лев
- [[[SCP-1861]]] — Команда подлодки «Винтерсхаймер»
- [[[SCP-1959]]] — Пропавший космонавт
- [[[SCP-1981]]] — «РОНАЛЬДА РЕЙГАНА ИЗРЕЗАЛИ ВО ВРЕМЯ РЕЧИ»
- [[[SCP-2669]]] — Кебтеул-1
- [[[SCP-2935]]] — О Смерть
- [[[SCP-3008]]] — Абсолютно нормальная старая добрая Икея
- [[[SCP-3515]]] — Самокопание
- [[[SCP-5031]]] — Очередной опасный монстр
- [[[SCP-8900-EX]]] — Синее небо над головой
  [[/div]]

  [[div class="scp-featured__title scp-featured__title_type_secondary"]]
    Избранные рассказы SCP Foundation
  [[/div]]

  [[div class="scp-featured__page-title"]]
- [[[introductory-antimemetics|Вводный курс антимеметики ]]]
- [[[and-it-starts-with-a-song|В начале была песнь]]]
- [[[lord-blackwood-and-the-great-tarasque-hunt-of-83| Лорд Блэквуд и великая охота на Тараска лета восемьдесят третьего]]]
- [[[when-in-doubt-poke-it-with-a-stick|Мы тыкаем палочками]]]
- [[[naptime|Тихий час]]]
  [[/div]]
[[/div]]


[[/div]]



[[div class="scp-other-branches"]]

[[div class="scp-featured__title" style="margin-bottom: 12px;"]]
Филиалы других стран
[[/div]]

[[image de.png style="box-shadow: 0 1px 3px rgba(0,0,0,.5);"]]@<&nbsp;>@**[http://scp-wiki-de.wikidot.com/ Германия]**@<&nbsp;>@@<&nbsp;>@@<&nbsp;>@[[image es.png style="box-shadow: 0 1px 3px rgba(0,0,0,.5);"]]@<&nbsp;>@**[http://lafundacionscp.wikidot.com/ Испания]**@<&nbsp;>@@<&nbsp;>@@<&nbsp;>@[[image it.png style="box-shadow: 0 1px 3px rgba(0,0,0,.5);"]]@<&nbsp;>@**[http://fondazionescp.wikidot.com/ Италия]**@<&nbsp;>@@<&nbsp;>@@<&nbsp;>@[[image cn.png style="box-shadow: 0 1px 3px rgba(0,0,0,.5);"]]@<&nbsp;>@**[http://scp-wiki-cn.wikidot.com/ Китай]**@<&nbsp;>@@<&nbsp;>@@<&nbsp;>@[[image kr.png style="box-shadow: 0 1px 3px rgba(0,0,0,.5);"]]@<&nbsp;>@**[http://ko.scp-wiki.net/ Корея]**@<&nbsp;>@@<&nbsp;>@@<&nbsp;>@[[image pl.png style="box-shadow: 0 1px 3px rgba(0,0,0,.5);"]]@<&nbsp;>@**[http://scp-pl.wikidot.com/ Польша]**@<&nbsp;>@@<&nbsp;>@@<&nbsp;>@[[image pt.png style="box-shadow: 0 1px 3px rgba(0,0,0,.5);"]]@<&nbsp;>@**[http://scp-pt-br.wikidot.com/ Португалия]**
@@ @@
[[image us.png style="box-shadow: 0 1px 3px rgba(0,0,0,.5);"]]@<&nbsp;>@**[http://www.scp-wiki.net/ США]**@<&nbsp;>@@<&nbsp;>@@<&nbsp;>@[[image th.png style="box-shadow: 0 1px 3px rgba(0,0,0,.5);"]]@<&nbsp;>@**[http://scp-th.wikidot.com/ Таиланд]**@<&nbsp;>@@<&nbsp;>@@<&nbsp;>@[[image fr.png style="box-shadow: 0 1px 3px rgba(0,0,0,.5);"]]@<&nbsp;>@**[http://fondationscp.wikidot.com/ Франция]**@<&nbsp;>@@<&nbsp;>@@<&nbsp;>@[[image ua.png style="box-shadow: 0 1px 3px rgba(0,0,0,.5);"]]@<&nbsp;>@**[http://scp-ukrainian.wikidot.com/ Украина]**@<&nbsp;>@@<&nbsp;>@@<&nbsp;>@[[image cz.png style="box-shadow: 0 1px 3px rgba(0,0,0,.5);"]]@<&nbsp;>@**[http://scp-cs.wikidot.com/ Чехия]**@<&nbsp;>@@<&nbsp;>@@<&nbsp;>@[[image jp.png style="box-shadow: 0 1px 3px rgba(0,0,0,.5);"]]@<&nbsp;>@**[http://ja.scp-wiki.net/ Япония]**
@@ @@
[[image zn.png style="box-shadow: 0 1px 3px rgba(0,0,0,.5);"]]@<&nbsp;>@**[http://scp-zh-tr.wikidot.com/ Традиционный китайский язык]**@<&nbsp;>@@<&nbsp;>@@<&nbsp;>@[[image vn.png style="box-shadow: 0 1px 3px rgba(0,0,0,.5);"]]@<&nbsp;>@**[http://scp-vn.wikidot.com/ Вьетнам]**


[[div class="scp-featured__title" style="margin-bottom: 12px; margin-top: 30px;"]]
Международный архив переводов
[[/div]]

[[image int.png style="box-shadow: 0 1px 3px rgba(0,0,0,.5);"]]@<&nbsp;>@**[http://scp-int.wikidot.com/ SCP International]**

[[/div]]
    """)
