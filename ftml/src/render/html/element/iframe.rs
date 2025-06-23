/*
 * render/html/element/iframe.rs
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
use crate::tree::AttributeMap;
use md5;

pub fn render_iframe(ctx: &mut HtmlContext, url: &str, attributes: &AttributeMap) {
    info!("Rendering iframe block (url '{url}')");

    ctx.html().iframe().attr(attr!(
        "src" => url,
        "sandbox" => "allow-scripts allow-top-navigation allow-popups allow-modals allow-same-origin",
        "allowfullscreen" => "",
        "crossorigin";;
        attributes
    ));
}

pub fn render_html(ctx: &mut HtmlContext, contents: &str, external: bool) {
    info!("Rendering html block");

    let id = ctx.random().generate_html_id();

    let hash_result = md5::compute(contents);
    let hash_hex = format!("{:x}", hash_result);

    let prepended_script = ctx.handle().get_html_injected_code(&id);

    if !external {
        ctx.html()
            .iframe()
            .attr(attr!(
                "id" => &id,
                "srcdoc" => &format!("{prepended_script}{contents}"),
                "sandbox" => "allow-scripts allow-top-navigation allow-popups allow-modals",
                "allow" => "fullscreen",
                "allowfullscreen" => "allowfullscreen",
                "style" => "width: 100%; height: 0",
                "class" => "w-iframe-autoresize",
                "frameborder" => "0",
                "allowtransparency" => "true"
            ));
    } else {
        let iframe_src = ctx.handle().get_iframe_link(&hash_hex, &id, ctx.info());
        ctx.html()
            .iframe()
            .attr(attr!(
                "id" => &id,
                "src" => &iframe_src,
                "sandbox" => "allow-scripts allow-top-navigation allow-popups allow-modals allow-same-origin",
                "allow" => "fullscreen",
                "allowfullscreen" => "allowfullscreen",
                "style" => "width: 100%; height: 0",
                "class" => "w-iframe-autoresize",
                "frameborder" => "0",
                "allowtransparency" => "true"
            ));
    }
}
