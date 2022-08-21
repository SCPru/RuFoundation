/*
 * render/html/element/table.rs
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
use crate::tree::{Table, Alignment};
use std::num::NonZeroU32;

pub fn render_table(ctx: &mut HtmlContext, table: &Table) {
    info!("Rendering table");

    let mut column_span_buf = String::new();
    let value_one = NonZeroU32::new(1).unwrap();

    // Full table
    ctx.html()
        .table()
        .attr(attr!(;; &table.attributes))
        .contents(|ctx| {
            ctx.html().tbody().contents(|ctx| {
                // Each row
                for row in &table.rows {
                    ctx.html() //
                        .tr()
                        .attr(attr!(;; &row.attributes))
                        .contents(|ctx| {
                            // Each cell in a row
                            for cell in &row.cells {
                                let elements: &[Element] = &cell.elements;
                                let align_style = match cell.align {
                                    Some(Alignment::Left) => "text-align: left",
                                    Some(Alignment::Right) => "text-align: right",
                                    Some(Alignment::Center) => "text-align: center",
                                    Some(Alignment::Justify) => "text-align: justify",
                                    None => "",
                                };

                                if cell.column_span > value_one {
                                    column_span_buf.clear();
                                    str_write!(column_span_buf, "{}", cell.column_span);
                                }

                                ctx.html()
                                    .table_cell(cell.header)
                                    .attr(attr!(
                                        // Add column span if not default (1)
                                        "colspan" => &column_span_buf;
                                            if cell.column_span > value_one,

                                        // Add alignment if specified
                                        "style" => align_style;
                                            if cell.align.is_some();;

                                        &cell.attributes,
                                    ))
                                    .inner(elements);
                            }
                        });
                }
            });
        });
}
