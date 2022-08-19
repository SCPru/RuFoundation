/*
 * render/html/element/toc.rs
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
use crate::tree::{Alignment, AttributeMap, FloatAlignment};

pub fn render_table_of_contents(
    ctx: &mut HtmlContext,
    align: Option<Alignment>,
    attributes: &AttributeMap,
) {
    info!("Creating table of contents");

    if ctx.settings().syntax_compatibility {

        let (msg_toc_close, msg_toc_open, msg_toc) = {
            let msg_toc_close = ctx.handle().get_message("toc-close");
            let msg_toc_open = ctx.handle().get_message("toc-open");
            let msg_toc = ctx.handle().get_message("table-of-contents");
            (msg_toc_close, msg_toc_open, msg_toc)
        };

        let float_class_append = match align {
            Some(Alignment::Left) => " floatleft",
            Some(Alignment::Right) => " floatright",
            _ => "",
        };

        let build_toc = |ctx: &mut HtmlContext| {
            ctx.html()
                .div()
                .attr(attr!("class" => &format!("w-toc{float_class_append}"), "id" => "toc"))
                .contents(|ctx| {
                    ctx.html()
                        .div()
                        .attr(attr!("class" => "toc-action-bar"))
                        .contents(|ctx| {
                            ctx.html()
                                .a()
                                .attr(attr!("class" => "w-toc-hide", "href" => "javascript:;"))
                                .inner(msg_toc_close.as_str());
                            ctx.html()
                                .a()
                                .attr(attr!("class" => "w-toc-show", "style" => "display: none", "href" => "javascript:;"))
                                .inner(msg_toc_open.as_str());
                        });
                    ctx.html()
                        .div()
                        .attr(attr!("class" => "title"))
                        .inner(msg_toc.as_str());

                    let table_of_contents = ctx.table_of_contents();

                    ctx.html()
                        .div()
                        .attr(attr!("class" => "w-toc-content", "id" => "toc-list"))
                        .inner(table_of_contents);
                });
        };

        // here comes the weird part
        // if the TOC is not floating, it's wrapped in a TABLE

        match float_class_append {
            "" => {
                ctx.html()
                    .table()
                    .attr(attr!("style" => "margin: 0; padding: 0"))
                    .contents(|ctx| {
                        ctx.html()
                            .tbody()
                            .contents(|ctx| { 
                                ctx.html()
                                    .tr()
                                    .contents(|ctx| {
                                        ctx.html()
                                            .table_cell(false)
                                            .attr(attr!("style" => "margin: 0; padding: 0"))
                                            .contents(build_toc);
                                    });
                            });
                    });
            }
            _ => {
                build_toc(ctx);
            }
        };

    } else {

        let use_true_ids = ctx.settings().use_true_ids;

        let class_value = match align {
            None => "",
            Some(align) => {
                // Only valid for float left / right
                FloatAlignment { align, float: true }.html_class()
            }
        };
    
        ctx.html()
            .div()
            .attr(attr!(
                "id" => "wj-toc"; if use_true_ids,
                "class" => class_value; if align.is_some();;
                attributes
            ))
            .contents(|ctx| {
                // TOC buttons
                ctx.html()
                    .div()
                    .attr(attr!("id" => "wj-toc-action-bar"; if use_true_ids))
                    .contents(|ctx| {
                        // TODO button
                        ctx.html().a().attr(attr!(
                            "href" => "javascript:;",
                            "onclick" => "WIKIJUMP.page.listeners.foldToc(event)",
                        ));
                    });
    
                // TOC Heading
                let table_of_contents_title = ctx
                    .handle()
                    .get_message("table-of-contents");
    
                ctx.html()
                    .div()
                    .attr(attr!("class" => "title"))
                    .inner(table_of_contents_title);
    
                // TOC List
                let table_of_contents = ctx.table_of_contents();
    
                ctx.html()
                    .div()
                    .attr(attr!("id" => "wj-toc-list"; if use_true_ids))
                    .inner(table_of_contents);
            });

    }
}
