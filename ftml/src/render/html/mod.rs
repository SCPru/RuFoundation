/*
 * render/html/mod.rs
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

#[cfg(test)]
mod test;

#[macro_use]
mod attributes;
mod builder;
mod context;
mod element;
mod escape;
mod meta;
mod output;
mod random;
mod render;

use std::rc::Rc;
pub use self::meta::{HtmlMeta, HtmlMetaType};
pub use self::output::HtmlOutput;

#[cfg(test)]
use super::prelude;

use self::context::HtmlContext;
use crate::data::{PageCallbacks, PageInfo};
use crate::render::html::element::render_elements;
use crate::render::{Handle, Render};
use crate::settings::WikitextSettings;
use crate::tree::SyntaxTree;

#[derive(Debug)]
pub struct HtmlRender;

impl Render for HtmlRender {
    type Output = HtmlOutput;

    fn render(
        &self,
        tree: &SyntaxTree,
        page_info: &PageInfo,
        page_callbacks: Rc<dyn PageCallbacks>,
        settings: &WikitextSettings,
    ) -> HtmlOutput {
        info!(
            "Rendering HTML (site {}, page {}, category {})",
            page_info.site.as_ref(),
            page_info.page.as_ref(),
            match &page_info.category {
                Some(category) => category.as_ref(),
                None => "_default",
            },
        );

        // fetch page details
        let internal_links = page_callbacks.get_page_info(&tree.internal_links);
        let handle = Handle::new(page_callbacks.clone(), &internal_links);

        let mut ctx = HtmlContext::new(
            page_info,
            page_callbacks,
            &handle,
            settings,
            &tree.table_of_contents,
            tree.has_toc_block,
            &tree.footnotes,
        );

        // Crawl through elements and generate HTML
        render_elements(&mut ctx, &tree.elements);

        // Build and return HtmlOutput
        ctx.into()
    }
}
