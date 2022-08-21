/*
 * render/html/element/tabs.rs
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
use crate::tree::Tab;

pub fn render_tabview(ctx: &mut HtmlContext, tabs: &[Tab]) {
    info!("Rendering tabview (tabs {})", tabs.len());

    ctx.html()
        .div()
        .attr(attr!("class" => "yui-navset yui-navset-top w-tabview"))
        .contents(|ctx| {
            // start ul
            ctx.html()
                .ul()
                .attr(attr!("class" => "yui-nav"))
                .contents(|ctx| {
                    for (i, tab) in tabs.iter().enumerate() {
                        ctx.html()
                            .li()
                            .attr(if i == 0 { attr!("class" => "selected", "title" => "active") } else { attr!() })
                            .contents(|ctx| {
                                ctx.html()
                                    .a()
                                    .attr(attr!("href" => "javascript:;"))
                                    .contents(|ctx| {
                                        ctx.html()
                                            .em()
                                            .inner(&tab.label);
                                    });
                            });
                    }
                });
            // end ul
            ctx.html()
                .div()
                .attr(attr!("class" => "yui-content"))
                .contents(|ctx| {
                    for (i, tab) in tabs.iter().enumerate() {
                        let style = if i == 0 { "display: block" } else { "display: none" };
                        ctx.html()
                            .div()
                            .attr(attr!("class" => "w-tabview-tab", "style" => style))
                            .inner(&tab.elements);
                    }
                });
        });
}
