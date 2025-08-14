/*
 * render/html/element/text.rs
 *
 * ftml - Library to parse Wikidot text
 * Copyright (C) 2019-2022 Wikijump Team
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU Affero General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
 * GNU Affero General Public License for more details.
 *
 * You should have received a copy of the GNU Affero General Public License
 * along with this program. If not, see <http://www.gnu.org/licenses/>.
 */

use super::prelude::*;

pub fn render_wikitext_raw(ctx: &mut HtmlContext, text: &str) {
    info!("Escaping raw string '{text}'");

    ctx.html()
        .span()
        .attr(attr!(
            "class" => "wj-raw",
            "style" => "white-space: pre-wrap;"
        ))
        .inner(text);
}

pub fn render_html_entity(ctx: &mut HtmlContext, entity: &str) {
    info!("Rendering HTML entity '{entity}'");

    str_write!(ctx.buffer(), "{entity}");
    if !entity.ends_with(';') {
        str_write!(ctx.buffer(), ";");
    }
}

pub fn render_email(ctx: &mut HtmlContext, email: &str) {
    info!("Rendering email address '{email}'");

    // Since our usecase doesn't typically have emails as real,
    // but rather as fictional elements, we're just rendering as text.

    ctx.html()
        .span()
        .attr(attr!("class" => "wj-email"))
        .inner(email);
}

pub fn render_code(ctx: &mut HtmlContext, language: Option<&str>, contents: &str) {
    info!(
        "Rendering code block (language {})",
        language.unwrap_or("<none>"),
    );

    let class = {
        let mut class = format!("code w-code language-{}", language.unwrap_or("none"));
        class.make_ascii_lowercase();
        class
    };

    ctx.html()
        .div()
        .attr(attr!("class" => &class))
        .contents(|ctx| {
            ctx.html()
                .div()
                .attr(attr!("class" => "hl-main"))
                .contents(|ctx| {
                    ctx.html()
                        .pre()
                        .inner(contents);
                });
        });
}
