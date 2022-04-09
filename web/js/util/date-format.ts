import { sprintf } from 'sprintf-js';


export default function formatDate(date: Date, seconds: boolean = false) {
    const localizedMonthNames = ['Янв', 'Фев', 'Мар', 'Апр', 'Мая', 'Июн', 'Июл', 'Авг', 'Сен', 'Окт', 'Ноя', 'Дек']
    let formatted = sprintf('%02d %s %04d %02d:%02d',
        date.getDate(), localizedMonthNames[date.getMonth()], date.getFullYear(),
        date.getHours(), date.getMinutes());
    if (seconds) {
        formatted += sprintf(':%02d', date.getSeconds())
    }
    return formatted
}
