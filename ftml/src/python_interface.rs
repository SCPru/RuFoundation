use std::borrow::Cow;
use std::borrow::Cow::Borrowed;
use std::collections::HashMap;
use std::fmt::{Debug, Formatter};
use std::rc::Rc;

use pyo3::prelude::*;

use crate::info::VERSION;
use crate::prelude::*;
use crate::render::html::HtmlRender;
use crate::render::text::TextRender;

fn render<R: Render>(text: &mut String, renderer: &R, page_info: PageInfo, callbacks: Py<PyAny>) -> R::Output
{
    // TODO includer
    let settings = WikitextSettings::from_mode(WikitextMode::Page);

    let page_callbacks = Rc::new(PythonCallbacks{ callbacks: Box::new(callbacks) }).clone();

    preprocess(text);
    let tokens = tokenize(text);
    let (tree, _warnings) = parse(&tokens, &page_info, page_callbacks.clone(), &settings).into();
    let output = renderer.render(&tree, &page_info, page_callbacks.clone(), &settings);
    output
}


fn page_info_dummy() -> PageInfo<'static>
{
    PageInfo {
        page: Borrowed("some-page"),
        category: None,
        site: Borrowed("sandbox"),
        title: Borrowed("title"),
        alt_title: None,
        rating: 0.0,
        tags: vec![],
        language: Borrowed("default")
    }
}

struct PythonCallbacks {
    callbacks: Box<Py<PyAny>>,
}

impl Debug for PythonCallbacks {
    fn fmt(&self, f: &mut Formatter<'_>) -> std::fmt::Result {
        write!(f, "<PythonCallbacks>")
    }
}

impl PageCallbacks for PythonCallbacks {
    fn module_has_body(&self, module_name: Cow<str>) -> bool {
        let result = Python::with_gil(|py| {
            return self.callbacks.getattr(py, "module_has_body")?.call(py, (module_name,), None)?.extract(py);
        });
        match result {
            Ok(result) => result,
            Err(_) => false
        }
    }

    fn render_module(&self, module_name: Cow<str>, params: HashMap<Cow<str>, Cow<str>>, body: Cow<str>) -> Cow<'static, str> {
        let py_params: HashMap<String, String> = params.keys().fold(HashMap::new(), |mut acc, k| {
            acc.insert(k.to_string(), params.get(k).unwrap().to_string());
            acc
        });
        let result: PyResult<String> = Python::with_gil(|py| {
            return self.callbacks.getattr(py, "render_module")?.call(py, (module_name, py_params, body), None)?.extract(py);
        });
        match result {
            Ok(result) => Cow::from(result.as_str().to_owned()),
            Err(_) => Cow::from("")
        }
    }
}


#[pyclass(subclass)]
struct Callbacks {}

#[pymethods]
impl Callbacks {
    #[new]
    fn new() -> Self {
        Callbacks{}
    }

    pub fn module_has_body(&self, _module_name: String) -> PyResult<bool> {
        return Ok(false)
    }

    pub fn render_module(&self, _module_name: String, _params: HashMap<String, String>, _body: String) -> PyResult<String> {
        return Ok("".to_string())
    }
}

#[pyfunction(kwargs="**")]
fn render_html(source: String, callbacks: Py<PyAny>) -> PyResult<HashMap<String, String>>
{
    let html_output = render(&mut source.to_string(), &HtmlRender, page_info_dummy(), callbacks);

    let mut output = HashMap::new();
    output.insert(String::from("body"), html_output.body);
    output.insert(String::from("style"), html_output.styles.join("\n"));

    Ok(output)
}


#[pyfunction(kwargs="**")]
fn render_text(source: String, callbacks: Py<PyAny>) -> PyResult<String>
{
    Ok(render(&mut source.to_string(), &TextRender, page_info_dummy(), callbacks))
}


#[pymodule]
fn ftml(_py: Python, m: &PyModule) -> PyResult<()> {

    m.add("ftml_version", VERSION.to_string())?;
    m.add_function(wrap_pyfunction!(render_html, m)?)?;
    m.add_function(wrap_pyfunction!(render_text, m)?)?;
    m.add_class::<Callbacks>()?;

    Ok(())
}

