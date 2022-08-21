/*
 * render/html/element/footnotes.rs
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

pub fn render_footnote(ctx: &mut HtmlContext) {
    info!("Rendering footnote reference");

    let index = ctx.next_footnote_index();

    ctx.html()
        .sup()
        .attr(attr!("class" => "footnoteref"))
        .contents(|ctx| {
            ctx.html()
                .a()
                .attr(attr!(
                    "id" => format!("footnoteref-{}", index).as_str(),
                    "class" => "footnoteref w-footnoteref",
                    "href" => format!("#footnote-{}", index).as_str(),
                ))
                .inner(index.to_string());
        });
}

pub fn render_footnote_block(ctx: &mut HtmlContext, title: Option<&str>) {
    info!(
        "Rendering footnote block (title {})",
        title.unwrap_or("<default>"),
    );

    let title = match title {
        Some(title) => String::from(title),
        None => {
            ctx
                .handle()
                .get_message("footnote-block-title")
        }
    };

    ctx.html()
        .div()
        .attr(attr!("class" => "footnotes-footer"))
        .contents(|ctx| {
            ctx.html()
                .div()
                .attr(attr!("class" => "title"))
                .inner(&title);
            for (index, contents) in ctx.footnotes().iter().enumerate() {
                let index = index + 1;
                ctx.html()
                    .div()
                    .attr(attr!("id" => &format!("footnote-{}", index), "class" => "footnote-footer"))
                    .contents(|ctx| {
                        ctx.html()
                            .a()
                            .attr(attr!("href" => &format!("#footnoteref-{}", index)))
                            .inner(index.to_string());
                        str_write!(ctx, ". ");
                        render_elements(ctx, contents);
                    });
            }
        });
}
