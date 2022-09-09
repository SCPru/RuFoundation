function padString(paddingValue, str) {
    return String(paddingValue + str).slice(-paddingValue.length);
}

export default function formatDate(date: Date, format: string = '%H:%M %d.%m.%Y') {
    const localizedMonthNames = ['Янв', 'Фев', 'Мар', 'Апр', 'Мая', 'Июн', 'Июл', 'Авг', 'Сен', 'Окт', 'Ноя', 'Дек'];
    const localizedDayNames = ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс'];

    if (!format) format = window.localStorage.dateFormat;
    var months = localizedMonthNames;
    var days = localizedDayNames;
    if (!months || !days || !format)
    {
        return padString('00', date.getDate())
            + '.' + padString('00', date.getMonth()+1)
            + '.' + padString('0000', date.getFullYear())
            + ' ' + padString('00', date.getHours())
            + ':' + padString('00', date.getMinutes())
            + ':' + padString('00', date.getSeconds());
    }

    var dayWeekU = (date.getDay()+6)%7;
    var dayWeekW = date.getDay();

    var hour24 = date.getHours();
    var hour12 = date.getHours() % 12;
    var isPM = hour24 > 12; // false = am
    if (!hour12) hour12 = 12;

    // sorry for comments in russian, ported from another project, cba replacing.
    // this is just php's strftime replication. compatible with python too for the most part
    // %a = день недели строкой
    // %d = день месяца с нулями
    // %e = день месяца с пробелом
    // %u = день недели (1 = понедельник)
    // %w = день недели (0 = воскресенье)
    // %b, %h = месяц
    // %m = месяц с нулями
    // %C = век = Math.floor(year / 100)
    // %y = год, 2 символа
    // %Y = год, 4 символа
    // %H = час, 0-23, с нулями
    // %k = час, 0-23, с пробелом
    // %I = час, 1-12, с нулями
    // %l = час, 1-12, с пробелом
    // %M = минута, 0-59, с нулями
    // %p = AM/PM
    // %P = am/pm
    // %r = %I:%M:%S %p
    // %R = %H:%M
    // %S = секунда, 0-59, с нулями
    // %s = timestamp

    var s = format;
    s = s.replace(/%h/g, '%b')
        .replace(/%r/g, '%I:%M:%s %p')
        .replace(/%R/g, '%H:%M')
        .replace(/%a/g, days[dayWeekU])
        .replace(/%d/g, padString('00', date.getDate()))
        .replace(/%e/g, padString('  ', date.getDate()))
        .replace(/%u/g, String(dayWeekU+1))
        .replace(/%w/g, String(dayWeekW))
        .replace(/%b/g, months[date.getMonth()])
        .replace(/%m/g, padString('00', date.getMonth()+1))
        .replace(/%C/g, String(Math.ceil(date.getFullYear()/100)))
        .replace(/%y/g, padString('00', date.getFullYear().toString().substr(2)))
        .replace(/%Y/g, padString('0000', date.getFullYear()))
        .replace(/%H/g, padString('00', date.getHours()))
        .replace(/%k/g, padString('  ', date.getHours()))
        .replace(/%I/g, padString('00', hour12))
        .replace(/%l/g, padString('  ', hour12))
        .replace(/%M/g, padString('00', date.getMinutes()))
        .replace(/%p/g, isPM?'PM':'AM')
        .replace(/%P/g, isPM?'pm':'am')
        .replace(/%S/g, padString('00', date.getSeconds()))
        .replace(/%s/g, String(Math.floor(date.getTime()/1000)));
    return s;
}
