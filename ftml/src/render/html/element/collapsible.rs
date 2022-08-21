/*
 * render/html/element/collapsible.rs
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
use crate::tree::{AttributeMap, Element};

#[derive(Debug, Copy, Clone)]
pub struct Collapsible<'a> {
    elements: &'a [Element<'a>],
    attributes: &'a AttributeMap<'a>,
    start_open: bool,
    show_text: Option<&'a str>,
    hide_text: Option<&'a str>,
    show_top: bool,
    show_bottom: bool,
}

impl<'a> Collapsible<'a> {
    #[inline]
    pub fn new(
        elements: &'a [Element<'a>],
        attributes: &'a AttributeMap<'a>,
        start_open: bool,
        show_text: Option<&'a str>,
        hide_text: Option<&'a str>,
        show_top: bool,
        show_bottom: bool,
    ) -> Self {
        Collapsible {
            elements,
            attributes,
            start_open,
            show_text,
            hide_text,
            show_top,
            show_bottom,
        }
    }
}

pub fn render_collapsible(ctx: &mut HtmlContext, collapsible: Collapsible) {
    let Collapsible {
        elements,
        attributes: _attributes,
        start_open,
        show_text,
        hide_text,
        show_top,
        show_bottom,
    } = collapsible;

    info!(
        "Rendering collapsible (elements length {}, start-open {}, show-text {}, hide-text {}, show-top {}, show-bottom {})",
        elements.len(),
        start_open,
        show_text.unwrap_or("<default>"),
        hide_text.unwrap_or("<default>"),
        show_top,
        show_bottom,
    );

    let show_text = match show_text {
        Some(s) => String::from(s),
        _ => ctx.handle().get_message("collapsible-open")
    };

    let hide_text = match hide_text {
        Some(s) => String::from(s),
        _ => ctx.handle().get_message("collapsible-hide")
    };

    ctx.html()
        .div()
        .attr(attr!("class" => "w-collapsible collapsible-block"))
        .contents(|ctx| {
            ctx.html()
                .div()
                .attr(attr!("class" => "collapsible-block-folded", "style" => if start_open { "display: none" } else { "display: block" }))
                .contents(|ctx| {
                    ctx.html()
                        .a()
                        .attr(attr!("class" => "collapsible-block-link", "href" => "javascript:;"))
                        .inner(show_text.as_str());
                });

            ctx.html()
                .div()
                .attr(attr!("class" => "collapsible-block-unfolded", "style" => if start_open { "display: block" } else { "display: none" }))
                .contents(|ctx| {
                    let build_unfolded_link = |ctx: &mut HtmlContext| {
                        ctx.html()
                            .div()
                            .attr(attr!("class" => "collapsible-block-unfolded-link"))
                            .contents(|ctx| {
                                ctx.html()
                                    .a()
                                    .attr(attr!("class" => "collapsible-block-link", "href" => "javascript:;"))
                                    .inner(hide_text.as_str());
                            });
                    };

                    if show_top || !show_bottom {
                        build_unfolded_link(ctx);
                    }

                    ctx.html()
                        .div()
                        .attr(attr!("class" => "collapsible-block-content"))
                        .inner(elements);

                    if show_bottom {
                        build_unfolded_link(ctx);
                    }
                });
        });
}
