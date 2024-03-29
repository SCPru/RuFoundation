/*
 * render/html/element/link.rs
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

use std::borrow::Cow;

use super::prelude::*;
use crate::tree::{
    AnchorTarget, AttributeMap, Element, LinkLabel, LinkLocation, LinkType,
};

pub fn render_anchor(
    ctx: &mut HtmlContext,
    elements: &[Element],
    attributes: &AttributeMap,
    target: Option<AnchorTarget>,
) {
    info!("Rendering anchor");

    let target_value = match target {
        Some(target) => target.html_attr(),
        None => "",
    };

    ctx.html()
        .a()
        .attr(attr!(
            "target" => target_value; if target.is_some();;
            attributes,
        ))
        .inner(elements);
}

pub fn render_link(
    ctx: &mut HtmlContext,
    link: &LinkLocation,
    label: &LinkLabel,
    target: Option<AnchorTarget>,
    ltype: LinkType,
) {
    info!("Rendering link '{:?}' (type {})", link, ltype.name());

    let label = {
        let mut o_label: String = String::new();
        ctx.handle().get_link_label(link, label, |label| {
            o_label = label.to_owned();
        });
        o_label
    };

    let url = match link {
        LinkLocation::Page(page_ref, anchor) => {
            Cow::Owned(format!("/{}{}", &page_ref.to_string(), match anchor {
                Some(anchor) => format!("#{anchor}"),
                None => String::from("")
            }))
        },
        LinkLocation::Url(url) => url.to_owned(),
    };

    let target_value = match target {
        Some(target) => target.html_attr(),
        None => "",
    };

    let css_class = match link {
        LinkLocation::Url(_) => None,
        LinkLocation::Page(page, _) => {
            if ctx.page_exists(page) {
                None
            } else {
                Some("newpage")
            }
        }
    };

    let mut tag = ctx.html().a();
    tag.attr(attr!(
        "href" => &url,
        "target" => target_value; if target.is_some(),
        "class" => css_class.unwrap_or(""); if css_class.is_some(),
    ));

    // Add <a> internals, i.e. the link name
    tag.inner(label);
}
