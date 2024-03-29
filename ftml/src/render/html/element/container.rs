/*
 * render/html/element/container.rs
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

use regex::{Regex, RegexBuilder};

use super::prelude::*;
use crate::tree::{Container, ContainerType, HtmlTag};

pub fn render_container(ctx: &mut HtmlContext, container: &Container) {
    info!("Rendering container '{}'", container.ctype().name());

    let has_toc_block = ctx.has_toc_block();

    match container.ctype() {
        // We wrap with <rp> around the <rt> contents
        ContainerType::RubyText => {
            ctx.html().rp().inner("(");

            render_container_internal(ctx, container);

            ctx.html().rp().inner(")");
        }

        ContainerType::Paragraph => {
            match container.elements().first() {
                Some(Element::AlignMarker(alignment)) => {
                    let style = match alignment {
                        crate::tree::Alignment::Left => "text-align: left",
                        crate::tree::Alignment::Right => "text-align: right",
                        crate::tree::Alignment::Center => "text-align: center",
                        crate::tree::Alignment::Justify => "text-align: justify",
                    };
                    ctx.html()
                        .tag("p")
                        .attr(attr!("style" => style))
                        .inner(container.elements());
                }
                _ => render_container_internal(ctx, container),
            }
        }

        ContainerType::Align(alignment) => {
            let style = match alignment {
                crate::tree::Alignment::Left => "text-align: left",
                crate::tree::Alignment::Right => "text-align: right",
                crate::tree::Alignment::Center => "text-align: center",
                crate::tree::Alignment::Justify => "text-align: justify",
            };
            ctx.html()
                .div()
                .attr(attr!("style" => style))
                .inner(container.elements());
        }

        ContainerType::Header(_) => {
            let tag_spec = container.ctype().html_tag(ctx);
            let mut tag = ctx.html().tag(tag_spec.tag());
            match tag_spec {
                HtmlTag::TagAndId { id, .. } if has_toc_block => {
                    tag.attr(attr!("id" => &id));
                }
                _ => {}
            }
            tag.contents(|ctx| {
                ctx.html()
                    .span()
                    .inner(container.elements());
            });
        }

        // Render normally
        _ => render_container_internal(ctx, container),
    }
}

pub fn render_container_internal(ctx: &mut HtmlContext, container: &Container) {
    // Get HTML tag type for this type of container
    let tag_spec = container.ctype().html_tag(ctx);

    // Get correct ID, based on the render setting
    let random_id = choose_id(ctx, &tag_spec);

    // Build the tag
    let mut tag = ctx.html().tag(tag_spec.tag());

    // Merge the class attribute with the container's class, if it conflicts
    match tag_spec {
        HtmlTag::Tag(_) => tag.attr(attr!(;; container.attributes())),
        HtmlTag::TagAndClass { class, .. } => tag.attr(attr!(
            "class" => class;;
            container.attributes(),
        )),
        HtmlTag::TagAndId { id, .. } => tag.attr(attr!(
            "id" => match random_id {
                Some(ref id) => id,
                None => &id,
            };;
            container.attributes(),
        )),
    };

    // Add container internals
    tag.inner(container.elements());
}

lazy_static! {
    static ref COLOR_REGEX: Regex = {
        RegexBuilder::new(r"^([0-9A-Fa-f]{3}|[0-9A-Fa-f]{6})$")
            .build()
            .unwrap()
    };
}


pub fn render_color(ctx: &mut HtmlContext, color: &str, elements: &[Element]) {
    info!("Rendering color container (color '{color}')");

    let real_color = if COLOR_REGEX.is_match(color) {
        format!("#{color}")
    } else {
        String::from(color)
    };

    ctx.html()
        .span()
        .attr(attr!(
            "style" => "color: " real_color.as_str() ";",
        ))
        .inner(elements);
}

fn choose_id(ctx: &mut HtmlContext, tag_spec: &HtmlTag) -> Option<String> {
    // If we're in a situation where we want a randomly generated ID
    if matches!(tag_spec, HtmlTag::TagAndId { .. }) && !ctx.settings().use_true_ids {
        Some(ctx.random().generate_html_id())
    } else {
        None
    }
}
