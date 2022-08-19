/*
 * render/html/element/image.rs
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
use crate::tree::{AttributeMap, FloatAlignment, ImageSource, LinkLocation, Alignment};
use crate::url::normalize_link;

pub fn render_image(
    ctx: &mut HtmlContext,
    source: &ImageSource,
    link: &Option<LinkLocation>,
    alignment: Option<FloatAlignment>,
    attributes: &AttributeMap,
) {
    info!(
        "Rendering image element (source '{}', link {}, alignment {}, float {})",
        source.name(),
        match link {
            Some(link) => format!("{:?}", link),
            None => str!("<none>"),
        },
        match alignment {
            Some(image) => image.align.name(),
            None => "<default>",
        },
        match alignment {
            Some(image) => image.float,
            None => false,
        },
    );

    let source_url = ctx
        .handle()
        .get_image_link(source, ctx.info(), ctx.settings());

    match source_url {
        // Found URL
        Some(url) => render_image_element(ctx, &url, link, alignment, attributes),

        // Missing or error
        None => render_image_missing(ctx),
    }
}

fn render_image_element(
    ctx: &mut HtmlContext,
    url: &str,
    link: &Option<LinkLocation>,
    alignment: Option<FloatAlignment>,
    attributes: &AttributeMap,
) {
    debug!("Found URL, rendering image (value '{url}')");

    if ctx.settings().syntax_compatibility {

        let build_image = |ctx: &mut HtmlContext| {
            ctx.html().img().attr(attr!(
                "src" => url,
                "alt" => url.split("/").last().unwrap();;
                attributes
            ));
        };

        let build_link = |ctx: &mut HtmlContext| {
            match link {
                Some(link) => {
                    let url = normalize_link(link, ctx.handle());
                    ctx.html()
                        .a()
                        .attr(attr!("href" => &url, "target" => "_blank"))
                        .contents(build_image);
                }
                None => build_image(ctx),
            }
        };

        let align_div_class = match alignment {
            Some(FloatAlignment{align: Alignment::Left, float: true}) => "floatleft",
            Some(FloatAlignment{align: Alignment::Right, float: true}) => "floatright",
            Some(FloatAlignment{align: Alignment::Left, float: false}) => "alignleft",
            Some(FloatAlignment{align: Alignment::Right, float: false}) => "alignright",
            Some(FloatAlignment{align: Alignment::Center, float: false}) => "aligncenter",
            _ => ""
        };

        match align_div_class {
            "" => build_link(ctx),
            other => {
                ctx.html().div()
                    .attr(attr!("class" => format!("image-container {other}").as_str()))
                    .contents(build_link);
            }
        }

    } else {

        let (space, align_class) = match alignment {
            Some(align) => (" ", align.html_class()),
            None => ("", ""),
        };

        ctx.html()
            .div()
            .attr(attr!(
                "class" => "wj-image-container" space align_class,
            ))
            .contents(|ctx| {
                let build_image = |ctx: &mut HtmlContext| {
                    ctx.html().img().attr(attr!(
                        "class" => "wj-image",
                        "src" => url,
                        "crossorigin";;
                        attributes
                    ));
                };

                match link {
                    Some(link) => {
                        let url = normalize_link(link, ctx.handle());
                        ctx.html()
                            .a()
                            .attr(attr!("href" => &url))
                            .contents(build_image);
                    }
                    None => build_image(ctx),
                };
            });

    }
}

fn render_image_missing(ctx: &mut HtmlContext) {
    debug!("Image URL unresolved, missing or error");

    let compat = ctx.settings().syntax_compatibility;

    let message = ctx
        .handle()
        .get_message("image-context-bad");

    ctx.html()
        .div()
        .attr(attr!("class" => if compat { "error-block" } else { "wj-error-block" }))
        .inner(message);
}
