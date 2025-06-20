/*
 * render/html/element/mod.rs
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

//! Module that implements HTML rendering for `Element` and its children.

mod collapsible;
mod container;
mod date;
mod definition_list;
mod footnotes;
mod form;
mod iframe;
mod image;
mod include;
mod link;
mod list;
mod math;
mod module;
mod table;
mod tabs;
mod text;
mod toc;
mod user;

mod prelude {
    pub use super::super::attributes::AddedAttributes;
    pub use super::super::context::HtmlContext;
    
    pub use super::{render_element, render_elements};
    pub use crate::tree::Element;
}

use self::collapsible::{render_collapsible, Collapsible};
use self::container::{render_color, render_container};
use self::date::render_date;
use self::definition_list::render_definition_list;
use self::footnotes::{render_footnote, render_footnote_block};
use self::form::render_form_input;
use self::iframe::{render_html, render_iframe};
use self::image::render_image;
use self::include::{render_include, render_variable};
use self::link::{render_anchor, render_link};
use self::list::render_list;
use self::math::{render_equation_reference, render_math_block, render_math_inline};
use self::module::render_module;
use self::table::render_table;
use self::tabs::render_tabview;
use self::text::{render_code, render_email, render_wikitext_raw, render_html_entity};
use self::toc::render_table_of_contents;
use self::user::render_user;
use super::attributes::AddedAttributes;
use super::HtmlContext;
use crate::tree::{Element, ClearFloat};
use ref_map::*;

pub fn render_elements(ctx: &mut HtmlContext, elements: &[Element]) {
    info!("Rendering elements (length {})", elements.len());

    for element in elements {
        render_element(ctx, element);
    }
}

pub fn render_element(ctx: &mut HtmlContext, element: &Element) {
    macro_rules! ref_cow {
        ($input:expr) => {
            $input.ref_map(|s| s.as_ref())
        };
    }

    info!("Rendering element '{}'", element.name());

    match element {
        Element::Fragment(elements) => render_elements(ctx, elements),
        Element::AlignMarker(_) => {},
        Element::Container(container) => render_container(ctx, container),
        Element::Module(module) => render_module(ctx, module),
        Element::Text(text) => ctx.push_escaped(text),
        Element::Raw(text) => render_wikitext_raw(ctx, text),
        Element::HtmlEntity(text) => render_html_entity(ctx, text),
        Element::Variable(name) => render_variable(ctx, name),
        Element::Email(email) => render_email(ctx, email),
        Element::Table(table) => render_table(ctx, table),
        Element::FormInput(input) => render_form_input(ctx, input),
        Element::TabView(tabs) => render_tabview(ctx, tabs),
        Element::Anchor {
            elements,
            attributes,
            target,
        } => render_anchor(ctx, elements, attributes, *target),
        Element::AnchorName(id) => {
            ctx.html().a().attr(attr!("id" => id));
        }
        Element::Link {
            ltype,
            link,
            label,
            target,
        } => render_link(ctx, link, label, *target, *ltype),
        Element::Image {
            source,
            link,
            link_target,
            alignment,
            attributes,
        } => render_image(ctx, source, link, *link_target, *alignment, attributes),
        Element::List {
            ltype,
            items,
            attributes,
        } => render_list(ctx, *ltype, items, attributes),
        Element::DefinitionList(items) => render_definition_list(ctx, items),
        Element::Collapsible {
            elements,
            attributes,
            start_open,
            show_text,
            hide_text,
            show_top,
            show_bottom,
            text_align,
        } => render_collapsible(
            ctx,
            Collapsible::new(
                elements,
                attributes,
                *start_open,
                ref_cow!(show_text),
                ref_cow!(hide_text),
                *show_top,
                *show_bottom,
                *text_align,
            ),
        ),
        Element::TableOfContents { align, attributes } => {
            render_table_of_contents(ctx, *align, attributes)
        }
        Element::Footnote => render_footnote(ctx),
        Element::FootnoteBlock { title, hide } => {
            if !(*hide || ctx.footnotes().is_empty()) {
                render_footnote_block(ctx, ref_cow!(title));
            }
        }
        Element::User { name, show_avatar } => render_user(ctx, name, *show_avatar),
        Element::Date {
            value,
            format,
            hover,
        } => render_date(ctx, *value, ref_cow!(format), *hover),
        Element::Color { color, elements } => render_color(ctx, color, elements),
        Element::Code { contents, language } => {
            render_code(ctx, ref_cow!(language), contents)
        }
        Element::Math { name, latex_source } => {
            render_math_block(ctx, ref_cow!(name), latex_source)
        }
        Element::MathInline { latex_source } => render_math_inline(ctx, latex_source),
        Element::EquationReference(name) => render_equation_reference(ctx, name),
        Element::Html { contents, external } => render_html(ctx, contents, *external),
        Element::Iframe { url, attributes } => render_iframe(ctx, url, attributes),
        Element::Include {
            variables,
            location,
            elements,
            ..
        } => render_include(ctx, location, variables, elements),
        Element::LineBreak => {
            ctx.html().br();
        }
        Element::LineBreaks(amount) => {
            let amount = amount.get();

            for _ in 0..amount {
                ctx.html().br();
            }
        }
        Element::ClearFloat(clear_float) => {
            let style = match clear_float {
                ClearFloat::Left => "clear: left; ",
                ClearFloat::Right => "clear: right; ",
                ClearFloat::Both => "clear: both; ",
            };
            ctx.html().div().attr(attr!(
                "style" => style "height: 0; font-size: 1px;",
            ));
        }
        Element::HorizontalRule => {
            ctx.html().hr();
        }
        Element::Partial(_) => panic!("Encountered partial element during parsing"),
        Element::Void => {},
    }
}