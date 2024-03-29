/*
 * render/html/context.rs
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

use super::builder::HtmlBuilder;
use super::escape::escape;
use super::meta::{HtmlMeta, HtmlMetaType};
use super::output::HtmlOutput;
use super::random::Random;
use crate::data::{PageCallbacks, PageRef};
use crate::data::{Backlinks, PageInfo};
use crate::info;
use crate::next_index::{NextIndex, TableOfContentsIndex};
use crate::render::Handle;
use crate::settings::WikitextSettings;
use crate::tree::{Element, VariableScopes};
use std::fmt::{self, Write};
use std::num::NonZeroUsize;
use std::rc::Rc;

#[derive(Debug)]
pub struct HtmlContext<'i, 'h, 'e, 't>
where
    'e: 't,
{
    body: String,
    styles: Vec<String>,
    meta: Vec<HtmlMeta>,
    backlinks: Backlinks<'static>,
    info: &'i PageInfo<'i>,
    callbacks: Rc<dyn PageCallbacks>,
    handle: &'h Handle<'t>,
    settings: &'e WikitextSettings,
    random: Random,

    //
    // Included page scopes
    //
    variables: VariableScopes,

    //
    // Fields from syntax tree
    //
    table_of_contents: &'e [Element<'t>],
    has_toc_block: bool,
    footnotes: &'e [Vec<Element<'t>>],

    //
    // Other fields to track
    //
    code_snippet_index: NonZeroUsize,
    table_of_contents_index: usize,
    equation_index: NonZeroUsize,
    footnote_index: NonZeroUsize,
}

impl<'i, 'h, 'e, 't> HtmlContext<'i, 'h, 'e, 't> {
    #[inline]
    pub fn new(
        info: &'i PageInfo<'i>,
        callbacks: Rc<dyn PageCallbacks>,
        handle: &'h Handle<'t>,
        settings: &'e WikitextSettings,
        table_of_contents: &'e [Element<'t>],
        has_toc_block: bool,
        footnotes: &'e [Vec<Element<'t>>],
    ) -> Self {
        HtmlContext {
            body: String::new(),
            styles: Vec::new(),
            meta: Self::initial_metadata(info),
            backlinks: Backlinks::new(),
            info,
            callbacks,
            handle,
            settings,
            random: Random::default(),
            variables: VariableScopes::new(),
            table_of_contents,
            has_toc_block,
            footnotes,
            code_snippet_index: NonZeroUsize::new(1).unwrap(),
            table_of_contents_index: 0,
            equation_index: NonZeroUsize::new(1).unwrap(),
            footnote_index: NonZeroUsize::new(1).unwrap(),
        }
    }

    fn initial_metadata(info: &PageInfo<'i>) -> Vec<HtmlMeta> {
        // Initial version, we can tune how the metadata is generated later.

        vec![
            HtmlMeta {
                tag_type: HtmlMetaType::HttpEquiv,
                name: str!("Content-Type"),
                value: str!("text/html"),
            },
            HtmlMeta {
                tag_type: HtmlMetaType::Name,
                name: str!("generator"),
                value: info::VERSION.clone(),
            },
            HtmlMeta {
                tag_type: HtmlMetaType::Name,
                name: str!("description"),
                value: {
                    let mut value = str!(info.title);

                    if let Some(ref alt_title) = info.alt_title {
                        str_write!(value, " - {alt_title}");
                    }

                    value
                },
            },
            HtmlMeta {
                tag_type: HtmlMetaType::Name,
                name: str!("keywords"),
                value: info.tags.join(","),
            },
        ]
    }

    // Field access
    #[inline]
    pub fn info(&self) -> &PageInfo<'i> {
        self.info
    }

    #[inline]
    pub fn callbacks(&self) -> Rc<dyn PageCallbacks> {
        self.callbacks.clone()
    }

    #[inline]
    pub fn settings(&self) -> &WikitextSettings {
        self.settings
    }

    #[inline]
    pub fn handle(&self) -> &'h Handle {
        self.handle
    }

    #[inline]
    pub fn random(&mut self) -> &mut Random {
        &mut self.random
    }

    #[inline]
    pub fn variables(&self) -> &VariableScopes {
        &self.variables
    }

    #[inline]
    pub fn variables_mut(&mut self) -> &mut VariableScopes {
        &mut self.variables
    }

    #[inline]
    pub fn table_of_contents(&self) -> &'e [Element<'t>] {
        self.table_of_contents
    }

    #[inline]
    pub fn has_toc_block(&self) -> bool {
        self.has_toc_block
    }

    #[inline]
    pub fn footnotes(&self) -> &'e [Vec<Element<'t>>] {
        self.footnotes
    }

    pub fn next_code_snippet_index(&mut self) -> NonZeroUsize {
        let index = self.code_snippet_index;
        self.code_snippet_index = NonZeroUsize::new(index.get() + 1).unwrap();
        index
    }

    pub fn next_table_of_contents_index(&mut self) -> usize {
        let index = self.table_of_contents_index;
        self.table_of_contents_index += 1;
        index
    }

    pub fn next_equation_index(&mut self) -> NonZeroUsize {
        let index = self.equation_index;
        self.equation_index = NonZeroUsize::new(index.get() + 1).unwrap();
        index
    }

    pub fn next_footnote_index(&mut self) -> NonZeroUsize {
        let index = self.footnote_index;
        self.footnote_index = NonZeroUsize::new(index.get() + 1).unwrap();
        index
    }

    #[inline]
    pub fn get_footnote(&self, index_one: NonZeroUsize) -> Option<&'e [Element<'t>]> {
        self.footnotes
            .get(usize::from(index_one) - 1)
            .map(|elements| elements.as_slice())
    }

    pub fn page_exists(&mut self, page_ref: &PageRef) -> bool {
        self.handle().get_page_exists(page_ref)
    }

    // Buffer management
    #[inline]
    pub fn buffer(&mut self) -> &mut String {
        &mut self.body
    }

    #[inline]
    pub fn add_style(&mut self, style: String) {
        self.styles.push(style);
    }

    #[inline]
    pub fn push_raw(&mut self, ch: char) {
        self.buffer().push(ch);
    }

    #[inline]
    pub fn push_raw_str(&mut self, s: &str) {
        self.buffer().push_str(s);
    }

    #[inline]
    pub fn push_escaped(&mut self, s: &str) {
        escape(self.buffer(), s);
    }

    #[inline]
    pub fn html(&mut self) -> HtmlBuilder<'_, 'i, 'h, 'e, 't> {
        HtmlBuilder::new(self)
    }
}

impl<'i, 'h, 'e, 't> From<HtmlContext<'i, 'h, 'e, 't>> for HtmlOutput {
    #[inline]
    fn from(ctx: HtmlContext<'i, 'h, 'e, 't>) -> HtmlOutput {
        let HtmlContext {
            body,
            styles,
            meta,
            backlinks,
            ..
        } = ctx;

        HtmlOutput {
            body,
            styles,
            meta,
            backlinks,
        }
    }
}

impl<'i, 'h, 'e, 't> Write for HtmlContext<'i, 'h, 'e, 't> {
    #[inline]
    fn write_str(&mut self, s: &str) -> fmt::Result {
        self.buffer().write_str(s)
    }
}

impl<'i, 'h, 'e, 't> NextIndex<TableOfContentsIndex> for HtmlContext<'i, 'h, 'e, 't> {
    #[inline]
    fn next(&mut self) -> usize {
        self.next_table_of_contents_index()
    }
}
