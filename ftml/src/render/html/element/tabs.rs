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

use std::iter;

use super::prelude::*;
use crate::tree::Tab;

pub fn render_tabview(ctx: &mut HtmlContext, tabs: &[Tab]) {
    info!("Rendering tabview (tabs {})", tabs.len());

    if ctx.settings().syntax_compatibility {
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
    } else {
        
        // Generate IDs for each tab
        let button_ids = generate_ids(ctx.random(), tabs.len());
        let tab_ids = generate_ids(ctx.random(), tabs.len());

        // Entire tab view
        ctx.html()
            .element("wj-tabs")
            .attr(attr!(
                "class" => "wj-tabs",
            ))
            .contents(|ctx| {
                // Tab buttons
                ctx.html()
                    .div()
                    .attr(attr!(
                        "class" => "wj-tabs-button-list",
                        "role" => "tablist",
                    ))
                    .contents(|ctx| {
                        for (i, tab) in tabs.iter().enumerate() {
                            let (tab_selected, tab_index) = if i == 0 {
                                ("true", "0")
                            } else {
                                ("false", "-1")
                            };

                            // Each tab button
                            ctx.html()
                                .element("wj-tabs-button")
                                .attr(attr!(
                                    "class" => "wj-tabs-button",
                                    "id" => &button_ids[i],
                                    "role" => "tab",
                                    "aria-label" => &tab.label,
                                    "aria-selected" => tab_selected,
                                    "aria-controls" => &tab_ids[i],
                                    "tabindex" => tab_index,
                                ))
                                .inner(&tab.label);
                        }
                    });

                // Tab panels
                ctx.html()
                    .div()
                    .attr(attr!(
                        "class" => "wj-tabs-panel-list",
                    ))
                    .contents(|ctx| {
                        for (i, tab) in tabs.iter().enumerate() {
                            // Each tab panel
                            ctx.html()
                                .div()
                                .attr(attr!(
                                    "class" => "wj-tabs-panel",
                                    "id" => &tab_ids[i],
                                    "role" => "tabpanel",
                                    "aria-labelledby" => &button_ids[i],
                                    "tabindex" => "0",
                                    "hidden"; if i > 0,
                                ))
                                .inner(&tab.elements);
                        }
                    });
            });
    }
}

fn generate_ids(random: &mut Random, len: usize) -> Vec<String> {
    iter::repeat(())
        .take(len)
        .map(|_| random.generate_html_id())
        .collect()
}