////
#[test]
fn test_main() {
    let main_code = r#"

    [[toc]]

    ++ Условные обозначения
    [[image na.png]] — Не назначен или нейтрализован
    [[image safe.png]] — [[[safe|Безопасный]]]
    [[image euclid.png]] — [[[euclid|Евклид]]]
    [[image keter.png]] — [[[keter|Кетер]]]
    [[image thaumiel.png]] — [[[object-class-thaumiel|Таумиэль]]]
    [[image nonstandard.png]] — [[[nonstandard|Нестандартный класс]]]
    
    ++ 001-099
    [[image na.png]] [[[SCP-001]]] — Ожидает рассекречивания [Заблокировано]
    [[image euclid.png]] [[[SCP-002]]] — «Живая» комната
    [[image euclid.png]] [[[SCP-003]]] — Биологическая материнская плата
    [[image euclid.png]] [[[SCP-004]]] — 12 ржавых ключей и дверь
    [[image safe.png]] [[[SCP-005]]] — Отмычка
    [[image safe.png]] [[[SCP-006]]] — Источник молодости
    [[image euclid.png]] [[[SCP-007]]] — Планета в животе
    [[image euclid.png]] [[[SCP-008]]] — Чума зомби
    [[image euclid.png]] [[[SCP-009]]] — Красный лед 
    [[image safe.png]] [[[SCP-010]]] — Ошейники подчинения
    [[image safe.png]] [[[SCP-011]]] — Разумный памятник участникам Гражданской войны
    [[image euclid.png]] [[[SCP-012]]] — Скверная мелодия
    [[image safe.png]] [[[SCP-013]]] — Сигареты «Blue Lady»
    [[image safe.png]] [[[SCP-014]]] — Каменный человек
    [[image euclid.png]] [[[SCP-015]]] — Ужасный трубопровод
    [[image keter.png]] [[[SCP-016]]] — Разумный вирус
    [[image keter.png]] [[[SCP-017]]] — «Тень» человека
    [[image euclid.png]] [[[SCP-018]]] — Мяч «Super Ball»
    [[image keter.png]] [[[SCP-019]]] — Чудовищная ваза
    [[image keter.png]] [[[SCP-020]]] — Незримая плесень
    [[image safe.png]] [[[SCP-021]]] — Подкожный Змей
    [[image euclid.png]] [[[SCP-022]]] — Морг
    [[image euclid.png]] [[[SCP-023]]] — Чёрный пёс
    [[image euclid.png]] [[[SCP-024]]] — Смертельное игровое шоу
    [[image safe.png]] [[[SCP-025]]] — Шкаф с поношенными вещами
    [[image euclid.png]] [[[SCP-026]]] — Оставшиеся после уроков
    [[image euclid.png]] [[[SCP-027]]] — Повелитель мух
    [[image safe.png]] [[[SCP-028]]] — Знание
    [[image keter.png]] [[[SCP-029]]] — Дочь теней
    [[image safe.png]] [[[SCP-030]]] — Гомункул
    [[image euclid.png]] [[[SCP-031]]] — Что такое любовь?
    [[image euclid.png]] [[[SCP-032]]] — Невеста Братьев
    [[image euclid.png]] [[[SCP-033]]] — Пропущенное число
    [[image safe.png]] [[[SCP-034]]] — Обсидиановый ритуальный нож
    [[image keter.png]] [[[SCP-035]]] — Маска одержимости
    [[image safe.png]] [[[SCP-036]]] — Паломничество Перевоплощения езидов
    [[image safe.png]] [[[SCP-038]]] — Дерево всего
    [[image euclid.png]] [[[SCP-040]]] — Дитя эволюции
    [[image safe.png]] [[[SCP-041]]] — Мыслевещатель
    [[image safe.png]] [[[SCP-042]]] — Некогда крылатая лошадь
    [[image safe.png]] [[[SCP-043]]] — The Beatle
    [[image safe.png]] [[[SCP-044]]] — Пушка Молекулярного Расщепления времён ВОВ
    [[image safe.png]] [[[SCP-045]]] — Преобразователь атмосферы
    [[image euclid.png]] [[[SCP-046]]] — «Хищные» заросли остролиста
    [[image keter.png]] [[[SCP-047]]] — Микробиологический мутаген
    [[image na.png]] [[[SCP-048]]] — Проклятый номер SCP
    [[image euclid.png]] [[[SCP-049]]] — Чумной доктор
    [[image euclid.png]] [[[SCP-050]]] — Самому умному
    [[image safe.png]] [[[SCP-051]]] — Японское пособие по акушерству
    [[image euclid.png]] [[[SCP-052]]] — Поезд, идущий сквозь время
    [[image euclid.png]] [[[SCP-053]]] — Маленькая девочка
    [[image safe.png]] [[[SCP-054]]] — Наяда
    [[image keter.png]] [[[SCP-055]]] — [неизвестно]
    [[image euclid.png]] [[[SCP-056]]] — Симпатяга
    [[image safe.png]] [[[SCP-057]]] — Всё перетрут
    [[image keter.png]] [[[SCP-058]]] — Сердце тьмы
    [[image keter.png]] [[[SCP-059]]] — Радиоактивный минерал
    [[image keter.png]] [[[SCP-060]]] — Инфернальный оккультный скелет
    [[image safe.png]] [[[SCP-061]]] — Акустический контроль над сознанием
    [[image euclid.png]] [[[SCP-062]]] — Квантовый компьютер
    [[image safe.png]] [[[SCP-063]]] — «Лучшая В Мире Зубная Щотка»
    [[image safe.png]] [[[SCP-064]]] — Дефектная структура фон Неймана
    [[image euclid.png]] [[[SCP-065]]] — Поле искажения органики
    [[image euclid.png]] [[[SCP-066]]] — Игрушка Эрика
    [[image safe.png]] [[[SCP-067]]] — Перо Мастера
    [[image euclid.png]] [[[SCP-068]]] — Проволочная фигурка
    [[image safe.png]] [[[SCP-069]]] — «Второй шанс»
    [[image safe.png]] [[[SCP-070]]] — «Железнокрылый»
    [[image euclid.png]] [[[SCP-071]]] — Дегенеративная метаморфная сущность
    [[image safe.png]] [[[SCP-072]]] — Ножки кровати 
    [[image euclid.png]] [[[SCP-073]]] — «Каин»
    [[image euclid.png]] [[[SCP-074]]] — Квантовая мокрица
    [[image euclid.png]] [[[SCP-075]]] — Едкая улитка
    [[image keter.png]] [[[SCP-076]]] — «Авель»
    [[image euclid.png]] [[[SCP-077]]] — Череп гниения
    [[image euclid.png]] [[[SCP-078]]] — Чувство вины
    [[image euclid.png]] [[[SCP-079]]] — Старый ИИ
    [[image euclid.png]] [[[SCP-080]]] — «Бука»
    [[image euclid.png]] [[[SCP-081]]] — Вирус самовозгорания
    [[image euclid.png]] [[[SCP-082]]] — Каннибал Фернанд
    [[image euclid.png]] [[[SCP-083]]] — Заброшенный дом
    [[image euclid.png]] [[[SCP-084]]] — Статичная радиомачта
    [[image safe.png]] [[[SCP-085]]] — Нарисованная Кассандра
    [[image safe.png]] [[[SCP-086]]] — Кабинет доктора [УДАЛЕНО]
    [[image euclid.png]] [[[SCP-087]]] — Лестница
    [[image safe.png]] [[[SCP-088]]] — Король ящериц
    [[image euclid.png]] [[[SCP-089]]] — Тофет
    [[image keter.png]] [[[SCP-090]]] — Кубик Апокорубика
    [[image safe.png]] [[[SCP-091]]] — Коробка с ностальгией
    [[image safe.png]] [[[SCP-092]]] — «Все хиты „5-го Измерения“»
    [[image euclid.png]] [[[SCP-093]]] — Объект из Красного моря
    [[image keter.png]] [[[SCP-094]]] — Миниатюрный горизонт событий
    [[image safe.png]] [[[SCP-095]]] — «Атомные приключения Ронни Рей-Гана»
    [[image euclid.png]] [[[SCP-096]]] — «Скромник»
    [[image euclid.png]] [[[SCP-097]]] — Старая ярмарка
    [[image safe.png]] [[[SCP-098]]] — Крабы-хирурги
    [[image safe.png]] [[[SCP-099]]] — Портрет
    
    ++ 100-199
    [[image euclid.png]] [[[SCP-100]]] — Развеселый развал растамана Родни 
    [[image euclid.png]] [[[SCP-101]]] — Голодная сумка
    [[image euclid.png]] [[[SCP-102]]] — Собственность Маршалл, Картер и Дарк, Лимитед 
    [[image euclid.png]] [[[SCP-103]]] — Не испытывающий голода человек
    [[image euclid.png]] [[[SCP-104]]] — Одинокий шар
    [[image safe.png]] [[[SCP-105]]] — «Айрис»
    [[image keter.png]] [[[SCP-106]]] — Старик
    [[image safe.png]] [[[SCP-107]]] — Черепаший панцирь
    [[image safe.png]] [[[SCP-108]]] — Экстрамерная полость носа
    [[image euclid.png]] [[[SCP-109]]] — Бесконечная фляга
    [[image euclid.png]] [[[SCP-110]]] — Подземный город
    [[image safe.png]] [[[SCP-111]]] — Драко-улитки
    [[image euclid.png]] [[[SCP-112]]] — Переменные горки
    [[image safe.png]] [[[SCP-113]]] — Переключатель пола
    [[image euclid.png]] [[[SCP-114]]] — Причина раздоров
    [[image safe.png]] [[[SCP-115]]] — Миниатюрный самосвал
    [[image euclid.png]] [[[SCP-116]]] — Хрупкий мальчик
    [[image safe.png]] [[[SCP-117]]] — Идеальный мультитул
    [[image euclid.png]] [[[SCP-118]]] — Ядерные микроорганизмы
    [[image euclid.png]] [[[SCP-119]]] — Времеволновая печь
    [[image safe.png]] [[[SCP-120]]] — Бассейн-телепорт
    [[image euclid.png]] [[[SCP-121]]] — Заповедник летающих зданий
    [[image keter.png]] [[[SCP-122]]] — Больше никаких монстров
    [[image euclid.png]] [[[SCP-123]]] — Удерживаемая маленькая чёрная дыра 
    [[image euclid.png]] [[[SCP-124]]] — Плодородная почва
    [[image euclid.png]] [[[SCP-125]]] — Заразное отражение
    [[image euclid.png]] [[[SCP-126]]] — Невидимый друг
    [[image safe.png]] [[[SCP-127]]] — Живое оружие
    [[image euclid.png]] [[[SCP-128]]] — Движущая сила во плоти
    [[image keter.png]] [[[SCP-129]]] — Прогрессирующее грибковое заражение
    [[image euclid.png]] [[[SCP-130]]] — Почтовое отделение
    [[image safe.png]] [[[SCP-131]]] — «Каплеглазики»
    [[image safe.png]] [[[SCP-132]]] — Раздробленная пустыня
    [[image safe.png]] [[[SCP-133]]] — Переводная дыра
    [[image safe.png]] [[[SCP-134]]] — Ребёнок со звёздными глазами
    [[image euclid.png]] [[[SCP-135]]] — Универсальный канцероген
    [[image euclid.png]] [[[SCP-136]]] — Обнажённая кукла
    [[image euclid.png]] [[[SCP-137]]] — Реальная игрушка
    [[image safe.png]] [[[SCP-138]]] — Всё ещё живой человек
    [[image keter.png]] [[[SCP-140]]] — Недописанная летопись
    [[image safe.png]] [[[SCP-141]]] — Судебник
    [[image safe.png]] [[[SCP-142]]] — «Однорукий бандит»
    [[image euclid.png]] [[[SCP-143]]] — Роща клинковых деревьев
    [[image safe.png]] [[[SCP-144]]] — Тибетский канат в небеса
    [[image euclid.png]] [[[SCP-145]]] — Телефон, похищающий людей
    [[image euclid.png]] [[[SCP-146]]] — Бронзовая голова стыда
    [[image euclid.png]] [[[SCP-147]]] — Анахроничный телевизор
    [[image euclid.png]] [[[SCP-148]]] — Сплав «Телекилл»
    [[image keter.png]] [[[SCP-149]]] — Кровяные комары
    [[image keter.png]] [[[SCP-150]]] — Корабль Тесея
    [[image euclid.png]] [[[SCP-151]]] — Картина
    [[image safe.png]] [[[SCP-152]]] — Книга концов света
    [[image euclid.png]] [[[SCP-153]]] — Черви в водостоке
    [[image euclid.png]] [[[SCP-154]]] — Воинственные браслеты
    [[image safe.png]] [[[SCP-155]]] — Бесконечно быстрый компьютер
    [[image euclid.png]] [[[SCP-156]]] — Воскрешающий гранат
    [[image euclid.png]] [[[SCP-157]]] — Хищник-подражатель
    [[image euclid.png]] [[[SCP-158]]] — Экстрактор души
    [[image safe.png]] [[[SCP-159]]] — Идеальный запиратель
    [[image euclid.png]] [[[SCP-160]]] — Хищный БПЛА
    [[image euclid.png]] [[[SCP-161]]] — Вертушка погибели!
    [[image euclid.png]] [[[SCP-162]]] — Колючий ком
    [[image safe.png]] [[[SCP-163]]] — Потерпевший кораблекрушение
    [[image euclid.png]] [[[SCP-164]]] — Кальмарогенная опухоль
    [[image keter.png]] [[[SCP-165]]] — Ползучие плотоядные пески Туле
    [[image euclid.png]] [[[SCP-166]]] — Просто Гея-подросток
    [[image safe.png]] [[[SCP-167]]] — Бесконечный лабиринт
    [[image safe.png]] [[[SCP-168]]] — Разумный калькулятор
    [[image keter.png]] [[[SCP-169]]] — Левиафан
    [[image safe.png]] [[[SCP-170]]] — Тюбик суперклея
    [[image euclid.png]] [[[SCP-171]]] — Пена с коллективным сознанием
    [[image euclid.png]] [[[SCP-172]]] — Заводной человек
    [[image euclid.png]] [[[SCP-173]]] — Скульптура — **Первый объект**
    [[image euclid.png]] [[[SCP-174]]] — Кукла чревовещателя
    [[image safe.png]] [[[SCP-175]]] — Карта сокровищ 
    [[image euclid.png]] [[[SCP-176]]] — Наблюдаемая петля времени
    [[image safe.png]] [[[SCP-177]]] — Шах и мат
    [[image euclid.png]] [[[SCP-178]]] — 3D-очки
    [[image thaumiel.png]] [[[SCP-179]]] — Сестра Солнца
    [[image euclid.png]] [[[SCP-180]]] — Головной убор, крадущий личность
    [[image safe.png]] [[[SCP-181]]] — «Везунчик»
    [[image euclid.png]] [[[SCP-182]]] — «Наездник»
    [[image euclid.png]] [[[SCP-183]]] — «Ткач»
    [[image euclid.png]] [[[SCP-184]]] — Архитектор
    [[image safe.png]] [[[SCP-185]]] — Радиостанция
    [[image euclid.png]] [[[SCP-186]]] — Покончить с войнами
    [[image safe.png]] [[[SCP-187]]] — Двойное видение
    [[image safe.png]] [[[SCP-188]]] — Ремесленник
    [[image safe.png]] [[[SCP-189]]] — Подражающий волосам паразит
    [[image safe.png]] [[[SCP-190]]] — Ящик с игрушками
    [[image safe.png]] [[[SCP-191]]] — Ребёнок-киборг
    [[image safe.png]] [[[SCP-192]]] — Идеальный рентген
    [[image safe.png]] [[[SCP-193]]] — Платочная улитка
    [[image euclid.png]] [[[SCP-195]]] — «Медицинский виски»
    [[image euclid.png]] [[[SCP-196]]] — Временной парадокс
    [[image safe.png]] [[[SCP-197]]] — Теплица
    [[image euclid.png]] [[[SCP-198]]] — Стаканчик Джо
    
    ++ 200-299
    [[image euclid.png]] [[[SCP-200]]] — Куколка
    [[image euclid.png]] [[[SCP-201]]] — Пустой мир
    [[image safe.png]] [[[SCP-202]]] — Человек наоборот 
    [[image euclid.png]] [[[SCP-203]]] — Измученный железный человек
    [[image keter.png]] [[[SCP-204]]] — Защитник
    [[image euclid.png]] [[[SCP-205]]] — Теневые лампы
    [[image euclid.png]] [[[SCP-206]]] — Путешественник
    [[image safe.png]] [[[SCP-207]]] — Бутылки с «Кока-Колой»
    [[image safe.png]] [[[SCP-208]]] — «Бес»
    [[image euclid.png]] [[[SCP-209]]] — Садистский тумблер
    [[image safe.png]] [[[SCP-210]]] — Затопленный дом 
    [[image safe.png]] [[[SCP-211]]] — Дом, оклеенный бумагой
    [[image safe.png]] [[[SCP-212]]] — Улучшитель
    [[image euclid.png]] [[[SCP-213]]] — Дематериализующий паразит 
    [[image euclid.png]] [[[SCP-214]]] — Вирус «Hemotopian»
    [[image safe.png]] [[[SCP-215]]] — Очки параноика
    [[image safe.png]] [[[SCP-216]]] — Сейф
    [[image keter.png]] [[[SCP-217]]] — Вирус часового механизма
    [[image euclid.png]] [[[SCP-218]]] — Клубок миног-паразитов
    [[image safe.png]] [[[SCP-219]]] — Поршневой резонатор
    [[image safe.png]] [[[SCP-220]]] — Два друга
    [[image safe.png]] [[[SCP-221]]] — Принуждающий пинцет
    [[image euclid.png]] [[[SCP-222]]] — Клонирующий гроб
    [[image euclid.png]] [[[SCP-223]]] — Фотоальбом
    [[image euclid.png]] [[[SCP-224]]] — Старинные напольные часы
    [[image euclid.png]] [[[SCP-225]]] — Неостановимый и неподвижный
    [[image safe.png]] [[[SCP-226]]] — Пазл ужаса 
    [[image safe.png]] [[[SCP-227]]] — Завершённый антикитерский механизм
    [[image safe.png]] [[[SCP-228]]] — Инструмент психиатрической диагностики 
    [[image euclid.png]] [[[SCP-229]]] — Кабельный сорняк
    [[image euclid.png]] [[[SCP-230]]] — Самый веселый человек на свете
    [[image keter.png]] [[[SCP-231]]] — Особые требования к персоналу
    [[image safe.png]] [[[SCP-232]]] — Атомный пистолет Джека Протона
    [[image keter.png]] [[[SCP-233]]] — 23-сторонний многогранник
    [[image euclid.png]] [[[SCP-234]]] — Экстрамерная рыба
    [[image safe.png]] [[[SCP-235]]] — Грампластинка
    [[image keter.png]] [[[SCP-236]]] — Крабы-маскировщики
    [[image safe.png]] [[[SCP-237]]] — Сам себе создатель
    [[image keter.png]] [[[SCP-239]]] — Дитя-ведьма
    [[image safe.png]] [[[SCP-240]]] — Воздухоплавательная духовая машина
    [[image safe.png]] [[[SCP-241]]] — Книга о вкусной и здоровой пище
    [[image safe.png]] [[[SCP-242]]] — Бассейн с самоочисткой 
    [[image safe.png]] [[[SCP-243]]] — Оживитель
    [[image euclid.png]] [[[SCP-244]]] — Кувшин с ледяным туманом
    [[image safe.png]] [[[SCP-245]]] — SCP-RPG
    [[image safe.png]] [[[SCP-246]]] — Предрекающий проектор
    [[image euclid.png]] [[[SCP-247]]] — Безобидный котенок
    [[image safe.png]] [[[SCP-248]]] — 110%
    [[image euclid.png]] [[[SCP-249]]] — Случайная дверь
    [[image euclid.png]] [[[SCP-250]]] — Скелет аллозавра
    [[image euclid.png]] [[[SCP-251]]] — Обманчивый снежный шар
    [[image safe.png]] [[[SCP-252]]] — Гигантский кальмар
    [[image euclid.png]] [[[SCP-253]]] — Раковая чума
    [[image safe.png]] [[[SCP-254]]] — Работник месяца
    [[image keter.png]] [[[SCP-255]]] — Одиннадцатеричное расстройство
    [[image euclid.png]] [[[SCP-256]]] — Заточённое в пишущей машинке
    [[image euclid.png]] [[[SCP-257]]] — Коллекция диковинок профессора Уильяма Вудсворта
    [[image safe.png]] [[[SCP-258]]] — Плачущая лягушка
    [[image keter.png]] [[[SCP-259]]] — Спираль Вейсенгласа
    [[image euclid.png]] [[[SCP-260]]] — Камень-преследователь
    [[image safe.png]] [[[SCP-261]]] — Межпространственный торговый автомат
    [[image euclid.png]] [[[SCP-262]]] — Плащ тысячерукого
    [[image safe.png]] [[[SCP-263]]] — «Пан или профан»
    [[image safe.png]] [[[SCP-264]]] — Храм скелета
    [[image euclid.png]] [[[SCP-265]]] — Чёрная «Волга»
    [[image euclid.png]] [[[SCP-266]]] — Блуждающий огонек
    [[image euclid.png]] [[[SCP-267]]] — Опухолеядные
    [[image euclid.png]] [[[SCP-268]]] — Кепка-невидимка
    [[image safe.png]] [[[SCP-269]]] — Очищающий браслет
    [[image euclid.png]] [[[SCP-270]]] — Захолустный телефон
    [[image keter.png]] [[[SCP-271]]] — Диск с надписями
    [[image safe.png]] [[[SCP-272]]] — Старый железный гвоздь
    [[image euclid.png]] [[[SCP-273]]] — Человек-феникс
    [[image keter.png]] [[[SCP-274]]] — Граффити
    [[image safe.png]] [[[SCP-275]]] — Железнокожая
    [[image euclid.png]] [[[SCP-276]]] — Шхуна времени
    [[image euclid.png]] [[[SCP-277]]] — Страна детских рисунков
    [[image safe.png]] [[[SCP-278]]] — Гигантский механопаук
    [[image euclid.png]] [[[SCP-279]]] — Слоняющийся человек
    [[image keter.png]] [[[SCP-280]]] — Глаза в темноте
    [[image safe.png]] [[[SCP-281]]] — Повторный сигнал будильника
    [[image safe.png]] [[[SCP-282]]] — Ритуальные палочки для жонглирования
    [[image safe.png]] [[[SCP-283]]] — Камень, падающий вбок
    [[image safe.png]] [[[SCP-284]]] — Близнецы
    [[image euclid.png]] [[[SCP-285]]] — Халтура
    [[image euclid.png]] [[[SCP-286]]] — Игра Братьев
    [[image safe.png]] [[[SCP-287]]] — Третий любимый меч Кларка
    [[image safe.png]] [[[SCP-288]]] — «Степфордские» обручальные кольца
    [[image safe.png]] [[[SCP-289]]] — Усилитель инерции
    [[image safe.png]] [[[SCP-290]]] — Пикассопарат
    [[image safe.png]] [[[SCP-291]]] — Разбиратель/Собиратель
    [[image euclid.png]] [[[SCP-292]]] — Песочные часы дежавю
    [[image keter.png]] [[[SCP-293]]] — Наваждение
    [[image euclid.png]] [[[SCP-294]]] — Кофейный автомат
    [[image euclid.png]] [[[SCP-295]]] — Огнегусеницы
    [[image safe.png]] [[[SCP-296]]] — Милитаризированная Зона Содержания 03 
    [[image safe.png]] [[[SCP-297]]] — «Стальной Дэн»
    [[image safe.png]] [[[SCP-298]]] — Кровавый Орган
    [[image keter.png]] [[[SCP-299]]] — Заразное дерево
    
    ++ 300-399
    [[image safe.png]] [[[SCP-300]]] — «Мир в бутылке»
    [[image euclid.png]] [[[SCP-301]]] — Телепортатор
    [[image safe.png]] [[[SCP-302]]] — Муравьиная скульптура
    [[image euclid.png]] [[[SCP-303]]] — Человек за дверью
    [[image safe.png]] [[[SCP-304]]] — Сигнал
    [[image euclid.png]] [[[SCP-305]]] — Шепчущий
    [[image keter.png]] [[[SCP-306]]] — Лягушки
    [[image keter.png]] [[[SCP-307]]] — Плотоядный плющ
    [[image safe.png]] [[[SCP-308]]] — Погребальный саркофаг ацтеков
    [[image euclid.png]] [[[SCP-309]]] — Мягкая игрушка
    [[image safe.png]] [[[SCP-310]]] — Вечное пламя
    [[image safe.png]] [[[SCP-311]]] — Перчатки-щупопередатчики
    [[image euclid.png]] [[[SCP-312]]] — Атмосферная медуза
    [[image safe.png]] [[[SCP-313]]] — Очень мощная сушилка для рук
    [[image euclid.png]] [[[SCP-314]]] — Клинок — детектор движения
    [[image safe.png]] [[[SCP-315]]] — Человек в записи
    [[image safe.png]] [[[SCP-316]]] — Лампа, высасывающая цвет
    [[image safe.png]] [[[SCP-317]]] — Учёная из мелового периода
    [[image safe.png]] [[[SCP-318 |SCP-318]]] — Машина, печатающая души
    [[image keter.png]] [[[SCP-319]]] — Диковинное устройство
    [[image euclid.png]] [[[SCP-320]]] — Ускоритель поля Хиггса
    [[image safe.png]] [[[SCP-321]]] — Дитя человеческое
    [[image safe.png]] [[[SCP-322]]] — Набор «Создай свой замок»
    [[image euclid.png]] [[[SCP-323]]] — Череп Вендиго
    [[image safe.png]] [[[SCP-324]]] — Поминальный куст
    [[image safe.png]] [[[SCP-325]]] — Моющее средство
    [[image euclid.png]] [[[SCP-326]]] — Китайская крестьянка 
    [[image euclid.png]] [[[SCP-327]]] — Сирена
    [[image safe.png]] [[[SCP-328]]] — Чуждый диск
    [[image euclid.png]] [[[SCP-329]]] — Раковый сад
    [[image safe.png]] [[[SCP-330]]] — «Не берите больше двух»
    [[image safe.png]] [[[SCP-331]]] — «Тамблс»
    [[image euclid.png]] [[[SCP-332]]] — Оркестр школы Кирк Лонвуд 1976 года
    [[image euclid.png]] [[[SCP-333]]] — Город в симфонии
    [[image euclid.png]] [[[SCP-334]]] — Звёздный лис
    [[image safe.png]] [[[SCP-335]]] — 150 3.5'' дискет
    [[image euclid.png]] [[[SCP-336]]] — «Лилит»
    [[image euclid.png]] [[[SCP-337]]] — Копна волос 
    [[image safe.png]] [[[SCP-338]]] — Портативное радио
    [[image keter.png]] [[[SCP-339]]] — Молчи, замри
    [[image safe.png]] [[[SCP-340]]]  — Вирусная дыхательная мембрана
    [[image safe.png]] [[[SCP-341]]] — Коллекция моделей внесолнечных систем
    [[image euclid.png]] [[[SCP-342]]] — Билет в один конец
    [[image safe.png]] [[[SCP-343]]] — «Бог»
    [[image safe.png]] [[[SCP-344]]] — Консервный нож Шрёдингера
    [[image safe.png]] [[[SCP-345]]] — Каменный кубик Рубика
    [[image safe.png]] [[[SCP-346]]] — «Птерри»
    [[image euclid.png]] [[[SCP-347]]] — Невидимая женщина
    [[image safe.png]] [[[SCP-348]]] — Папин подарок 
    [[image safe.png]] [[[SCP-349]]] — Философский камень и кладбище бессмертных
    [[image safe.png]] [[[SCP-350]]] — Нерушимый договор
    [[image euclid.png]] [[[SCP-351]]] — Постоянное запоминающее устройство
    [[image keter.png]] [[[SCP-352]]] — «Баба-Яга»
    [[image keter.png]] [[[SCP-353]]] — «Вектор»
    [[image keter.png]] [[[SCP-354]]] — Алое Озеро
    [[image euclid.png]] [[[SCP-355]]] — Зубастая лужайка
    [[image na.png]] [[[SCP-356]]] — Самодопрос
    [[image euclid.png]] [[[SCP-357]]] — Голодная глина
    [[image euclid.png]] [[[SCP-358]]] — Пустынный госпиталь
    [[image safe.png]] [[[SCP-360]]] — Вознесение
    [[image safe.png]] [[[SCP-361]]] — Бронзовая печень
    [[image euclid.png]] [[[SCP-362]]] — Отпадная футболка
    [[image keter.png]] [[[SCP-363]]] — Не совсем многоножки
    [[image safe.png]] [[[SCP-364]]] — Точка сброса на Ио
    [[image euclid.png]] [[[SCP-365]]] — Аквапалка 
    [[image euclid.png]] [[[SCP-366]]]  — Личинки-путешественницы
    [[image euclid.png]] [[[SCP-367]]] — Маленькая собачка
    [[image safe.png]] [[[SCP-368]]] — Бумажный журавлик
    [[image euclid.png]] [[[SCP-369]]] — Живые мигрирующие дорожные работы
    [[image keter.png]] [[[SCP-370]]] — Ключ
    [[image euclid.png]] [[[SCP-371]]] — Макровирус
    [[image euclid.png]] [[[SCP-372]]] — Периферийный прыгун
    [[image safe.png]] [[[SCP-373]]] — Призрачная запись
    [[image safe.png]] [[[SCP-374]]] — Вещая гильотина
    [[image safe.png]] [[[SCP-376]]] — Дерево из светофоров 
    [[image safe.png]] [[[SCP-377]]] — Печенье с точными предсказаниями
    [[image thaumiel.png]] [[[SCP-378]]] — Мозговой червь
    [[image safe.png]] [[[SCP-379]]] — Механический феромон
    [[image safe.png]] [[[SCP-380]]] — Биологическое сетевое устройство
    [[image safe.png]] [[[SCP-381]]] — Пиротехническое многоголосье
    [[image euclid.png]] [[[SCP-382]]] — Проклятая детская коляска
    [[image euclid.png]] [[[SCP-383]]] — Периодически полезный грипп
    [[image safe.png]] [[[SCP-384]]] — Позволь ей войти
    [[image safe.png]] [[[SCP-385]]] — Личный Антигравитационный Полевой Генератор 
    [[image euclid.png]] [[[SCP-386]]] — Вечный гриб
    [[image safe.png]] [[[SCP-387]]] — Живой Lego
    [[image euclid.png]] [[[SCP-388]]] — Невероятный фрисби
    [[image safe.png]] [[[SCP-389]]] — Послание в бутылке
    [[image safe.png]] [[[SCP-390]]] — Древний боевой лазер
    [[image safe.png]] [[[SCP-391]]] — Сова по прозвищу Мидас
    [[image safe.png]] [[[SCP-392]]] — Растение, которое раньше росло только в домах у знати, а теперь — только в Зоне 103
    [[image euclid.png]] [[[SCP-393]]] — Планировщик воспоминаний
    [[image safe.png]] [[[SCP-394]]] — Ушные свечи
    [[image euclid.png]] [[[SCP-395]]] — Искусственник
    [[image keter.png]] [[[SCP-396]]] — Внезапный стул
    [[image safe.png]] [[[SCP-397]]] — Диктатор приматов
    [[image euclid.png]] [[[SCP-398]]] — Встречающий холл
    [[image safe.png]] [[[SCP-399]]] — Кольцо атомных манипуляций 
    
    ++ 400-499
    [[image euclid.png]] [[[SCP-400]]] — Милые детишки 
    [[image euclid.png]] [[[SCP-401]]] — Ладонное дерево
    [[image euclid.png]] [[[SCP-402]]] — Обсидиановый поглотитель
    [[image safe.png]] [[[SCP-403]]] — Взрывная зажигалка 
    [[image safe.png]] [[[SCP-404]]] — Потерянные воспоминания, найденные воспоминания
    [[image euclid.png]] [[[SCP-405]]] — Вирус телепатии
    [[image euclid.png]] [[[SCP-406]]] — Тоннель лунатиков
    [[image na.png]] [[[SCP-407]]] — Песнь Бытия
    [[image safe.png]] [[[SCP-408]]] — Иллюзорные бабочки
    [[image keter.png]] [[[SCP-409]]] — Инфекционный кристалл
    [[image safe.png]] [[[SCP-410]]] — Жуки-редакторы
    [[image thaumiel.png]] [[[SCP-411]]] — Старик-контрамот
    [[image safe.png]] [[[SCP-412]]] — Мутагенное зеркальце
    [[image safe.png]] [[[SCP-413]]] — Бесконечный гараж
    [[image keter.png]] [[[SCP-414]]] — Лекарство горше болезни
    [[image safe.png]] [[[SCP-415]]] — Невольный донор
    [[image euclid.png]] [[[SCP-416]]] — Бесконечный лес
    [[image euclid.png]] [[[SCP-417]]] — Чумное дерево
    [[image safe.png]] [[[SCP-418]]] — Человек-пазл 
    [[image safe.png]] [[[SCP-419]]] — Окно в Другой Мир
    [[image safe.png]] [[[SCP-420]]] — Агрессивное кожное заболевание
    [[image euclid.png]] [[[SCP-421]]] — Стая обломков
    [[image safe.png]] [[[SCP-422]]] — Лоскутное чудовище
    [[image safe.png]] [[[SCP-423]]] — Персонаж-просебятина
    [[image safe.png]] [[[SCP-424]]] — Наноподражатели
    [[image euclid.png]] [[[SCP-425]]] — Передача бесконечности
    [[image euclid.png]] [[[SCP-426]]] — Я тостер
    [[image safe.png]] [[[SCP-427]]] — Лавкрафтовский амулет
    [[image euclid.png]] [[[SCP-428]]] — Толпа 
    [[image safe.png]] [[[SCP-429]]] — Заводной телепортатор
    [[image euclid.png]] [[[SCP-430]]] — Крестьянская казнь
    [[image euclid.png]] [[[SCP-431]]] — Д-р Гидеон
    [[image safe.png]] [[[SCP-432]]] — Лабиринт в шкафчике
    [[image euclid.png]] [[[SCP-433]]] — Ритуал
    [[image euclid.png]] [[[SCP-434]]] — Встреча с самим собой 
    [[image keter.png]] [[[SCP-435]]] — Творец Тьмы
    [[image euclid.png]] [[[SCP-436]]] — Медальон ошибок 
    [[image euclid.png]] [[[SCP-437]]] — Лето 1991 года
    [[image euclid.png]] [[[SCP-438]]] — Шпионская смирительная рубашка
    [[image euclid.png]] [[[SCP-439]]] — Костяной улей
    [[image euclid.png]] [[[SCP-440]]] — Песчаная экосистема 
    [[image euclid.png]] [[[SCP-441]]] — Баран Иакова
    [[image euclid.png]] [[[SCP-442]]] — Всегда вовремя
    [[image safe.png]] [[[SCP-443]]] — Мыслепотоковые мелки 
    [[image euclid.png]] [[[SCP-444]]] — Язык всемирной гармонии
    [[image safe.png]] [[[SCP-445]]] — «Супер-бумага Доктора Развлечудова»
    [[image safe.png]] [[[SCP-446]]] — Манекенщица
    [[image safe.png]] [[[SCP-447]]] — Шарик из зеленой слизи
    [[image safe.png]] [[[SCP-448]]] — Чёртик из табакерки
    [[image euclid.png]] [[[SCP-449]]] — Кишечный порошок
    [[image euclid.png]] [[[SCP-450]]] — Заброшенная федеральная тюрьма 
    [[image euclid.png]] [[[SCP-451]]] — Господин Одиночка
    [[image euclid.png]] [[[SCP-452]]] — Пауки, крадущие сны
    [[image euclid.png]] [[[SCP-453]]] — Ночной клуб по сценарию
    [[image safe.png]] [[[SCP-454]]] — Книга комиксов
    [[image euclid.png]] [[[SCP-455]]] — Грузовое судно
    [[image safe.png]] [[[SCP-456]]] — Усыпляющие клопы
    [[image euclid.png]] [[[SCP-457]]] — Горящий человек
    [[image safe.png]] [[[SCP-458]]] — Бесконечная коробка пиццы
    [[image safe.png]] [[[SCP-459]]] — Межпланетный терморегулятор
    [[image euclid.png]] [[[SCP-460]]] — Спиритуальный шторм
    [[image safe.png]] [[[SCP-461]]] — Телевизор наблюдения
    [[image euclid.png]] [[[SCP-462]]] — Авто для побега
    [[image safe.png]] [[[SCP-463]]] — Ложка, сгибающая людей
    [[image euclid.png]] [[[SCP-464]]] — Завод
    [[image safe.png]] [[[SCP-465]]] — Вечеринка в коробке
    [[image euclid.png]] [[[SCP-466]]] — Подвижные вены
    [[image euclid.png]] [[[SCP-467]]] — Телефонная будка откровений
    [[image euclid.png]] [[[SCP-468]]] — Счёты
    [[image keter.png]] [[[SCP-469]]] — Многокрылый ангел
    [[image euclid.png]] [[[SCP-470]]] — Средоточие всего заброшенного
    [[image euclid.png]] [[[SCP-471]]] — Спутник
    [[image euclid.png]] [[[SCP-472]]] — Кровавый камень
    [[image euclid.png]] [[[SCP-473]]] — Супай
    [[image safe.png]] [[[SCP-475]]] — Мыльный Папа
    [[image safe.png]] [[[SCP-476]]] — Карта, ведущая в никуда
    [[image euclid.png]] [[[SCP-477]]]  — Морские окаменелости
    [[image euclid.png]] [[[SCP-478]]] — Зубные феи
    [[image euclid.png]] [[[SCP-479]]] — Коридор №4, общежитие сотрудников класса D в Зоне 14
    [[image euclid.png]] [[[SCP-480]]] — Поле бесконечных кошмаров
    [[image euclid.png]] [[[SCP-481]]] — Шрамы
    [[image euclid.png]] [[[SCP-482]]] — Рубашка ментальных мутаций
    [[image safe.png]] [[[SCP-483]]] — Анти-возрастное плацебо
    [[image safe.png]] [[[SCP-484]]] — Наркотик, похищающий воспоминания
    [[image safe.png]] [[[SCP-485]]] — Ручка смерти
    [[image safe.png]] [[[SCP-486]]] — Кожа Коатликуэ
    [[image euclid.png]] [[[SCP-487]]] — Невозможный дом
    [[image euclid.png]] [[[SCP-488]]] — Притягивающий метеориты
    [[image euclid.png]] [[[SCP-489]]] — 1-555-МУХО-БОЙ
    [[image safe.png]] [[[SCP-490]]] — Фургончик с мороженым
    [[image euclid.png]] [[[SCP-491]]] — Гибельный свет
    [[image safe.png]] [[[SCP-492]]] — Ожившая тряпичная кукла
    [[image safe.png]] [[[SCP-493]]] — Репликант
    [[image safe.png]] [[[SCP-494]]] — Перчатки передачи материи
    [[image safe.png]] [[[SCP-495]]] — «Создаватель»
    [[image keter.png]] [[[SCP-496]]] — Затонувшая инфекция
    [[image euclid.png]] [[[SCP-497]]] — Ракушка
    [[image safe.png]] [[[SCP-498]]] — 11-минутная отсрочка
    [[image euclid.png]] [[[SCP-499]]] — Солнечный старик
    
    ++ 500-599
    [[image safe.png]] [[[SCP-500]]] — Панацея
    [[image euclid.png]] [[[SCP-501]]] — Монашеская алчность
    [[image safe.png]] [[[SCP-502]]] — Искусственное сердце
    [[image euclid.png]] [[[SCP-503]]] — Самый везучий человек на свете
    [[image safe.png]] [[[SCP-504]]] — «Помидоры-критики»
    [[image keter.png]] [[[SCP-505]]] — Чернильное пятно
    [[image safe.png]] [[[SCP-506]]] — Быстрорастущие растения
    [[image safe.png]] [[[SCP-507]]] — Не любитель ходить между мирами
    [[image safe.png]] [[[SCP-508]]] — Случайно-точечная стереограмма
    [[image safe.png]] [[[SCP-509]]] — Все люди — свиньи
    [[image keter.png]] [[[SCP-510]]] — Мягкая смерть
    [[image euclid.png]] [[[SCP-511]]] — Подвальный кот
    [[image safe.png]] [[[SCP-512]]] — Антигравитационный зонт
    [[image euclid.png]] [[[SCP-513]]] — Коровий колокольчик
    [[image euclid.png]] [[[SCP-514]]] — Голубиная стая
    [[image keter.png]] [[[SCP-515]]] — Спящий
    [[image safe.png]] [[[SCP-516]]] — Умный танк
    [[image safe.png]] [[[SCP-517]]] — Бабуля знает
    [[image euclid.png]] [[[SCP-518]]] — Изменчивая гробница Эйзы Рутледжа
    [[image safe.png]] [[[SCP-519]]] — Ехидный телефон-автомат
    [[image safe.png]] [[[SCP-520]]] — Рубильник
    [[image safe.png]] [[[SCP-521]]] — Почтовый ящик
    [[image safe.png]] [[[SCP-522]]] — Ковёр-кровосос
    [[image euclid.png]] [[[SCP-523]]] — Самый бесполезный предмет в мире
    [[image safe.png]] [[[SCP-524]]] — Всеядный кролик Вальтер
    [[image euclid.png]] [[[SCP-525]]] — Глазные пауки
    [[image euclid.png]] [[[SCP-526]]] — Врата Вальхаллы
    [[image euclid.png]] [[[SCP-527]]] — Г-н Рыба
    [[image euclid.png]] [[[SCP-528]]] — Вуду-пластилин
    [[image safe.png]] [[[SCP-529]]] — Полукошка Джози
    [[image safe.png]] [[[SCP-530]]] — Переменчивый пес Карл
    [[image safe.png]] [[[SCP-531]]] — Парные сторожевые кошки из латуни
    [[image keter.png]] [[[SCP-532]]] — Морозный микроб
    [[image safe.png]] [[[SCP-533]]] — Змеиное ожерелье
    [[image euclid.png]] [[[SCP-534]]] — Кровь, текущая не там
    [[image euclid.png]] [[[SCP-535]]] — Коммуникационная мензурка
    [[image safe.png]] [[[SCP-536]]] — Устройство испытания законов физики
    [[image safe.png]] [[[SCP-537]]] — Поющий граммофон
    [[image euclid.png]] [[[SCP-538]]] — Пауки-тени
    [[image euclid.png]] [[[SCP-539]]] — Совершенный отвлекатель
    [[image safe.png]] [[[SCP-540]]] — Агробомбы
    [[image na.png]] [[[SCP-541]]] — Живые торакальные органы
    [[image euclid.png]] [[[SCP-542]]] — Герр Хирург
    [[image euclid.png]] [[[SCP-543]]] — Шум
    [[image euclid.png]] [[[SCP-544]]] — Новый голос
    [[image euclid.png]] [[[SCP-545]]] — «Жидкая жизнь» 
    [[image safe.png]] [[[SCP-546]]] — Блокнот
    [[image safe.png]] [[[SCP-547]]] — Картезианская визитная карточка 
    [[image euclid.png]] [[[SCP-548]]] — Ледяной паук
    [[image euclid.png]] [[[SCP-549]]] — Малая Медведица
    [[image euclid.png]] [[[SCP-550]]] — Гуль
    [[image safe.png]] [[[SCP-551]]] — Несобираемый пазл
    [[image safe.png]] [[[SCP-552]]] — Опередивший своё время
    [[image safe.png]] [[[SCP-553]]] — Кристаллические бабочки
    [[image euclid.png]] [[[SCP-554]]] — Идеальное убийство 
    [[image euclid.png]] [[[SCP-555]]] — Трупный магнит 
    [[image euclid.png]] [[[SCP-556]]] — Раскрашенный самолёт
    [[image euclid.png]] [[[SCP-557]]] — Древняя Зона содержания 
    [[image safe.png]] [[[SCP-558]]] — Странные контактные линзы
    [[image euclid.png]] [[[SCP-559]]] — «Время дня рождения!»
    [[image safe.png]] [[[SCP-560]]] — Цифровая амёба
    [[image euclid.png]] [[[SCP-561]]] — Скрытый временной разрыв
    [[image euclid.png]] [[[SCP-562]]] — Нереальная вечеринка
    [[image euclid.png]] [[[SCP-563]]] — Заброшенная китайская ферма
    [[image safe.png]] [[[SCP-564]]] — Незавершённый примитивный киборг
    [[image safe.png]] [[[SCP-565]]] — Голова Эда
    [[image safe.png]] [[[SCP-566]]] — Новое слово каждый день
    [[image euclid.png]] [[[SCP-567]]] — Каземат
    [[image safe.png]] [[[SCP-568]]] — Лента разделения
    [[image euclid.png]] [[[SCP-569]]] — Головы
    [[image keter.png]] [[[SCP-571]]] — Самораспространяющийся заразный узор 
    [[image safe.png]] [[[SCP-572]]] — Катана кажущейся неуязвимости
    [[image euclid.png]] [[[SCP-573]]] — Подчиняющая свирель
    [[image euclid.png]] [[[SCP-574]]]  — Бомжатник
    [[image keter.png]] [[[SCP-575]]] — Хищная тьма
    [[image safe.png]] [[[SCP-576]]] — Приятных снов
    [[image euclid.png]] [[[SCP-577]]]  —  Одиночество в свете луны
    [[image safe.png]] [[[SCP-578]]] — Кровавые опалы
    [[image keter.png]] [[[SCP-579]]] — [ДАННЫЕ УДАЛЕНЫ]
    [[image euclid.png]] [[[SCP-580]]] — Небесная колесница Цинь Ши-Хуанди 
    [[image safe.png]] [[[SCP-581]]] — Душа всадника
    [[image keter.png]] [[[SCP-582]]] — Котомка рассказов
    [[image euclid.png]] [[[SCP-583]]] — Смертельная видеокассета
    [[image euclid.png]] [[[SCP-584]]] — Многопалость
    [[image safe.png]] [[[SCP-585]]] — Точилки
    [[image safe.png]] [[[SCP-586]]] — Неописуемый объектив
    [[image safe.png]] [[[SCP-587]]] — Модельная система
    [[image safe.png]] [[[SCP-588]]] — Прожорливая монета
    [[image keter.png]] [[[SCP-589]]] — Цена одержимости
    [[image safe.png]] [[[SCP-590]]] — Он чувствует твою боль
    [[image euclid.png]] [[[SCP-591]]] — «Pretendo» Доктора Развлечудова
    [[image euclid.png]] [[[SCP-592]]] — Неточная книга по истории
    [[image euclid.png]] [[[SCP-593]]] — Заразная дискалькулия
    [[image euclid.png]] [[[SCP-594]]] — Электроовцы
    [[image euclid.png]] [[[SCP-595]]] — Телепортирующийся эсминец 
    [[image safe.png]] [[[SCP-596]]] — Прóклятая исцеляющая статуя
    [[image euclid.png]] [[[SCP-597]]] — Всеобщая Мать 
    [[image safe.png]] [[[SCP-598]]] — Разумный цвет
    [[image euclid.png]] [[[SCP-599]]] — Неведомый город
    
    ++ 600-699
    [[image safe.png]] [[[SCP-600]]] — «Этот парень»
    [[image euclid.png]] [[[SCP-601]]] — Хор Софокла
    [[image safe.png]] [[[SCP-602]]] — Скульптор из СоХо
    [[image safe.png]] [[[SCP-603]]] — Компьютерная программа, воспроизводящая саму себя
    [[image safe.png]] [[[SCP-604]]] — Пир каннибала: осквернённый обряд
    [[image euclid.png]] [[[SCP-605]]] — Живое грозовое облако
    [[image euclid.png]] [[[SCP-606]]] — «Учитель»
    [[image euclid.png]] [[[SCP-607]]] — Серый кот Дориан
    [[image safe.png]] [[[SCP-608]]] — Фрактальная «мишура»
    [[image keter.png]] [[[SCP-609]]] — Онтологический Бильярдный Шар™ Доктора Развлечудова
    [[image keter.png]] [[[SCP-610]]] — Ненавидящая плоть
    [[image euclid.png]] [[[SCP-611]]] — Зубочистка-паразит
    [[image euclid.png]] [[[SCP-612]]] — Агрессивные провода
    [[image euclid.png]] [[[SCP-613]]] — «Чудо-хлеб!» 
    [[image euclid.png]] [[[SCP-614]]] — IP-адрес 57.32.███.███
    [[image euclid.png]] [[[SCP-615]]] — Колючая капля 
    [[image keter.png]] [[[SCP-616]]] — Самолёт и Врата
    [[image euclid.png]] [[[SCP-617]]] — Каменные питомцы
    [[image safe.png]] [[[SCP-619]]] — Счастливые джинсы
    [[image safe.png]] [[[SCP-620]]] — Время летит
    [[image euclid.png]] [[[SCP-621]]] — Гипнотические тюльпаны
    [[image euclid.png]] [[[SCP-622]]]  — Пустыня в банке 
    [[image euclid.png]] [[[SCP-623]]] — Комната безумия
    [[image safe.png]] [[[SCP-624]]] — Плеер «личной» музыки
    [[image euclid.png]] [[[SCP-625]]] — Ногогрызы
    [[image safe.png]] [[[SCP-626]]] — Скульптура, меняющая зрение
    [[image safe.png]] [[[SCP-627]]] — Вечный круг
    [[image euclid.png]] [[[SCP-628]]] — Поющая роща
    [[image euclid.png]] [[[SCP-630]]] — Чёрный ледник
    [[image keter.png]] [[[SCP-631]]] — Никтофобный ночной хищник
    [[image safe.png]] [[[SCP-632]]] — Навязчивые мысли о пауках в голове
    [[image euclid.png]] [[[SCP-634]]] — Золотая рыбка
    [[image euclid.png]] [[[SCP-635]]] — Средневековая программа-загрузчик
    [[image euclid.png]] [[[SCP-636]]] — Лифт в никуда
    [[image safe.png]] [[[SCP-637]]] — Вирусная кошка
    [[image safe.png]] [[[SCP-639]]] — Искажённый человек
    [[image euclid.png]] [[[SCP-640]]] — Солнечные зайчики
    [[image safe.png]] [[[SCP-641]]] — «Успокоитель»
    [[image euclid.png]] [[[SCP-642]]] — Горячие источники
    [[image euclid.png]] [[[SCP-644]]] — Г-н Горячий
    [[image safe.png]] [[[SCP-645]]] — Уста истины
    [[image euclid.png]] [[[SCP-646]]] — Родильный червь
    [[image euclid.png]] [[[SCP-647]]] — Голодная коробка
    [[image euclid.png]] [[[SCP-648]]] — Лабиринт 
    [[image safe.png]] [[[SCP-649]]] — Спичечный коробок с метелью
    [[image euclid.png]] [[[SCP-650]]] — Поразительная статуя
    [[image euclid.png]] [[[SCP-651]]] — Вирус срастания
    [[image safe.png]] [[[SCP-652]]] — Пес-метеоролог
    [[image safe.png]] [[[SCP-653]]] — Бумеранг
    [[image euclid.png]] [[[SCP-655]]]  — Биологическая дезинформационная кампания
    [[image safe.png]] [[[SCP-656]]] — Телевикторина
    [[image safe.png]] [[[SCP-657]]] — Предсказатель смерти
    [[image euclid.png]] [[[SCP-658]]]  — Робомухи
    [[image keter.png]] [[[SCP-659]]] — Совместный птичий разум
    [[image safe.png]] [[[SCP-660]]] —  Глиняная Матка 
    [[image safe.png]] [[[SCP-661]]] — Слишком хороший продавец 
    [[image safe.png]] [[[SCP-662]]] — Колокольчик дворецкого
    [[image euclid.png]] [[[SCP-663]]] — Живой водяной фильтр
    [[image euclid.png]] [[[SCP-664]]]  — Этаж небытия
    [[image safe.png]] [[[SCP-665]]] — Мусорщик 
    [[image euclid.png]] [[[SCP-666]]] — Спиритическая юрта
    [[image keter.png]] [[[SCP-667]]] — Кудзу с феями
    [[image euclid.png]] [[[SCP-668]]] — Тринадцатидюймовый кухонный нож
    [[image euclid.png]] [[[SCP-669]]] — Наглядное пособие
    [[image safe.png]] [[[SCP-670]]] — Семья Коттонов
    [[image euclid.png]] [[[SCP-671]]] — Муравьи-разбиратели
    [[image euclid.png]] [[[SCP-672]]] — Скалистый коралл
    [[image keter.png]] [[[SCP-673]]] — Ткани
    [[image safe.png]] [[[SCP-674]]] — Закадровый пистолет
    [[image safe.png]] [[[SCP-675]]] — Тени в окне
    [[image euclid.png]] [[[SCP-676]]] — Необычный горячий источник
    [[image safe.png]] [[[SCP-677]]] — Непредсказуемый «кузнечик»
    [[image safe.png]] [[[SCP-678]]] — Собиратель душевных травм
    [[image keter.png]] [[[SCP-679]]] — Глазная гниль
    [[image safe.png]] [[[SCP-680]]] — Заводной череп
    [[image euclid.png]] [[[SCP-681]]] — Враждебный гелий
    [[image keter.png]] [[[SCP-682]]] — Неуязвимая рептилия
    [[image euclid.png]] [[[SCP-683]]] — Холодильник с рисунком
    [[image euclid.png]] [[[SCP-684]]] — Иждивенец
    [[image euclid.png]] [[[SCP-685]]] — Не-бездонная яма
    [[image safe.png]] [[[SCP-686]]] — Заразная лактация
    [[image safe.png]] [[[SCP-687]]] — {{НУАР}}
    [[image euclid.png]] [[[SCP-688]]] — Норные жители
    [[image keter.png]] [[[SCP-689]]] — Призрак во тьме
    [[image euclid.png]] [[[SCP-690]]] — Шуточный пластырь
    [[image euclid.png]] [[[SCP-691]]] — Выход труса
    [[image safe.png]] [[[SCP-692]]] — Оживляющий стиральный порошок 
    [[image euclid.png]] [[[SCP-693]]] — Вязаный топтун
    [[image euclid.png]] [[[SCP-694]]] — У нас есть целая вечность
    [[image safe.png]] [[[SCP-695]]] — Угри-паразиты
    [[image na.png]] [[[SCP-696]]]  — Печатная машинка из бездны
    [[image euclid.png]] [[[SCP-697]]] — Токсичный сад в бочке 
    [[image euclid.png]] [[[SCP-698]]] — Черепашка-неодобряшка
    [[image euclid.png]] [[[SCP-699]]] — Таинственный ящик
    
    ++ 700-799
    [[image safe.png]] [[[SCP-700]]] — Фабрика граффити
    [[image euclid.png]] [[[SCP-701]]] — «Трагедия о повешенном короле»
    [[image euclid.png]] [[[SCP-702]]] — Лавка менялы
    [[image euclid.png]] [[[SCP-703]]] — В шкафу
    [[image euclid.png]] [[[SCP-704]]] — Опасный вираж 
    [[image safe.png]] [[[SCP-705]]] — Воинственный пластилин
    [[image euclid.png]] [[[SCP-706]]] — Идеальная фарфоровая кукла
    [[image safe.png]] [[[SCP-707]]] — Матрёшки
    [[image euclid.png]] [[[SCP-708]]] — Вилочный подъемник
    [[image safe.png]] [[[SCP-709]]] — Лесное Око
    [[image euclid.png]] [[[SCP-710]]] — Исчезновение
    [[image safe.png]] [[[SCP-711]]] — Парадоксальная страховка
    [[image safe.png]] [[[SCP-712]]] — Невозможные цвета
    [[image safe.png]] [[[SCP-713]]] — Компьютер без границ
    [[image safe.png]] [[[SCP-714]]] — Нефартовое кольцо
    [[image safe.png]] [[[SCP-715]]] — Мое лицо, каким я мог быть
    [[image euclid.png]] [[[SCP-716]]] — Поезд
    [[image euclid.png]] [[[SCP-717]]] — Посланник
    [[image keter.png]] [[[SCP-718]]] — Глаз
    [[image safe.png]] [[[SCP-719]]] — Несущий свет
    [[image safe.png]] [[[SCP-721]]] — Игрушки Фабрики
    [[image keter.png]] [[[SCP-722]]] — Йормунганд
    [[image safe.png]] [[[SCP-723]]] — Лестница старения
    [[image safe.png]] [[[SCP-724]]] — Енот-полоскун громогласный
    [[image euclid.png]] [[[SCP-725]]] — Кит-попугай
    [[image euclid.png]] [[[SCP-726]]] — Восстанавливающие личинки
    [[image safe.png]] [[[SCP-727]]] — Кузница Гефеста
    [[image safe.png]] [[[SCP-728]]] — Комната вечности
    [[image safe.png]] [[[SCP-729]]] — Мраморная ванна
    [[image euclid.png]] [[[SCP-730]]] — Децеребрирующая чума
    [[image euclid.png]] [[[SCP-731]]] — Крысиный люк
    [[image keter.png]] [[[SCP-732]]] — Зараза из фанфиков
    [[image safe.png]] [[[SCP-733]]] — Ножницы
    [[image keter.png]] [[[SCP-734]]] — Младенец
    [[image euclid.png]] [[[SCP-735]]] — Оскорбительная коробка
    [[image keter.png]] [[[SCP-736]]] — Аномалия Япета
    [[image safe.png]] [[[SCP-737]]] — Голодный поезд
    [[image keter.png]] [[[SCP-738]]] — Сделка с дьяволом
    [[image euclid.png]] [[[SCP-739]]] — Зеркальная Будка 
    [[image safe.png]] [[[SCP-740]]] — Фотография «Гинденбурга»
    [[image euclid.png]] [[[SCP-741]]] — Загадочная русская подлодка
    [[image keter.png]] [[[SCP-742]]] — Ретровирус
    [[image keter.png]] [[[SCP-743]]] — Шоколадный фонтан
    [[image euclid.png]] [[[SCP-744]]] — Требуется ремонт
    [[image euclid.png]] [[[SCP-745]]] — Фары
    [[image euclid.png]] [[[SCP-747]]] — Дети и куклы
    [[image euclid.png]] [[[SCP-748]]] — Индустриальный крах
    [[image safe.png]] [[[SCP-749]]] — Капли дождя
    [[image safe.png]] [[[SCP-750]]] — Другой взгляд на жизнь
    [[image euclid.png]] [[[SCP-751]]] — Пожиратель органов
    [[image keter.png]] [[[SCP-752]]] — Альтруистическая утопия
    [[image safe.png]] [[[SCP-753]]] — Робот-рисовальщик
    [[image euclid.png]] [[[SCP-754]]] — Нарисованная лоза
    [[image keter.png]] [[[SCP-755]]] — «Опасайся белой птицы»
    [[image euclid.png]] [[[SCP-756]]] — Миниатюрная звездная система
    [[image euclid.png]] [[[SCP-757]]] — Фруктовое дерево
    [[image safe.png]] [[[SCP-758]]] — Корректор по имени Василий
    [[image euclid.png]] [[[SCP-759]]] — Закваска
    [[image safe.png]] [[[SCP-760]]]  — Щёточники
    [[image safe.png]] [[[SCP-761]]] — Слегка опасный батут 
    [[image safe.png]] [[[SCP-762]]] — Вечная Железная дева
    [[image safe.png]] [[[SCP-763]]] — Органокомплекс «Беовульф»
    [[image safe.png]] [[[SCP-764]]] — Непотребное представление 
    [[image safe.png]] [[[SCP-765]]] — Утиный пруд
    [[image safe.png]] [[[SCP-766]]] — Человекоподобная пространственная аномалия 
    [[image euclid.png]] [[[SCP-767]]] — Фотографии с места преступления 
    [[image safe.png]] [[[SCP-768]]] — Дальнобойный будильник
    [[image safe.png]] [[[SCP-769]]] — Древняя энциклопедия
    [[image keter.png]] [[[SCP-770]]] — Ядерная плесень
    [[image keter.png]] [[[SCP-771]]] — Органический ИИ с самовосстановлением 
    [[image euclid.png]] [[[SCP-772]]] — Гигантские осы-паразиты
    [[image safe.png]] [[[SCP-773]]] — Вуду-дартс
    [[image safe.png]] [[[SCP-774]]] — Свистящие кости
    [[image keter.png]] [[[SCP-775]]] — Голодные клещи
    [[image euclid.png]] [[[SCP-776]]] — Культ молодости
    [[image euclid.png]] [[[SCP-777]]] — Песчаное царство
    [[image euclid.png]] [[[SCP-778]]] — Райские водопады
    [[image safe.png]] [[[SCP-779]]] — Домовые осы
    [[image safe.png]] [[[SCP-780]]] — Бусина-семечко
    [[image euclid.png]] [[[SCP-781]]] — Невольный повелитель снов
    [[image safe.png]] [[[SCP-782]]] — Ваше Новое Я
    [[image keter.png]] [[[SCP-783]]] — Жил на свете человек ^^Скрю^^чен,,ные,, ножки
    [[image euclid.png]] [[[SCP-784]]] — Вечное Рождество
    [[image keter.png]] [[[SCP-785]]] — Сеть закусочных
    [[image safe.png]] [[[SCP-786]]] — Двенадцатикратная воронка
    [[image safe.png]] [[[SCP-787]]] — Самолёт, которого не было
    [[image euclid.png]] [[[SCP-788]]] — Магматический карп
    [[image euclid.png]] [[[SCP-789]]] — Охотник на педофилов
    [[image euclid.png]] [[[SCP-790]]] — Кровь?
    [[image safe.png]] [[[SCP-791]]] — Водяной шар
    [[image euclid.png]] [[[SCP-792]]] — Трупоферма
    [[image euclid.png]] [[[SCP-793]]] — Призрачная болезнь 
    [[image euclid.png]] [[[SCP-794]]] — Кораблекрушение в пустыне
    [[image euclid.png]] [[[SCP-795]]] — Кот, изменяющий реальность
    [[image euclid.png]] [[[SCP-796]]] — Речная кошка
    [[image euclid.png]] [[[SCP-797]]] — Любопытный полтергейст
    [[image safe.png]] [[[SCP-798]]] — Мозговая крыса
    [[image euclid.png]] [[[SCP-799]]] — Хищные одеяла
    
    ++ 800-899
    [[image euclid.png]] [[[SCP-800]]] — История Востока
    [[image euclid.png]] [[[SCP-801]]] — Семь шкур
    [[image euclid.png]] [[[SCP-802]]] — Музыкальный танк
    [[image euclid.png]] [[[SCP-803]]] — Хищные зонтики
    [[image keter.png]] [[[SCP-804]]] — Мир без людей
    [[image euclid.png]] [[[SCP-805]]] — Ядовитая деревянная лошадка 
    [[image safe.png]] [[[SCP-806]]] — Воскрешающий проектор
    [[image euclid.png]] [[[SCP-807]]] — Сердечный приступ на блюдечке
    [[image euclid.png]] [[[SCP-808]]] — Механический хор
    [[image safe.png]] [[[SCP-809]]] — Военные ботинки
    [[image euclid.png]] [[[SCP-810]]] — Лампа нежелания
    [[image euclid.png]] [[[SCP-811]]] — Болотница
    [[image euclid.png]] [[[SCP-812]]] — Река в контейнере
    [[image keter.png]] [[[SCP-813]]] — Осколок стекла
    [[image euclid.png]] [[[SCP-814]]] — Чистые тоны
    [[image safe.png]] [[[SCP-815]]] — Банка змеиных орехов
    [[image euclid.png]] [[[SCP-816]]] — Конструктор Дарвина
    [[image euclid.png]] [[[SCP-817]]] — Случайное превращение
    [[image na.png]] [[[SCP-818]]] — Прерванный проект
    [[image safe.png]] [[[SCP-819]]] — Леденцы-вампиры
    [[image euclid.png]] [[[SCP-820]]] — Раскрашенная саранча
    [[image na.png]] [[[SCP-821]]] — Южная ярмарка
    [[image euclid.png]] [[[SCP-822]]] — Кактус-мина
    [[image euclid.png]] [[[SCP-823]]] — Карнавал ужасов
    [[image euclid.png]] [[[SCP-824]]] — Активная борьба с сорняками
    [[image safe.png]] [[[SCP-825]]] — Шлем тревожных видений
    [[image safe.png]] [[[SCP-826]]] — Захватывающее чтение
    [[image safe.png]] [[[SCP-827]]] — Суп
    [[image euclid.png]] [[[SCP-828]]] — ᖃᓪᓗᐱᓪᓗᐃᑦ
    [[image safe.png]] [[[SCP-829]]] — Кровожадный лак для ногтей
    [[image safe.png]] [[[SCP-830]]] — Нефтяные зыбучие пески 
    [[image euclid.png]] [[[SCP-831]]] — Термиты-ремесленники
    [[image safe.png]] [[[SCP-832]]] — Монета счетовода
    [[image euclid.png]] [[[SCP-833]]] — Червь милосердия
    [[image euclid.png]] [[[SCP-834]]] — Маркеры
    [[image keter.png]] [[[SCP-835]]] — Рассекреченные данные
    [[image keter.png]] [[[SCP-836]]] — Строительный рак
    [[image safe.png]] [[[SCP-837]]] — Глина умножения
    [[image safe.png]] [[[SCP-838]]] — Работа во сне
    [[image safe.png]] [[[SCP-839]]] — «Засахаренные червячки»
    [[image euclid.png]] [[[SCP-840]]] — Трубожители
    [[image safe.png]] [[[SCP-841]]] — Горизонтально-Отражённая Зеркальная Вуду-Марионетка
    [[image safe.png]] [[[SCP-842]]] — Операционный стол
    [[image euclid.png]] [[[SCP-843]]] — Коровьи семена
    [[image euclid.png]] [[[SCP-844]]] — Плакса
    [[image euclid.png]] [[[SCP-845]]] — Жидкий хорь 
    [[image safe.png]] [[[SCP-846]]] — Робо-Чувак
    [[image euclid.png]] [[[SCP-847]]] — Манекен
    [[image euclid.png]] [[[SCP-848]]] — Межпространственная паутина
    [[image safe.png]] [[[SCP-849]]] — Идеальный день 
    [[image euclid.png]] [[[SCP-850]]] — Косяк рыб
    [[image euclid.png]] [[[SCP-851]]] — Снотворные насекомые
    [[image safe.png]] [[[SCP-852]]] — Лунная аномалия
    [[image safe.png]] [[[SCP-853]]] — Консервированная погода
    [[image safe.png]] [[[SCP-854]]] — Мост Снов
    [[image euclid.png]] [[[SCP-855]]] — Оживший кинотеатр
    [[image euclid.png]] [[[SCP-856]]] — Речной лев
    [[image safe.png]] [[[SCP-857]]] — Ожившие человеческие органы
    [[image keter.png]] [[[SCP-858]]] — Гравитационная радуга
    [[image euclid.png]] [[[SCP-859]]] — Шар арахнофобии
    [[image safe.png]] [[[SCP-860]]] — Синий ключ
    [[image keter.png]] [[[SCP-861]]] — Снизошедший ангел
    [[image safe.png]] [[[SCP-862]]] — Крысы
    [[image safe.png]] [[[SCP-863]]] — Крабы-конструкторы 
    [[image euclid.png]] [[[SCP-864]]] — Таз-людоед
    [[image safe.png]] [[[SCP-865]]] — Плеть джентльмена
    [[image euclid.png]] [[[SCP-866]]] — Суперкомпьютер
    [[image euclid.png]] [[[SCP-867]]] — Кровавая ель
    [[image euclid.png]] [[[SCP-868]]] — Мнемонический мем
    [[image euclid.png]] [[[SCP-869]]] — Лето 1948 года
    [[image keter.png]] [[[SCP-870]]] — Здесь могут водиться чудовища
    [[image keter.png]] [[[SCP-871]]] — Пироги пекутся сами
    [[image safe.png]] [[[SCP-872]]] — Пугало-фермер
    [[image euclid.png]] [[[SCP-873]]] — Хрустальный шар из России
    [[image euclid.png]] [[[SCP-874]]] — Текучая бездна
    [[image safe.png]] [[[SCP-875]]] — Военные преступники
    [[image safe.png]] [[[SCP-876]]] — Таблетки, заменяющие элементы
    [[image keter.png]] [[[SCP-877]]] — Микрочипы Университета
    [[image euclid.png]] [[[SCP-878]]] — Актёр
    [[image euclid.png]] [[[SCP-879]]] — Колониальное китообразное
    [[image euclid.png]] [[[SCP-880]]] — Вечная зима
    [[image euclid.png]] [[[SCP-881]]] — Маленькие люди
    [[image euclid.png]] [[[SCP-882]]] — Машина
    [[image euclid.png]] [[[SCP-883]]] — Экстрамерный пчелиный улей
    [[image euclid.png]] [[[SCP-884]]] — Зеркальце для бритья
    [[image euclid.png]] [[[SCP-885]]] — Живой вакуум
    [[image safe.png]] [[[SCP-886]]] — Козья матушка
    [[image safe.png]] [[[SCP-887]]] — Гиперграфия
    [[image safe.png]] [[[SCP-888]]] — Камни памяти 
    [[image euclid.png]] [[[SCP-889]]] — Скрещивание
    [[image euclid.png]] [[[SCP-890]]] — Ракетный хирург
    [[image safe.png]] [[[SCP-891]]] — Калифорнийское поле 
    [[image euclid.png]] [[[SCP-892]]] — Таблица на всех
    [[image safe.png]] [[[SCP-893]]] — Размножающийся почкованием
    [[image safe.png]] [[[SCP-894]]] — Ничего не вижу, ничего не слышу, ничего никому не скажу
    [[image euclid.png]] [[[SCP-895]]] — Искажения на видео
    [[image safe.png]] [[[SCP-896]]] — Ролевая онлайн-игра
    [[image safe.png]] [[[SCP-897]]] — Вуду-трансплантация 
    [[image safe.png]] [[[SCP-898]]] — Меметический контрагент
    [[image euclid.png]] [[[SCP-899]]] — Пропавшие дети
    
    ++ 900-999
    [[image euclid.png]] [[[SCP-900]]] — Город Солнца
    [[image euclid.png]] [[[SCP-901]]] — Здание на площади
    [[image keter.png]] [[[902-warning|SCP-902]]] — Финальный отсчёт
    [[image euclid.png]] [[[SCP-903]]] — Тоннель бесконечности вариантов
    [[image euclid.png]] [[[SCP-904]]] — Короткий стих
    [[image safe.png]] [[[SCP-905]]] — Г-н Хамелеон
    [[image euclid.png]] [[[SCP-906]]] — Едкая стая
    [[image safe.png]] [[[SCP-907]]] — Исследовательский фургон
    [[image safe.png]] [[[SCP-908]]] — Остров во многих местах
    [[image euclid.png]] [[[SCP-909]]] — Г-н Забывчивый
    [[image euclid.png]] [[[SCP-911]]] — Египетская Книга мертвых
    [[image safe.png]] [[[SCP-912]]] — Автономная броня SWAT
    [[image euclid.png]] [[[SCP-913]]] — Г-н Голодный
    [[image safe.png]] [[[SCP-914]]] — Часовой механизм
    [[image euclid.png]] [[[SCP-915]]] — Механоэкстрамерный компьютер
    [[image safe.png]] [[[SCP-916]]] — Лучший друг человека
    [[image safe.png]] [[[SCP-917]]] — Г-н Луна
    [[image euclid.png]] [[[SCP-918]]] — Мельница детей
    [[image safe.png]] [[[SCP-919]]] — Нуждающееся зеркало
    [[image euclid.png]] [[[SCP-920]]] — Г-н Потерянный
    [[image euclid.png]] [[[SCP-921]]] — Музей воспоминаний
    [[image euclid.png]] [[[SCP-922]]] — Другая версия истины
    [[image safe.png]] [[[SCP-923]]] — Полезный инструмент  
    [[image euclid.png]] [[[SCP-924]]] — Ледяной Водяной
    [[image euclid.png]] [[[SCP-925]]] — Грибной культ
    [[image safe.png]] [[[SCP-926]]] — Гуцинь
    [[image euclid.png]] [[[SCP-927]]] — Заразный дом
    [[image euclid.png]] [[[SCP-928]]]  — Белый король
    [[image euclid.png]] [[[SCP-929]]] — Кукушонок
    [[image euclid.png]] [[[SCP-930]]] — Остров чаек
    [[image safe.png]] [[[SCP-931]]] — Чаша для риса
    [[image euclid.png]] [[[SCP-932]]] — Пожиратели страха
    [[image euclid.png]] [[[SCP-933]]] — Клейкая лента
    [[image euclid.png]] [[[SCP-934]]] — Материковый маяк
    [[image euclid.png]] [[[SCP-935]]] — Древние игральные карты
    [[image euclid.png]] [[[SCP-936]]] — Плоды человеческие
    [[image safe.png]] [[[SCP-937]]] — Палочники
    [[image keter.png]] [[[SCP-938]]] — Кровь и молния
    [[image keter.png]] [[[SCP-939]]] — Со множеством голосов
    [[image keter.png]] [[[SCP-940]]] — Пауки-кукловоды
    [[image safe.png]] [[[SCP-942]]] — Кровавые конфеты
    [[image safe.png]] [[[SCP-943]]]  — Воздаяние по заслугам
    [[image euclid.png]] [[[SCP-944]]] — Зеркальный лабиринт
    [[image euclid.png]] [[[SCP-945]]] — «Ушебти»
    [[image euclid.png]] [[[SCP-946]]] — Конструктивная дискуссия
    [[image keter.png]] [[[SCP-947]]] — [РУГАТЕЛЬСТВО УДАЛЕНО] сын
    [[image safe.png]] [[[SCP-949]]] — «Страна Развлечудова»
    [[image safe.png]] [[[SCP-950]]] — Стиральная машина
    [[image safe.png]] [[[SCP-951]]] — Мой друг ЛУКАС
    [[image keter.png]] [[[SCP-953]]] — Полиморфный гуманоид
    [[image euclid.png]] [[[SCP-954]]] — Поющие лягушки
    [[image safe.png]] [[[SCP-955]]] — Господин Букашкин
    [[image euclid.png]] [[[SCP-956]]] — Пиньята наоборот
    [[image keter.png]] [[[SCP-957]]] — Наживка
    [[image safe.png]] [[[SCP-958]]] — Генерал-Бип
    [[image safe.png]] [[[SCP-959]]] — Страшила
    [[image safe.png]] [[[SCP-960]]] — Вдохновение
    [[image euclid.png]] [[[SCP-961]]] — Солнечные часы Университета
    [[image euclid.png]] [[[SCP-962]]] — Многословный столп
    [[image euclid.png]] [[[SCP-963]]] — Бессмертие
    [[image euclid.png]] [[[SCP-964]]] — Неописуемый полиморф
    [[image euclid.png]] [[[SCP-965]]] — Лицо в окне
    [[image euclid.png]] [[[SCP-966]]] — Бессонники
    [[image euclid.png]] [[[SCP-967]]] — Бесконечная свалка
    [[image keter.png]] [[[SCP-968]]] — Смоляное чучелко
    [[image euclid.png]] [[[SCP-969]]] — Репеллент марки «█████»
    [[image euclid.png]] [[[SCP-970]]] — Рекурсивная комната
    [[image safe.png]] [[[SCP-971]]] — Экзотический фаст-фуд
    [[image euclid.png]] [[[SCP-973]]] — Призрак полицейского
    [[image euclid.png]] [[[SCP-974]]] — Хищник-шалашник
    [[image euclid.png]] [[[SCP-975]]] — Метрожабы
    [[image safe.png]] [[[SCP-976]]] — Аномальный жесткий диск
    [[image euclid.png]] [[[SCP-977]]] — Пункт наблюдения 
    [[image safe.png]] [[[SCP-978]]] — Фотоаппарат желаний
    [[image euclid.png]] [[[SCP-979]]] — Керамический кролик
    [[image safe.png]] [[[SCP-980]]] — Никаких тонкостей
    [[image safe.png]] [[[SCP-981]]] — Режиссёрская версия
    [[image safe.png]] [[[SCP-982]]] — Чикагская петля
    [[image safe.png]] [[[SCP-983]]] — Именинная обезьянка
    [[image safe.png]] [[[SCP-984]]] — Общественный туалет
    [[image euclid.png]] [[[SCP-985]]] — Невостребованный багаж
    [[image safe.png]] [[[SCP-986]]]  — Последняя рукопись Фолкнера
    [[image euclid.png]] [[[SCP-987]]] — Галерея ужасов
    [[image safe.png]] [[[SCP-988]]] — Неоткрываемый сундук
    [[image safe.png]] [[[SCP-989]]] — Сахар для самозащиты
    [[image keter.png]] [[[SCP-990]]] — Человек из снов
    [[image safe.png]] [[[SCP-991]]] — Шприц
    [[image safe.png]] [[[SCP-992]]] — Тайный посланник Геи
    [[image safe.png]] [[[SCP-993]]] — Клоун Помпон 
    [[image euclid.png]] [[[SCP-994]]] — Некие серебряные блюдца
    [[image euclid.png]] [[[SCP-995]]] — Монстры под кроватью
    [[image euclid.png]] [[[SCP-996]]] — Неправильная топология
    [[image safe.png]] [[[SCP-997]]] — Подавитель вредителей 
    [[image euclid.png]] [[[SCP-998]]] — Пропавший самолёт
    [[image safe.png]] [[[SCP-999]]] — Щекоточный монстр
    ------
    [[[log-of-anomalous-items|Список аномальных предметов]]] ([[[log-of-anomalous-items-vol-ii|часть 2]]]) — список предметов, которые нельзя назвать полноценными SCP-объектами несмотря на наличие аномальных свойств.
    [[[log-of-extranormal-events|Список аномальных явлений]]] — список необычных явлений, зачастую произошедших единожды и слишком быстро, чтобы Организация могла оперативно среагировать.
    [[[log-of-unexplained-locations|Список необъяснённых локаций]]] — список обнаруженных Фондом необычных зон, которые всё же не требуют установки специфических ОУС.
    
    "#;

    use crate::data::NullPageCallbacks;

    // TODO includer
    let settings = WikitextSettings::from_mode(WikitextMode::Page);

    let page_info = page_info_dummy();

    let page_callbacks = Rc::new(NullPageCallbacks{}).clone();

    let text = &mut String::from(main_code);

    preprocess(text);
    let tokens = tokenize(text);
    let (tree, _warnings) = parse(&tokens, &page_info, page_callbacks.clone(), &settings).into();
    let output = &HtmlRender.render(&tree, &page_info, page_callbacks.clone(), &settings);

    println!("result: {}", output.body);
}