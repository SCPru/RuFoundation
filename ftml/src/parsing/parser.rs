/*
 * parsing/parser.rs
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

use bitflags::bitflags;

use super::condition::ParseCondition;
use super::{prelude::*, parse_internal, UnstructuredParseResult, WikiScriptScope};
use super::rule::Rule;
use super::RULE_PAGE;
use crate::data::{PageCallbacks, PageInfo, PageRef};
use crate::render::text::TextRender;
use crate::tokenizer::Tokenization;
use crate::tree::{AcceptsPartial, HeadingLevel, Container, ContainerType, AttributeMap};
use std::borrow::Cow;
use std::cell::RefCell;
use std::collections::HashMap;
use regex::Regex;
use std::vec;
use std::rc::Rc;
use std::{mem, ptr};
use std::ops::{Deref, DerefMut};

lazy_static! {
    static ref VARIABLE_REGEX: Regex =
        Regex::new(r"\{@(?P<name>[a-zA-Z0-9_\-]+)\}").unwrap();
}

const MAX_RECURSION_DEPTH: usize = 100;

bitflags! {
    #[derive(Clone, Copy, Debug, PartialEq, Eq, Hash)]
    pub struct ParserTransactionFlags: u32 {
        const TOC = 1 << 1;
        const Footnotes = 1 << 2;
        const FootnoteFlag = 1 << 3;
        const InternalLinks = 1 << 4;
        const AcceptsPartial = 1 << 5;
        const Scopes = 1 << 6;
        const Code = 1 << 7;
        const HTML = 1 << 8;
    }
}

#[derive(Debug, Clone)]
struct ParserState<'t> {
    // Migrated from ParserWrap.
    accepts_partial: AcceptsPartial,

    // Table of Contents
    //
    // Schema: Vec<(depth, _, name)>
    //
    // Note: These three are in Rc<_> items so that the Parser
    //       can be cloned. This struct is intended as a
    //       cheap pointer object, with the true contents
    //       here preserved across parser child instances.
    table_of_contents: Rc<RefCell<Vec<(usize, String)>>>,

    // Footnotes
    //
    // Schema: Vec<List of elements in a footnote>
    footnotes: Rc<RefCell<Vec<Vec<Element<'t>>>>>,

    // List of [[code]]. First element is type
    code: Rc<RefCell<Vec<(String, String)>>>,

    // List of [[html]]
    html: Rc<RefCell<Vec<String>>>,

    // Internal links
    internal_links: Rc<RefCell<Vec<PageRef<'t>>>>,

    // Flags
    has_footnote_block: bool, // Whether a [[footnoteblock]] was created.
    has_toc_block: bool, // Whether a [[toc]] was created.
    in_footnote: bool, // Whether we're currently inside [[footnote]] ... [[/footnote]].

    // WikiScript variable scopes
    scopes: Vec<WikiScriptScope<'t>>,
}

#[derive(Debug)]
pub struct ParserTransaction<'a, 'r, 't> {
    flags: ParserTransactionFlags,
    parser: &'a mut Parser<'r, 't>,
    applied: bool
}

impl ParserTransaction<'_, '_, '_> {
    pub fn commit(&mut self) {
        assert!(!self.applied);
        self.applied = true;
        self.parser.pop_state(ParserTransactionFlags::all())
    }

    pub fn rollback(&mut self) {
        if !self.applied {
            self.applied = true;
            self.parser.pop_state(ParserTransactionFlags::all().difference(self.flags))
        }
    }
}

impl<'a, 'r, 't> Deref for ParserTransaction<'a, 'r, 't> {
    type Target = Parser<'r, 't>;

    fn deref(&self) -> &Parser<'r, 't> {
        self.parser
    }
}

impl<'a, 'r, 't> DerefMut for ParserTransaction<'a, 'r, 't> {
    fn deref_mut(&mut self) -> &mut Parser<'r, 't> {
        self.parser
    }
}

impl Drop for ParserTransaction<'_, '_, '_> {
    fn drop(&mut self) {
        self.rollback();
    }
}

#[derive(Debug, Clone)]
pub struct Parser<'r, 't> {
    // Page and parse information
    page_info: &'r PageInfo<'t>,
    page_callbacks: Rc<dyn PageCallbacks>,
    settings: &'r WikitextSettings,

    // Parse state
    current: &'r ExtractedToken<'t>,
    remaining: &'r [ExtractedToken<'t>],
    full_text: FullText<'t>,
    ast_cache: Rc<RefCell<HashMap<usize, (usize, ParseSuccess<'r, 't, Elements<'t>>)>>>,

    // Rule state
    rule: Rule,
    depth: usize,

    // State that affects the output.
    state: Vec<ParserState<'t>>,

    // Flags
    start_of_line: bool,
}

impl<'r, 't> Parser<'r, 't> {
    /// Constructor. Should only be created by `parse()`.
    ///
    /// All other instances should be `.clone()` or `.clone_with_rule()`d from
    /// the main instance used during parsing.
    pub(crate) fn new(
        tokenization: &'r Tokenization<'t>,
        page_info: &'r PageInfo<'t>,
        page_callbacks: Rc<dyn PageCallbacks>,
        settings: &'r WikitextSettings,
    ) -> Self {
        let scopes = vec![WikiScriptScope::new()];

        let full_text = tokenization.full_text();
        let (current, remaining) = tokenization
            .tokens()
            .split_first()
            .expect("Parsed tokens list was empty (expected at least one element)");

        let root_state = ParserState {
            accepts_partial: AcceptsPartial::None,
            table_of_contents: make_shared_vec(),
            footnotes: make_shared_vec(),
            code: make_shared_vec(),
            html: make_shared_vec(),
            internal_links: make_shared_vec(),
            has_footnote_block: false,
            has_toc_block: false,
            in_footnote: false,
            scopes,
        };

        Parser {
            page_info,
            page_callbacks,
            settings,
            current,
            remaining,
            ast_cache: Rc::new(RefCell::new(HashMap::new())),
            full_text,
            rule: RULE_PAGE,
            depth: 0,
            start_of_line: true,
            state: vec![root_state]
        }
    }

    // This saves current parser state.
    pub fn transaction(&mut self, flags: ParserTransactionFlags) -> ParserTransaction<'_, 'r, 't> {
        let current = self.state().clone();

        let cloned_toc = if flags.contains(ParserTransactionFlags::TOC) {
            Rc::new(RefCell::new(current.table_of_contents.borrow().to_vec()))
        } else {
            current.table_of_contents
        };

        let cloned_footnotes = if flags.contains(ParserTransactionFlags::Footnotes) {
            Rc::new(RefCell::new(current.footnotes.borrow().to_vec()))
        } else {
            current.footnotes
        };

        let cloned_code = if flags.contains(ParserTransactionFlags::Code) {
            Rc::new(RefCell::new(current.code.borrow().to_vec()))
        } else {
            current.code
        };

        let cloned_html = if flags.contains(ParserTransactionFlags::HTML) {
            Rc::new(RefCell::new(current.html.borrow().to_vec()))
        } else {
            current.html
        };

        let cloned_internal_links = if flags.contains(ParserTransactionFlags::InternalLinks) {
            Rc::new(RefCell::new(current.internal_links.borrow().to_vec()))
        } else {
            current.internal_links
        };

        self.state.push(ParserState {
            accepts_partial: current.accepts_partial,
            table_of_contents: cloned_toc,
            footnotes: cloned_footnotes,
            code: cloned_code,
            html: cloned_html,
            internal_links: cloned_internal_links,
            has_footnote_block: current.has_footnote_block,
            has_toc_block: current.has_toc_block,
            in_footnote: current.in_footnote,
            scopes: current.scopes,
        });

        ParserTransaction {
            parser: self,
            flags,
            applied: false
        }
    }

    // This pops the stack and persists all values specified in flags on top of previously known value.
    fn pop_state(&mut self, flags: ParserTransactionFlags) {
        assert!(self.state.len() > 1);

        let last_known = self.state.pop().unwrap().clone();
        let current = self.state_mut();

        if flags.contains(ParserTransactionFlags::AcceptsPartial) {
            current.accepts_partial = last_known.accepts_partial;
        }

        if flags.contains(ParserTransactionFlags::TOC) {
            current.has_toc_block = last_known.has_toc_block;
            current.table_of_contents = last_known.table_of_contents;
        }

        if flags.contains(ParserTransactionFlags::Footnotes) {
            current.has_footnote_block = last_known.has_footnote_block;
            current.footnotes = last_known.footnotes;
        }

        if flags.contains(ParserTransactionFlags::Code) {
            current.code = last_known.code;
        }

        if flags.contains(ParserTransactionFlags::HTML) {
            current.html = last_known.html;
        }

        if flags.contains(ParserTransactionFlags::FootnoteFlag) {
            current.in_footnote = last_known.in_footnote;
        }

        if flags.contains(ParserTransactionFlags::InternalLinks) {
            current.internal_links = last_known.internal_links;
        }

        if flags.contains(ParserTransactionFlags::Scopes) {
            current.scopes = last_known.scopes;
        }
    }

    //
    #[inline]
    fn state(&self) -> &ParserState<'t> {
        assert!(!self.state.is_empty());
        return self.state.last().unwrap()
    }

    #[inline]
    fn state_mut(&mut self) -> &mut ParserState<'t> {
        assert!(!self.state.is_empty());
        return self.state.last_mut().unwrap()
    }

    // This runs a sub-parser, appending state to current structure.
    #[inline]
    pub fn sub_parse(&mut self, mut tokens: Vec<ExtractedToken<'t>>) -> Vec<Element<'t>> {
        match tokens.first() {
            Some(ExtractedToken{token: Token::InputStart, ..}) => {},
            None => {},
            _ => {
                tokens.insert(0, ExtractedToken{token: Token::InputStart, slice: "", span: 0..0});
            }
        }

        match tokens.last() {
            Some(ExtractedToken{token: Token::InputEnd, ..}) => {},
            None => {},
            Some(ExtractedToken{span, ..}) => {
                tokens.push(ExtractedToken{token: Token::InputEnd, slice: "", span: span.end..span.end});
            }
        }

        let tokens_as_raw_text = tokens.iter().map(|x| x.slice).collect::<Vec<&str>>().join("");
        let sub_tokenization: Tokenization = Tokenization::new(self.full_text, tokens);
        let UnstructuredParseResult {
            result,
            table_of_contents_depths,
            footnotes,
            html,
            code,
            has_footnote_block,
            has_toc_block,
            internal_links,
        } = parse_internal(self.page_info, self.page_callbacks.clone(), self.settings, &sub_tokenization);

        match result {
            Ok(ParseSuccess{item, ..}) => {
                let elements: Vec<Element<'static>> = item.iter().map(|element| element.to_owned()).collect();

                let state = self.state_mut();

                for toc_depth in table_of_contents_depths {
                    state.table_of_contents.borrow_mut().push(toc_depth.to_owned());
                }
        
                for foot in footnotes {
                    let elements = foot.iter().map(|element| element.to_owned()).collect();
                    state.footnotes.borrow_mut().push(elements);
                }

                for s in html {
                    state.html.borrow_mut().push(s);
                }

                for s in code {
                    state.code.borrow_mut().push(s);
                }

                for internal in internal_links {
                    state.internal_links.borrow_mut().push(internal.to_owned());
                }
        
                state.has_footnote_block |= has_footnote_block;
                state.has_toc_block |= has_toc_block;
                
                elements
            }
            Err(_) => {
                let element = Element::Container(Container::new(
                    ContainerType::Paragraph,
                    vec![text!(&tokens_as_raw_text)],
                    AttributeMap::new(),
                )).to_owned();

                vec![element]
            }
        }
    }

    // Getters
    #[inline]
    pub fn page_info(&self) -> &PageInfo<'t> {
        self.page_info
    }

    #[inline]
    pub fn page_callbacks(&self) -> Rc<dyn PageCallbacks> {
        self.page_callbacks.clone()
    }

    #[inline]
    pub fn settings(&self) -> &WikitextSettings {
        self.settings
    }

    #[inline]
    pub fn full_text(&self) -> FullText<'t> {
        self.full_text
    }

    #[inline]
    pub fn rule(&self) -> Rule {
        self.rule
    }

    #[inline]
    pub fn accepts_partial(&self) -> AcceptsPartial {
        self.state().accepts_partial
    }

    #[inline]
    pub fn in_footnote(&self) -> bool {
        self.state().in_footnote
    }

    #[inline]
    pub fn has_footnote_block(&self) -> bool {
        self.state().has_footnote_block
    }

    #[inline]
    pub fn has_toc_block(&self) -> bool {
        self.state().has_toc_block
    }

    #[inline]
    pub fn start_of_line(&self) -> bool {
        self.start_of_line
    }

    #[inline]
    pub fn scope_depth(&self) -> u32 {
        self.state().scopes.len() as u32
    }

    #[inline]
    pub fn current_scope(&self) -> &WikiScriptScope<'t> {
        let state =  self.state();

        state.scopes.last().unwrap()
    }

    #[inline]
    pub fn current_scope_mut(&mut self) -> &mut WikiScriptScope<'t> {
        let state =  self.state_mut();

        state.scopes.last_mut().unwrap()
    }

    #[inline]
    pub fn variable(&mut self, name: Cow<'t, str>) -> Cow<'t, str> {
        let scope = self.current_scope();
        
        match scope.get(&name) {
            Some(value) => value.0.to_owned(),
            None => Cow::from("")
        }
    }

    // Setters
    #[inline]
    pub fn set_rule(&mut self, rule: Rule) {
        self.rule = rule;
    }

    pub fn clone_with_rule(&self, rule: Rule) -> Self {
        let mut clone = self.clone();
        clone.set_rule(rule);
        clone
    }

    pub fn depth_increment(&mut self) -> Result<(), ParseWarning> {
        self.depth += 1;
        debug!("Incrementing recursion depth to {}", self.depth);

        if self.depth > MAX_RECURSION_DEPTH {
            return Err(self.make_warn(ParseWarningKind::RecursionDepthExceeded));
        }

        Ok(())
    }

    #[inline]
    pub fn depth_decrement(&mut self) {
        self.depth -= 1;
        debug!("Decrementing recursion depth to {}", self.depth);
    }

    #[inline]
    pub fn set_accepts_partial(&mut self, value: AcceptsPartial) {
        self.state_mut().accepts_partial = value;
    }

    #[inline]
    pub fn set_footnote_flag(&mut self, value: bool) {
        self.state_mut().in_footnote = value;
    }

    #[inline]
    pub fn set_footnote_block(&mut self) {
        self.state_mut().has_footnote_block = true;
    }

    #[inline]
    pub fn set_toc_block(&mut self) {
        self.state_mut().has_toc_block = true;
    }

    // Parse settings helpers
    pub fn check_page_syntax(&self) -> Result<(), ParseWarning> {
        if self.settings.enable_page_syntax {
            Ok(())
        } else {
            Err(self.make_warn(ParseWarningKind::NotSupportedMode))
        }
    }

    // Table of Contents
    pub fn push_table_of_contents_entry(
        &mut self,
        heading: HeadingLevel,
        name_elements: &[Element],
    ) {
        // Headings are 1-indexed (e.g. H1), but depth lists are 0-indexed
        let level = usize::from(heading.value()) - 1;

        // Render name as text, so it lacks formatting
        let name =
            TextRender.render_partial(name_elements, self.page_info, self.page_callbacks.clone(), self.settings);

        self.state_mut().table_of_contents.borrow_mut().push((level, name));
    }

    #[cold]
    pub fn remove_table_of_contents(&mut self) -> Vec<(usize, String)> {
        mem::take(&mut self.state_mut().table_of_contents.borrow_mut())
    }

    // WikiScript scopes and variables management

    pub fn push_scope(&mut self) {
        let scopes = &mut self.state_mut().scopes;
        let current_scope = scopes.last().unwrap();

        scopes.push(current_scope.clone());
    }
    
    pub fn pop_scope(&mut self) {
        let state = self.state_mut();
        let last_scope = state.scopes.pop().unwrap();
        let current_depth = self.scope_depth();
        let current_scope = self.current_scope_mut();
        
        for (name, (value, depth)) in last_scope.iter() {
            let last_depth = depth.to_owned();
            if last_depth <= current_depth {
                current_scope.insert(name.to_owned(), (value.to_owned(), last_depth));
            }
        }
    }

    pub fn push_variable(&mut self, name: Cow<'t, str>, value: Cow<'t, str>, override_: bool) {
        let scope_depth = self.scope_depth();
        let current_scope = self.current_scope_mut();

        let new_depth = match override_ {
            false => if current_scope.contains_key(&name) { current_scope.get(&name).unwrap().1 } else { scope_depth },
            true => scope_depth
        };

        current_scope.insert(name, (value, new_depth));
    }

    pub fn replace_variables(&self, content: &mut String) {
        let variables = self.current_scope();
        let mut matches = Vec::new();
    
        for capture in VARIABLE_REGEX.captures_iter(content) {
            let mtch = capture.get(0).unwrap();
            let name = &capture["name"];
    
            if let Some(value) = variables.get(name) {
                matches.push((&value.0, mtch.range()));
            }
        }
    
        matches.reverse();
        for (value, range) in matches {
            content.replace_range(range, value);
        }
    }

    pub fn replace_variables_alloc(&self, content_: &str) -> Cow<str> {
        let variables = self.current_scope();
        let mut matches = Vec::new();

        let mut content = content_.to_owned();
    
        for capture in VARIABLE_REGEX.captures_iter(&mut content) {
            let mtch = capture.get(0).unwrap();
            let name = &capture["name"];
    
            if let Some(value) = variables.get(name) {
                matches.push((&value.0, mtch.range()));
            }
        }
    
        matches.reverse();
        for (value, range) in matches {
            content.replace_range(range, value);
        }

        Cow::from(content)
    }
    
    // Footnotes
    pub fn push_footnote(&mut self, contents: Vec<Element<'t>>) {
        self.state_mut().footnotes.borrow_mut().push(contents);
    }

    #[cold]
    pub fn remove_footnotes(&mut self) -> Vec<Vec<Element<'t>>> {
        mem::take(&mut self.state_mut().footnotes.borrow_mut())
    }

    // Code
    pub fn push_code(&mut self, code_type: String, code: String) {
        self.state_mut().code.borrow_mut().push((code_type, code));
    }

    #[cold]
    pub fn remove_code(&mut self) -> Vec<(String, String)> {
        mem::take(&mut self.state_mut().code.borrow_mut())
    }

    // HTML
    pub fn push_html(&mut self, html: String) {
        self.state_mut().html.borrow_mut().push(html);
    }

    #[cold]
    pub fn remove_html(&mut self) -> Vec<String> {
        mem::take(&mut self.state_mut().html.borrow_mut())
    }

    // Internal links
    pub fn push_internal_link(&mut self, page_ref: PageRef<'t>) {
        self.state_mut().internal_links.borrow_mut().push(page_ref);
    }

    #[cold]
    pub fn remove_internal_links(&mut self) -> Vec<PageRef<'t>> {
        mem::take(&mut self.state_mut().internal_links.borrow_mut())
    }

    // Special for [[include]], appending a SyntaxTree
    pub fn append_toc_and_footnotes(
        &mut self,
        table_of_contents: &mut Vec<(usize, String)>,
        footnotes: &mut Vec<Vec<Element<'t>>>,
    ) {
        self.state_mut().table_of_contents.borrow_mut().append(table_of_contents);

        self.state_mut().footnotes.borrow_mut().append(footnotes);
    }

    // State evaluation
    pub fn evaluate(&self, condition: ParseCondition, match_token_count: &mut Option<&mut usize>) -> bool {
        info!(
            "Evaluating parser condition (token {}, slice '{}', span {}..{})",
            self.current.token.name(),
            self.current.slice,
            self.current.span.start,
            self.current.span.end,
        );

        // you can tell I coded in JavaScript before
        let (matched, token_count) = (|| { 
            match condition {
                ParseCondition::CurrentToken(token) => {
                    (self.current.token == token, 1)
                }
                ParseCondition::TokenPair(current, next) => {
                    if self.current().token != current {
                        debug!(
                            "Current token in pair doesn't match, failing (expected '{}', actual '{}')",
                            current.name(),
                            self.current().token.name(),
                        );
                        return (false, 0);
                    }

                    match self.look_ahead(0) {
                        Some(actual) => {
                            if actual.token != next {
                                debug!(
                                    "Second token in pair doesn't match, failing (expected {}, actual {})",
                                    next.name(),
                                    actual.token.name(),
                                );
                                return (false, 0);
                            }
                        }
                        None => {
                            debug!(
                                "Second token in pair doesn't exist (token {})",
                                next.name(),
                            );
                            return (false, 0);
                        }
                    }

                    (true, 1)
                }
            }
        })();

        if matched {
            match match_token_count {
                Some(count) => **count = token_count,
                _ => {}
            }
        }

        matched
    }

    #[inline]
    pub fn evaluate_any(&self, conditions: &[ParseCondition], matched_token_count: &mut Option<&mut usize>) -> bool {
        info!(
            "Evaluating to see if any parser condition is true (conditions length {})",
            conditions.len(),
        );

        conditions.iter().any(|&condition| self.evaluate(condition, matched_token_count))
    }

    #[inline]
    pub fn evaluate_fn<F>(&self, f: F) -> bool
    where
        F: FnOnce(&mut Parser<'r, 't>) -> Result<bool, ParseWarning>,
    {
        info!("Evaluating closure for parser condition");
        f(&mut self.clone()).unwrap_or(false)
    }

    pub fn save_evaluate_fn<F>(&mut self, f: F) -> Option<&'r ExtractedToken<'t>>
    where
        F: FnOnce(&mut Parser<'r, 't>) -> Result<bool, ParseWarning>,
    {
        info!("Evaluating closure for parser condition, saving progress on success");

        let mut parser = self.clone();
        if f(&mut parser).unwrap_or(false) {
            let last = self.current;
            self.update(&parser);
            Some(last)
        } else {
            self.update_flags(&parser);
            None
        }
    }

    // Token pointer state and manipulation
    #[inline]
    pub fn current(&self) -> &'r ExtractedToken<'t> {
        self.current
    }

    #[inline]
    pub fn remaining(&self) -> &'r [ExtractedToken<'t>] {
        self.remaining
    }

    #[inline]
    pub fn cached_node(&self, offset: usize) -> Option<(usize, ParseSuccess<'r, 't, Elements<'t>>)> {
        match self.ast_cache.borrow().get(&offset) {
            Some((consumed_tokens, success)) => Some((*consumed_tokens, success.to_owned())),
            None => None
        }
    }

    #[inline]
    pub fn put_cached_node(&mut self, offset: usize, consumed_tokens: usize, node: ParseSuccess<'r, 't, Elements<'t>>) {
        self.ast_cache.borrow_mut().insert(offset, (consumed_tokens, node));
    }

    #[inline]
    pub fn update_flags(&mut self, parser: &Parser<'r, 't>) {
        // Flags
        let other_state = parser.state();
        let state = self.state_mut();

        state.has_footnote_block |= other_state.has_footnote_block;
        state.has_toc_block |= other_state.has_toc_block;
    }

    #[inline]
    pub fn update(&mut self, parser: &Parser<'r, 't>) {
        // Global flags
        self.update_flags(parser);

        // Flags that depend on current state
        let other_state = parser.state();
        let state = self.state_mut();

        *state = other_state.clone();
        
        self.start_of_line = parser.start_of_line;

        // Token pointers
        self.current = parser.current;
        self.remaining = parser.remaining;
    }

    #[inline]
    pub fn same_pointer(&self, old_remaining: &'r [ExtractedToken<'t>]) -> bool {
        ptr::eq(self.remaining, old_remaining)
    }

    /// Move the token pointer forward one step.
    #[inline]
    pub fn step(&mut self) -> Result<&'r ExtractedToken<'t>, ParseWarning> {
        debug!("Stepping to the next token");

        // Set the start-of-line flag.
        self.start_of_line = matches!(
            self.current.token,
            Token::InputStart | Token::LineBreak | Token::ParagraphBreak,
        );

        // Step to the next token.
        match self.remaining.split_first() {
            Some((current, remaining)) => {
                self.current = current;
                self.remaining = remaining;
                Ok(current)
            }
            None => {
                warn!("Exhausted all tokens, yielding end of input warning");
                Err(self.make_warn(ParseWarningKind::EndOfInput))
            }
        }
    }

    /// Move the token pointer forward `count` steps.
    #[inline]
    pub fn step_n(&mut self, count: usize) -> Result<(), ParseWarning> {
        trace!("Stepping {count} times");

        for _ in 0..count {
            self.step()?;
        }

        Ok(())
    }

    /// Look for the token `offset + 1` beyond the current one.
    ///
    /// For instance, submitting `0` will yield the first item of `parser.remaining()`.
    #[inline]
    pub fn look_ahead(&self, offset: usize) -> Option<&'r ExtractedToken<'t>> {
        debug!("Looking ahead to a token (offset {offset})");
        self.remaining.get(offset)
    }

    /// Like `look_ahead`, except returns a warning if the token isn't found.
    #[inline]
    pub fn look_ahead_warn(
        &self,
        offset: usize,
    ) -> Result<&'r ExtractedToken<'t>, ParseWarning> {
        self.look_ahead(offset)
            .ok_or_else(|| self.make_warn(ParseWarningKind::EndOfInput))
    }

    /// Retrieves the current and next tokens.
    pub fn next_two_tokens(&self) -> (Token, Option<Token>) {
        let first = self.current.token;
        let second = self.look_ahead(0).map(|next| next.token);

        (first, second)
    }

    /// Retrieves the current, second, and third tokens.
    pub fn next_three_tokens(&self) -> (Token, Option<Token>, Option<Token>) {
        let first = self.current.token;
        let second = self.look_ahead(0).map(|next| next.token);
        let third = self.look_ahead(1).map(|next| next.token);

        (first, second, third)
    }

    // Helpers to get individual tokens
    pub fn get_token(
        &mut self,
        token: Token,
        kind: ParseWarningKind,
    ) -> Result<&'t str, ParseWarning> {
        debug!(
            "Looking for token {} (warning {})",
            token.name(),
            kind.name(),
        );

        let current = self.current();
        if current.token == token {
            let text = current.slice;
            self.step()?;
            Ok(text)
        } else {
            Err(self.make_warn(kind))
        }
    }

    pub fn get_optional_token(&mut self, token: Token) -> Result<(), ParseWarning> {
        debug!("Looking for optional token {}", token.name());

        if self.current().token == token {
            self.step()?;
        }

        Ok(())
    }

    pub fn get_optional_line_break(&mut self) -> Result<(), ParseWarning> {
        info!("Looking for optional line break");
        self.get_optional_token(Token::LineBreak)
    }

    #[inline]
    pub fn get_optional_space(&mut self) -> Result<(), ParseWarning> {
        info!("Looking for optional space");
        self.get_optional_token(Token::Whitespace)
    }

    pub fn get_optional_spaces_any(&mut self) -> Result<(), ParseWarning> {
        info!("Looking for optional spaces (any)");

        let tokens = &[
            Token::Whitespace,
            Token::LineBreak,
            Token::ParagraphBreak,
            Token::Equals,
        ];

        loop {
            let current_token = self.current().token;
            if !tokens.contains(&current_token) {
                return Ok(());
            }

            self.step()?;
        }
    }

    // Utilities
    #[cold]
    #[inline]
    pub fn make_warn(&self, kind: ParseWarningKind) -> ParseWarning {
        ParseWarning::new(kind, self.rule, self.current)
    }
}

#[inline]
fn make_shared_vec<T>() -> Rc<RefCell<Vec<T>>> {
    Rc::new(RefCell::new(Vec::new()))
}